#!/usr/bin/env python3
"""
GC Log Parser - Extract structured metrics from Java GC logs.

Supports:
  - JDK 8 legacy format (-XX:+PrintGCDetails) including G1GC
  - JDK 9+ unified logging (-Xlog:gc*)
  - G1GC, ZGC, Shenandoah, Parallel, Serial collectors

Usage:
  python3 gc_log_parser.py <gc.log> --summary > summary.json
  python3 gc_log_parser.py <gc.log> --window-start TIME --window-end TIME > window.log
  python3 gc_log_parser.py <gc.log> --anomalies > anomalies.json
"""

import argparse
import gzip
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
import statistics
from pathlib import Path

from model import GCPhase
from filter import LineFilter
from trend import HeapTrendAnalyzer


def detect_format(line):
    """Detect GC log format from a single line."""
    if "[gc," in line or "[gc]" in line or "[gc " in line:
        if "GC(" in line:
            return "jdk9_unified"
    # JDK 8 format with date timestamp - must contain GC marker
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", line):
        if "[GC" in line or "[Full GC" in line or "[GC pause" in line:
            return "jdk8_legacy"
        # Also detect from safepoint lines that follow GC events
        if "Total time for which application threads were stopped" in line:
            return "jdk8_legacy"
    if re.match(r"^\[\d+\.\d+s\]\s*\[GC", line):
        return "jdk8_legacy"
    return None


def detect_format_enhanced(filepath: str) -> str:
    """GCViewer-style format detection: multi-chunk + multi-feature matching + GZIP."""
    path = Path(filepath)
    if not path.exists():
        return "unknown"

    # Detect GZIP via magic bytes
    is_gz = False
    with open(path, "rb") as f:
        magic = f.read(2)
        is_gz = magic == b"\x1f\x8b"

    opener = gzip.open if is_gz else open
    with opener(path, "rt", encoding="utf-8", errors="ignore") as f:
        # Read up to 100 chunks of 4KB (like GCViewer)
        for _ in range(100):
            chunk = f.read(4096)
            if not chunk:
                break

            # Multi-feature matching (priority order)
            if "][gc" in chunk or "][safepoint" in chunk:
                return "jdk9_unified"
            if " (young)" in chunk or " (mixed)" in chunk or "G1Ergonomics" in chunk:
                return "jdk8_legacy"
            if "[Times:" in chunk or "[Pause Init Mark" in chunk:
                return "jdk8_legacy"
            if "[GC" in chunk or "[Full GC" in chunk:
                return "jdk8_legacy"
    return "unknown"


def detect_collector(line, current_format):
    """Detect which GC collector produced the log."""
    line_lower = line.lower()
    if "zgc" in line_lower or "pause mark" in line_lower:
        return "ZGC"
    if "shenandoah" in line_lower or "concurrent marking" in line_lower:
        return "Shenandoah"
    if "g1" in line_lower or "evacuation pause" in line_lower:
        return "G1GC"
    if "metadata gc threshold" in line_lower:
        return "G1GC"
    if "psyounggen" in line_lower or "paroldgen" in line_lower:
        return "Parallel"
    if "defnew" in line_lower or "tenured" in line_lower:
        return "Serial"
    if "cms" in line_lower:
        return "CMS"
    return None


# Regex patterns for JDK 9+ unified logging
# G1GC/Shenandoah style: [gc] GC(42) Pause Young (Normal) ... 12.345ms
JDK9_PAUSE_PATTERN = re.compile(
    r"\[.*?\]\s*GC\((\d+)\)\s+Pause\s+(\w+(?:\s+\([^)]*\))?)\s+.*?(\d+(?:\.\d+)?)\s*ms"
)
# ZGC style: GC(0) Y: Pause Mark Start (Major) 0.099ms
ZGC_PAUSE_PATTERN = re.compile(
    r"GC\((\d+)\)\s+([YOy]):\s+Pause\s+([\w\s]+?)\s*(?:\([^)]*\))?\s+([\d.]+)\s*ms"
)
# ZGC collection summary: GC(11) Major Collection (Proactive) 7486M(91%)->714M(9%) 0.755s
ZGC_COLLECTION_PATTERN = re.compile(
    r"GC\((\d+)\)\s+(Major|Minor)\s+Collection\s*(?:\([^)]*\))?\s+([\d.]+[KMGT]?)\([^)]*\)->([\d.]+[KMGT]?)\([^)]*\)\s+([\d.]+)s"
)
# ZGC concurrent phases: GC(0) Y: Concurrent Mark 16.269ms
ZGC_CONCURRENT_PATTERN = re.compile(
    r"GC\((\d+)\)\s+([YOy]):\s+Concurrent\s+([\w\s]+?)\s+([\d.]+)\s*ms"
)
# ZGC allocation stall: [gc,alloc] GC(42) Y: Allocation Stalls: ... (with counts per phase)
ZGC_ALLOC_STALL_PATTERN = re.compile(
    r"GC\((\d+)\)\s+([YOy]):\s+Allocation\s+Stalls:"
)
# ZGC critical stall from stats: Critical: Allocation Stall 0.000 / X.XXX ms
ZGC_STALL_STATS_PATTERN = re.compile(
    r"Critical:\s+Allocation\s+Stall\s+([\d.]+)\s+/\s+([\d.]+)\s+ms"
)

# JDK 9+ G1GC [gc,phases] detail phases
# Matches: GC(42) Pre Evacuate Collection Set: 0.2ms
#          GC(42)   Object Copy: 6.5ms
JDK9_G1_PHASE_PATTERN = re.compile(
    r"GC\((\d+)\)\s+([A-Za-z][A-Za-z\s]*?)\s*:\s+([\d.]+)\s*ms"
)
# Extract GC cause from JDK 9+ unified logging lines like:
# [gc] GC(42) Pause Young (Normal) (G1 Evacuation Pause) 12.345ms
JDK9_CAUSE_PATTERN = re.compile(
    r"Pause\s+\w+(?:\s+\([^)]*\))?\s+\(([^)]+)\)"
)

JDK9_TIME_PATTERN = re.compile(
    r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(?:[+-]\d{2}:?\d{2})?)\]"
)
JDK9_UPTIME_PATTERN = re.compile(
    r"\[(\d+\.\d+)s\]"
)

# Regex patterns for JDK 8 legacy logging
JDK8_TIME_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(?:[+-]\d{2}:?\d{2})?):"
)
# Match G1GC pause start lines (supports optional uptime field and extra qualifiers like initial-mark)
JDK8_G1_PAUSE_START = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[^:]*:\s+(?:\d+\.\d+:\s+)?\[GC pause \((.+?)\)\s+\(?(\w+)(?:\s+\([^)]+\))?\)?"
)
# Match [Times: user=X sys=Y, real=Z secs]
JDK8_TIMES_PATTERN = re.compile(
    r"\[Times:\s+user=[\d.]+\s+sys=[\d.]+,\s+real=([\d.]+)\s+secs\]"
)
# Match simple trailing pause: , 0.1234567 secs]
JDK8_SIMPLE_PAUSE = re.compile(
    r",\s+([\d.]+)\s+secs\]\s*$"
)
# Match Full GC
JDK8_FULL_GC_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[^:]*:\s+\[Full GC"
)
# Match Eden/Survivors/Heap line
JDK8_HEAP_LINE = re.compile(
    r"\[Eden:\s+([\d.]+)([KMGTB]?)\([^)]+\)->([\d.]+)([KMGTB]?)\([^)]+\)\s+"
    r"Survivors:\s+([\d.]+)([KMGTB]?)\s*->\s*([\d.]+)([KMGTB]?)\s+"
    r"Heap:\s+([\d.]+)([KMGTB]?)\(([^)]+)\)->([\d.]+)([KMGTB]?)\(([^)]+)\)\]"
)
# Match Metaspace line
JDK8_METASPACE_LINE = re.compile(
    r"Metaspace\s+used\s+([\d]+)K,\s+capacity\s+([\d]+)K,\s+committed\s+([\d]+)K"
)

# G1GC detailed metrics (JDK 8 legacy)
JDK8_GC_WORKERS = re.compile(r"\[Parallel Time:\s+[\d.]+ ms, GC Workers:\s+(\d+)\]")
JDK8_OBJECT_COPY = re.compile(
    r"\[Object Copy \(ms\): Min:\s+([\d.]+), Avg:\s+([\d.]+), Max:\s+([\d.]+), Diff:\s+([\d.]+), Sum:\s+([\d.]+)\]"
)
JDK8_WORKER_START = re.compile(
    r"\[GC Worker Start \(ms\): Min:\s+([\d.]+), Avg:\s+([\d.]+), Max:\s+([\d.]+), Diff:\s+([\d.]+)\]"
)
JDK8_TIMES_DETAILED = re.compile(
    r"\[Times:\s+user=([\d.]+)\s+sys=([\d.]+),\s+real=([\d.]+)\s+secs\]"
)
JDK8_SURVIVOR_THRESHOLD = re.compile(
    r"Desired survivor size\s+(\d+)\s+bytes, new threshold\s+(\d+)\s+\(max\s+(\d+)\)"
)
JDK8_SAFEPOINT_LINE = re.compile(
    r"Total time for which application threads were stopped:\s+([\d.]+)\s+seconds,\s+Stopping threads took:\s+([\d.]+)\s+seconds"
)


def parse_size(size_str, unit=""):
    """Convert size string with unit to bytes."""
    if not size_str:
        return 0
    try:
        val = float(size_str)
    except (ValueError, TypeError):
        return 0
    multipliers = {"": 1, "B": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    return int(val * multipliers.get(unit, 1))


def parse_jdk9_timestamp(line):
    """Extract timestamp from JDK 9+ unified log line."""
    m = JDK9_TIME_PATTERN.search(line)
    if m:
        ts_str = m.group(1)
        if re.search(r"[+-]\d{4}$", ts_str):
            ts_str = ts_str[:-2] + ":" + ts_str[-2:]
        try:
            return datetime.fromisoformat(ts_str)
        except ValueError:
            pass
    m = JDK9_UPTIME_PATTERN.search(line)
    if m:
        return float(m.group(1))
    return None


def parse_jdk8_timestamp(line):
    """Extract timestamp from JDK 8 legacy log line."""
    m = JDK8_TIME_PATTERN.match(line)
    if m:
        ts_str = m.group(1)
        if re.search(r"[+-]\d{4}$", ts_str):
            ts_str = ts_str[:-2] + ":" + ts_str[-2:]
        try:
            return datetime.fromisoformat(ts_str)
        except ValueError:
            pass
    return None


class Jdk8G1EventParser:
    """State machine parser for multi-line G1 GC events in JDK 8 legacy logs."""

    # Phase patterns for G1 detail lines
    PHASE_PATTERNS = {
        'parallel_time': re.compile(r'\[Parallel Time:\s+([\d.]+)\s*ms'),
        'gc_workers': re.compile(r'GC Workers:\s+(\d+)'),
        'ext_root_scanning': re.compile(r'\[Ext Root Scanning \(ms\):\s+Min:\s+([\d.]+)'),
        'update_rs': re.compile(r'\[Update RS \(ms\):\s+Min:\s+([\d.]+)'),
        'scan_rs': re.compile(r'\[Scan RS \(ms\):\s+Min:\s+([\d.]+)'),
        'code_root_scanning': re.compile(r'\[Code Root Scanning \(ms\):\s+Min:\s+([\d.]+)'),
        'object_copy': re.compile(r'\[Object Copy \(ms\):\s+Min:\s+([\d.]+)'),
        'termination': re.compile(r'\[Termination \(ms\):\s+Min:\s+([\d.]+)'),
        'code_root_fixup': re.compile(r'\[Code Root Fixup:\s+([\d.]+)\s*ms'),
        'code_root_purge': re.compile(r'\[Code Root Purge:\s+([\d.]+)\s*ms'),
        'clear_ct': re.compile(r'\[Clear CT:\s+([\d.]+)\s*ms'),
        'choose_cset': re.compile(r'\[Choose CSet:\s+([\d.]+)\s*ms'),
        'ref_proc': re.compile(r'\[Ref Proc:\s+([\d.]+)\s*ms'),
        'ref_enq': re.compile(r'\[Ref Enq:\s+([\d.]+)\s*ms'),
        'redirty_cards': re.compile(r'\[Redirty Cards:\s+([\d.]+)\s*ms'),
        'free_cset': re.compile(r'\[Free CSet:\s+([\d.]+)\s*ms'),
        'humongous_register': re.compile(r'\[Humongous Register:\s+([\d.]+)\s*ms'),
        'humongous_reclaim': re.compile(r'\[Humongous Reclaim:\s+([\d.]+)\s*ms'),
    }

    # Event start/end patterns
    GC_START_PATTERN = re.compile(r'\[GC pause \((.+?)\)\s+\(?(\w+)')
    FULL_GC_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[^:]*:\s+\[Full GC')
    TIMES_PATTERN = re.compile(r'\[Times:\s+user=[\d.]+\s+sys=[\d.]+,\s+real=([\d.]+)\s+secs\]')
    SIMPLE_PAUSE_PATTERN = re.compile(r',\s+([\d.]+)\s+secs\]\s*$')

    def __init__(self):
        self.pending = None
        self.start_line = 0
        self.raw_lines = []
        self.phases = []
        self.gc_workers = None
        self.object_copy = None
        self.worker_start = None
        self.times_detailed = None

    def feed_line(self, line: str, line_num: int, ts) -> dict:
        """Process a line and return a complete GC event dict, or None."""
        # Check for GC event start
        m = self.GC_START_PATTERN.search(line)
        if m:
            # Finalize any existing pending event without proper end
            result = self._finalize_if_pending(ts)
            self.pending = {
                'trigger': m.group(1),
                'gen': m.group(2),
                'line': line_num,
                'timestamp': str(ts) if ts else None,
                'is_full_gc': False,
            }
            self.start_line = line_num
            self.raw_lines = [line]
            self.phases = []
            self.gc_workers = None
            self.object_copy = None
            self.worker_start = None
            self.times_detailed = None
            return result

        # Check for Full GC start
        m = self.FULL_GC_PATTERN.match(line)
        if m:
            result = self._finalize_if_pending(ts)
            self.pending = {
                'trigger': 'Full GC',
                'gen': 'full',
                'line': line_num,
                'timestamp': str(ts) if ts else None,
                'is_full_gc': True,
            }
            self.start_line = line_num
            self.raw_lines = [line]
            self.phases = []
            return result

        if not self.pending:
            return None

        self.raw_lines.append(line)

        # Check for event end markers
        m = self.TIMES_PATTERN.search(line)
        if m:
            self.pending['pause_sec'] = float(m.group(1))
            return self._finalize(ts)

        # Simple trailing pause (for non-G1 styles that might match)
        m = self.SIMPLE_PAUSE_PATTERN.search(line)
        if m and not self.pending.get('pause_sec') and ('[GC' in line or '[Full GC' in line):
            self.pending['pause_sec'] = float(m.group(1))
            return self._finalize(ts)

        # Extract detail phases
        self._extract_phases(line)

        return None

    def _extract_phases(self, line: str):
        for phase_name, pattern in self.PHASE_PATTERNS.items():
            m = pattern.search(line)
            if m:
                val = float(m.group(1))
                if phase_name == 'gc_workers':
                    self.gc_workers = int(val)
                elif phase_name == 'object_copy':
                    # Try to extract all stats if available
                    full_match = re.search(
                        r'\[Object Copy \(ms\): Min:\s+([\d.]+), Avg:\s+([\d.]+), Max:\s+([\d.]+), Diff:\s+([\d.]+), Sum:\s+([\d.]+)\]',
                        line
                    )
                    if full_match:
                        self.object_copy = {
                            'min': float(full_match.group(1)),
                            'avg': float(full_match.group(2)),
                            'max': float(full_match.group(3)),
                            'diff': float(full_match.group(4)),
                            'sum': float(full_match.group(5)),
                        }
                elif phase_name == 'ext_root_scanning':
                    # Try full format with all stats
                    full_match = re.search(
                        r'\[Ext Root Scanning \(ms\): Min:\s+([\d.]+), Avg:\s+([\d.]+), Max:\s+([\d.]+), Diff:\s+([\d.]+), Sum:\s+([\d.]+)\]',
                        line
                    )
                    if full_match:
                        self.phases.append(GCPhase('ext_root_scanning', float(full_match.group(2))))
                    else:
                        self.phases.append(GCPhase('ext_root_scanning', val))
                elif phase_name == 'update_rs':
                    full_match = re.search(
                        r'\[Update RS \(ms\): Min:\s+([\d.]+), Avg:\s+([\d.]+), Max:\s+([\d.]+), Diff:\s+([\d.]+), Sum:\s+([\d.]+)\]',
                        line
                    )
                    if full_match:
                        self.phases.append(GCPhase('update_rs', float(full_match.group(2))))
                    else:
                        self.phases.append(GCPhase('update_rs', val))
                elif phase_name == 'worker_start':
                    full_match = re.search(
                        r'\[GC Worker Start \(ms\): Min:\s+([\d.]+), Avg:\s+([\d.]+), Max:\s+([\d.]+), Diff:\s+([\d.]+)\]',
                        line
                    )
                    if full_match:
                        self.worker_start = {
                            'min': float(full_match.group(1)),
                            'avg': float(full_match.group(2)),
                            'max': float(full_match.group(3)),
                            'diff': float(full_match.group(4)),
                        }
                else:
                    self.phases.append(GCPhase(phase_name, val))

        # Also extract detailed [Times] info if present
        m = JDK8_TIMES_DETAILED.search(line)
        if m:
            self.times_detailed = {
                "user": float(m.group(1)), "sys": float(m.group(2)),
                "real": float(m.group(3)),
            }

    def _finalize_if_pending(self, ts) -> dict:
        if self.pending:
            # Event was interrupted by a new start; use what we have
            return self._finalize(ts)
        return None

    def _finalize(self, ts) -> dict:
        event = self.pending
        self.pending = None
        result = {
            'event': event,
            'start_line': self.start_line,
            'phases': self.phases,
            'gc_workers': self.gc_workers,
            'object_copy': self.object_copy,
            'worker_start': self.worker_start,
            'times_detailed': self.times_detailed,
        }
        self.phases = []
        self.gc_workers = None
        self.object_copy = None
        self.worker_start = None
        self.times_detailed = None
        return result


class GCLogAnalyzer:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.format = None
        self.collector = None
        self.gc_events = []
        self.pause_times = []
        self.full_gc_count = 0
        self.anomalies = []
        self.first_timestamp = None
        self.last_timestamp = None
        self.total_pause_ms = 0
        self.line_count = 0
        # ZGC-specific tracking
        self.zgc_cycle_times = []  # Total GC cycle times (not STW)
        self.mmu_stats = {}  # MMU data: {window_ms: percentage}
        # JDK8 state tracking
        self._jdk8_pending_gc = None
        self._jdk8_gc_start_line = 0
        # Detailed metrics tracking (G1GC)
        self._jdk8_gc_workers = None
        self._jdk8_object_copy = None
        self._jdk8_worker_start = None
        self._jdk8_times_detailed = None
        self._jdk8_survivor_threshold = None
        # Safepoint tracking
        self.safepoint_events = []
        self._last_gc_real_time_sec = None
        # NEW: G1 multi-line state machine
        self._g1_parser = Jdk8G1EventParser()
        # NEW: Concurrent cycle tracking
        self.concurrent_cycles = []
        self._pending_concurrent = None
        # NEW: Heap trend analysis
        self.heap_trend = HeapTrendAnalyzer()
        # NEW: G1 detail phase stats
        self.g1_detail_phases = defaultdict(list)
        # NEW: Max heap for OOM estimation
        self._max_heap_mb = None
        # NEW: JDK 9+ G1 detail phases by gc_id
        self._jdk9_phases_by_gc_id = defaultdict(list)

    def analyze(self):
        """Main analysis routine - single pass over the file."""
        # Use enhanced format detection first
        if self.format is None:
            self.format = detect_format_enhanced(str(self.filepath))

        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                self.line_count = line_num
                line = line.rstrip("\n\r")
                if not line.strip():
                    continue

                # Apply line filter to skip noise from verbose JVM flags
                if LineFilter.should_skip(line):
                    continue

                if self.format is None or self.format == "unknown":
                    fmt = detect_format(line)
                    if fmt:
                        self.format = fmt

                if self.collector is None:
                    detected = detect_collector(line, self.format)
                    if detected:
                        self.collector = detected

                self._process_line(line, line_num)

        # Handle any pending GC at EOF
        if self._jdk8_pending_gc:
            self._finalize_jdk8_gc(self._jdk8_pending_gc, self._jdk8_gc_start_line, None)
        if self._g1_parser.pending:
            result = self._g1_parser._finalize(None)
            if result:
                self._apply_g1_event(result)
        if self._pending_concurrent:
            # Unfinished concurrent cycle at EOF — discard
            self._pending_concurrent = None

        # Associate JDK 9+ G1 detail phases with their gc_events
        if self._jdk9_phases_by_gc_id:
            for event in self.gc_events:
                gc_id = event.get('gc_id')
                if gc_id is not None and gc_id in self._jdk9_phases_by_gc_id:
                    phases = self._jdk9_phases_by_gc_id[gc_id]
                    event['phases'] = [
                        {'name': p['name'], 'duration_ms': round(p['duration_ms'], 3)}
                        for p in phases
                    ]

        return self._build_summary()

    def _process_line(self, line, line_num):
        """Process a single log line."""
        if self.format == "jdk9_unified":
            self._process_jdk9_line(line, line_num)
        elif self.format == "jdk8_legacy":
            self._process_jdk8_line(line, line_num)

    def _process_jdk9_line(self, line, line_num):
        ts = parse_jdk9_timestamp(line)
        if ts and self.first_timestamp is None:
            self.first_timestamp = ts
        if ts:
            self.last_timestamp = ts

        # --- G1GC / Shenandoah style pauses ---
        m = JDK9_PAUSE_PATTERN.search(line)
        if m:
            gc_id = int(m.group(1))
            pause_type = m.group(2)
            pause_ms = float(m.group(3))
            self.pause_times.append(pause_ms)
            self.total_pause_ms += pause_ms

            is_full = "Full" in pause_type or "Full" in line
            if is_full:
                self.full_gc_count += 1

            # Extract GC cause for G1/Shenandoah (e.g., "G1 Evacuation Pause")
            gc_cause = None
            if self.collector in (None, "G1GC", "Shenandoah"):
                cm = JDK9_CAUSE_PATTERN.search(line)
                if cm:
                    gc_cause = cm.group(1)
                else:
                    gc_cause = pause_type

            event = {
                "line": line_num,
                "gc_id": gc_id,
                "type": pause_type,
                "pause_ms": pause_ms,
                "is_full_gc": is_full,
                "raw": line[:200],
            }
            if gc_cause:
                event["gc_cause"] = gc_cause
            if ts:
                event["timestamp"] = str(ts) if isinstance(ts, datetime) else ts

            self.gc_events.append(event)

            if is_full:
                self.anomalies.append({
                    "line": line_num,
                    "type": "full_gc",
                    "pause_ms": pause_ms,
                    "description": f"Full GC detected: {pause_ms:.1f}ms",
                })

        # --- ZGC STW pauses (Generational ZGC: Y/O phases) ---
        m = ZGC_PAUSE_PATTERN.search(line)
        if m:
            gc_id = int(m.group(1))
            gen = m.group(2)
            pause_type = m.group(3).strip()
            pause_ms = float(m.group(4))
            self.pause_times.append(pause_ms)
            self.total_pause_ms += pause_ms

            event = {
                "line": line_num,
                "gc_id": gc_id,
                "type": f"ZGC {gen}: {pause_type}",
                "pause_ms": pause_ms,
                "is_full_gc": False,
                "raw": line[:200],
                "gc_cause": f"ZGC {gen}",
            }
            if ts:
                event["timestamp"] = str(ts) if isinstance(ts, datetime) else ts

            self.gc_events.append(event)

        # --- ZGC collection summary (total cycle time + heap change) ---
        m = ZGC_COLLECTION_PATTERN.search(line)
        if m:
            gc_id = int(m.group(1))
            coll_type = m.group(2)
            heap_before = m.group(3)
            heap_after = m.group(4)
            cycle_sec = float(m.group(5))
            cycle_ms = cycle_sec * 1000
            self.zgc_cycle_times.append(cycle_ms)

            heap_before_mb = self._parse_size_mb(heap_before)
            heap_after_mb = self._parse_size_mb(heap_after)
            event = {
                "line": line_num,
                "gc_id": gc_id,
                "type": f"ZGC {coll_type} Collection (total)",
                "pause_ms": round(cycle_ms, 2),
                "is_full_gc": False,
                "raw": line[:200],
                "heap_before": heap_before,
                "heap_after": heap_after,
                "gc_cause": f"ZGC {coll_type}",
            }
            if heap_before_mb is not None:
                event["heap_before_mb"] = round(heap_before_mb, 1)
            if heap_after_mb is not None:
                event["heap_after_mb"] = round(heap_after_mb, 1)
            if ts:
                event["timestamp"] = str(ts) if isinstance(ts, datetime) else ts

            self.gc_events.append(event)

            # Feed to heap trend analyzer
            heap_after_mb = self._parse_size_mb(heap_after)
            if heap_after_mb is not None and ts:
                ts_sec = self._timestamp_to_seconds(ts)
                if ts_sec is not None:
                    self.heap_trend.add_point(ts_sec, heap_after_mb, is_full_gc=False)

        # --- ZGC concurrent phases ---
        m = ZGC_CONCURRENT_PATTERN.search(line)
        if m:
            gc_id = int(m.group(1))
            gen = m.group(2)
            phase_name = m.group(3).strip()
            duration_ms = float(m.group(4))
            ts_sec = self._timestamp_to_seconds(ts)
            if ts_sec is not None:
                self.concurrent_cycles.append({
                    'cycle_id': len(self.concurrent_cycles),
                    'algorithm': 'ZGC',
                    'start_timestamp': ts_sec - duration_ms / 1000,
                    'end_timestamp': ts_sec,
                    'phases': [{'name': f'concurrent_{phase_name.lower()}', 'duration_ms': duration_ms}],
                })

        # --- ZGC MMU extraction ---
        if "MMU:" in line and self.collector == "ZGC":
            for mmu_m in re.finditer(r'(\d+)ms/(\d+(?:\.\d+)?)%', line):
                self.mmu_stats[int(mmu_m.group(1))] = float(mmu_m.group(2))

        # --- ZGC allocation stall stats (from gc,stats summary) ---
        m = ZGC_STALL_STATS_PATTERN.search(line)
        if m:
            avg_stall = float(m.group(1))
            max_stall = float(m.group(2))
            if max_stall > 0:
                self.anomalies.append({
                    "line": line_num,
                    "type": "allocation_stall",
                    "pause_ms": max_stall,
                    "description": f"ZGC allocation stall detected (avg={avg_stall:.3f}ms, max={max_stall:.3f}ms)",
                })

        # --- JDK 9+ G1GC detail phases from [gc,phases] ---
        if self.collector in (None, 'G1GC'):
            m = JDK9_G1_PHASE_PATTERN.search(line)
            if m:
                gc_id = int(m.group(1))
                phase_name = m.group(2).strip()
                duration_ms = float(m.group(3))
                self._jdk9_phases_by_gc_id[gc_id].append({
                    'name': phase_name,
                    'duration_ms': duration_ms,
                })
                self.g1_detail_phases[phase_name].append(duration_ms)

        # Match to-space exhausted (G1)
        if "To-space exhausted" in line:
            self.anomalies.append({
                "line": line_num,
                "type": "to_space_exhausted",
                "description": "To-space exhausted (evacuation failure)",
            })

        # Match humongous allocations (G1)
        if "Humongous" in line and "object size" in line:
            self.anomalies.append({
                "line": line_num,
                "type": "humongous_allocation",
                "description": "Humongous object allocation",
            })

        # Match Shenandoah degenerated GC
        if "Degenerated GC" in line:
            self.anomalies.append({
                "line": line_num,
                "type": "degenerated_gc",
                "description": "Shenandoah degenerated GC",
            })

    def _process_jdk8_line(self, line, line_num):
        ts = parse_jdk8_timestamp(line)
        if ts and self.first_timestamp is None:
            self.first_timestamp = ts
        if ts:
            self.last_timestamp = ts

        # --- Concurrent cycle tracking (G1) ---
        if 'concurrent-mark-start' in line:
            self._pending_concurrent = {
                'cycle_id': len(self.concurrent_cycles),
                'algorithm': 'G1',
                'start_timestamp': self._timestamp_to_seconds(ts),
                'reset_for_overflow': False,
            }
        elif 'concurrent-mark-end' in line and self._pending_concurrent:
            self._pending_concurrent['end_timestamp'] = self._timestamp_to_seconds(ts)
            self.concurrent_cycles.append(self._pending_concurrent)
            self._pending_concurrent = None
        elif 'concurrent-mark-reset-for-overflow' in line:
            if self._pending_concurrent:
                self._pending_concurrent['reset_for_overflow'] = True
                self.anomalies.append({
                    'line': line_num,
                    'type': 'concurrent_mark_overflow',
                    'description': 'G1 concurrent mark reset for overflow',
                })

        # --- G1 state machine (when collector is unknown or G1) ---
        if self.collector in (None, 'G1GC'):
            result = self._g1_parser.feed_line(line, line_num, ts)
            if result:
                self.collector = 'G1GC'
                self._apply_g1_event(result, ts)
                return
            if self._g1_parser.pending:
                self.collector = 'G1GC'
                return

        # --- Non-G1 fallback: existing logic for Parallel/Serial/Unknown ---
        # Check for safepoint lines
        m = JDK8_SAFEPOINT_LINE.search(line)
        if m:
            self._process_safepoint(ts, float(m.group(1)), float(m.group(2)), line_num)
            return

        # Check for Full GC start
        m = JDK8_FULL_GC_PATTERN.match(line)
        if m:
            if self._jdk8_pending_gc:
                self._finalize_jdk8_gc(self._jdk8_pending_gc, self._jdk8_gc_start_line, None)
            self._jdk8_pending_gc = {
                "trigger": "Full GC",
                "gen": "full",
                "line": line_num,
                "timestamp": str(ts) if ts else None,
                "is_full_gc": True,
            }
            self._jdk8_gc_start_line = line_num
            return

        # If we have a pending GC, look for its end markers
        if self._jdk8_pending_gc:
            m = JDK8_TIMES_DETAILED.search(line)
            if m:
                self._jdk8_times_detailed = {
                    "user": float(m.group(1)), "sys": float(m.group(2)),
                    "real": float(m.group(3)),
                }

            m = JDK8_TIMES_PATTERN.search(line)
            if m:
                pause_sec = float(m.group(1))
                self._jdk8_pending_gc["pause_sec"] = pause_sec
                self._finalize_jdk8_gc(self._jdk8_pending_gc, self._jdk8_gc_start_line, line_num)
                self._jdk8_pending_gc = None
                return

            m = JDK8_SIMPLE_PAUSE.search(line)
            if m and not self._jdk8_pending_gc.get("pause_sec"):
                if "[GC" in line or "[Full GC" in line:
                    pause_sec = float(m.group(1))
                    self._jdk8_pending_gc["pause_sec"] = pause_sec
                    self._finalize_jdk8_gc(self._jdk8_pending_gc, self._jdk8_gc_start_line, line_num)
                    self._jdk8_pending_gc = None
                    return

            m = JDK8_HEAP_LINE.search(line)
            if m:
                self._jdk8_pending_gc["eden_before_mb"] = self._to_mb(float(m.group(1)), m.group(2))
                self._jdk8_pending_gc["eden_after_mb"] = self._to_mb(float(m.group(3)), m.group(4))
                self._jdk8_pending_gc["survivor_before_mb"] = self._to_mb(float(m.group(5)), m.group(6))
                self._jdk8_pending_gc["survivor_after_mb"] = self._to_mb(float(m.group(7)), m.group(8))
                self._jdk8_pending_gc["heap_before_mb"] = self._to_mb(float(m.group(9)), m.group(10))
                self._jdk8_pending_gc["heap_after_mb"] = self._to_mb(float(m.group(12)), m.group(13))
                return

            m = JDK8_METASPACE_LINE.search(line)
            if m:
                self._jdk8_pending_gc["metaspace_used_kb"] = int(m.group(1))
                return

            m = JDK8_GC_WORKERS.search(line)
            if m:
                self._jdk8_gc_workers = int(m.group(1))
                return

            m = JDK8_OBJECT_COPY.search(line)
            if m:
                self._jdk8_object_copy = {
                    "min": float(m.group(1)), "avg": float(m.group(2)),
                    "max": float(m.group(3)), "diff": float(m.group(4)),
                    "sum": float(m.group(5)),
                }
                return

            m = JDK8_WORKER_START.search(line)
            if m:
                self._jdk8_worker_start = {
                    "min": float(m.group(1)), "avg": float(m.group(2)),
                    "max": float(m.group(3)), "diff": float(m.group(4)),
                }
                return

            m = JDK8_TIMES_DETAILED.search(line)
            if m:
                self._jdk8_times_detailed = {
                    "user": float(m.group(1)), "sys": float(m.group(2)),
                    "real": float(m.group(3)),
                }
                return

            m = JDK8_SURVIVOR_THRESHOLD.search(line)
            if m:
                self._jdk8_survivor_threshold = {
                    "desired_bytes": int(m.group(1)),
                    "new_threshold": int(m.group(2)),
                    "max_threshold": int(m.group(3)),
                }
                return

    def _to_mb(self, val, unit):
        """Convert value + unit to MB."""
        multipliers = {"": 1/1024/1024, "B": 1/1024/1024, "K": 1/1024, "M": 1, "G": 1024, "T": 1024*1024}
        return val * multipliers.get(unit, 1)

    def _parse_size_mb(self, size_str):
        """Parse a size string like '7486M' or '2.5G' into MB."""
        import re
        m = re.match(r'([\d.]+)([KMGT]?)', size_str)
        if m:
            return self._to_mb(float(m.group(1)), m.group(2))
        return None

    def _timestamp_to_seconds(self, ts):
        """Convert a timestamp to seconds since epoch."""
        if isinstance(ts, datetime):
            return ts.timestamp()
        elif isinstance(ts, (int, float)):
            return ts
        elif isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts)
                return dt.timestamp()
            except (ValueError, TypeError):
                pass
        return None

    def _apply_g1_event(self, result, ts):
        """Apply a completed G1 event from the state machine."""
        event_data = result['event']
        start_line = result['start_line']
        raw_lines = self._g1_parser.raw_lines
        phases = result.get('phases', [])

        # Extract heap info from raw lines
        for line in raw_lines:
            m = JDK8_HEAP_LINE.search(line)
            if m:
                event_data['eden_before_mb'] = self._to_mb(float(m.group(1)), m.group(2))
                event_data['eden_after_mb'] = self._to_mb(float(m.group(3)), m.group(4))
                event_data['survivor_before_mb'] = self._to_mb(float(m.group(5)), m.group(6))
                event_data['survivor_after_mb'] = self._to_mb(float(m.group(7)), m.group(8))
                event_data['heap_before_mb'] = self._to_mb(float(m.group(9)), m.group(10))
                event_data['heap_after_mb'] = self._to_mb(float(m.group(12)), m.group(13))
                # Track max heap capacity for OOM estimation (from Heap: X(Y)->Z(W) )
                capacity_mb = self._parse_size_mb(m.group(14))
                if capacity_mb and capacity_mb > (self._max_heap_mb or 0):
                    self._max_heap_mb = capacity_mb
                break

            m = JDK8_METASPACE_LINE.search(line)
            if m:
                event_data['metaspace_used_kb'] = int(m.group(1))

        # Set detailed metrics for finalizer
        if result.get('gc_workers'):
            self._jdk8_gc_workers = result['gc_workers']
        if result.get('object_copy'):
            self._jdk8_object_copy = result['object_copy']
        if result.get('worker_start'):
            self._jdk8_worker_start = result['worker_start']
        if result.get('times_detailed'):
            self._jdk8_times_detailed = result['times_detailed']

        # Collect G1 detail phases for summary
        if phases:
            event_data['phases'] = [{'name': p.name, 'duration_ms': round(p.duration_ms, 3)} for p in phases]
            for phase in phases:
                self.g1_detail_phases[phase.name].append(phase.duration_ms)

        # Feed to heap trend analyzer (use event start timestamp, not end line ts)
        if event_data.get('heap_after_mb') and event_data.get('timestamp'):
            ts_sec = self._timestamp_to_seconds(event_data['timestamp'])
            if ts_sec is not None:
                self.heap_trend.add_point(
                    ts_sec,
                    event_data['heap_after_mb'],
                    is_full_gc=event_data.get('is_full_gc', False),
                )

        # Call existing finalizer
        self._finalize_jdk8_gc(event_data, start_line, None)

    def _finalize_jdk8_gc(self, gc_info, start_line, end_line):
        """Finalize a JDK8 GC event and add to statistics."""
        pause_sec = gc_info.get("pause_sec", 0)
        pause_ms = pause_sec * 1000

        if pause_ms > 0:
            self.pause_times.append(pause_ms)
            self.total_pause_ms += pause_ms

        is_full = gc_info.get("is_full_gc", False)
        if is_full:
            self.full_gc_count += 1

        trigger = gc_info.get("trigger", "Unknown")
        gen = gc_info.get("gen", "unknown")

        # Build type description
        if is_full:
            pause_type = "Full GC"
        elif trigger == "Metadata GC Threshold":
            pause_type = f"Young GC (Metadata GC Threshold)"
        elif trigger == "G1 Evacuation Pause":
            pause_type = f"Young GC (G1 Evacuation)"
        else:
            pause_type = f"{gen} GC ({trigger})"

        event = {
            "line": start_line,
            "type": pause_type,
            "pause_ms": round(pause_ms, 2),
            "is_full_gc": is_full,
            "raw": f"{trigger} at line {start_line}",
            "gc_cause": trigger,
        }
        if gc_info.get("timestamp"):
            event["timestamp"] = gc_info["timestamp"]
        if gc_info.get("heap_before_mb") is not None:
            event["heap_before_mb"] = round(gc_info["heap_before_mb"], 1)
            event["heap_after_mb"] = round(gc_info["heap_after_mb"], 1)
        if gc_info.get("eden_before_mb") is not None:
            event["eden_before_mb"] = round(gc_info["eden_before_mb"], 1)
            event["eden_after_mb"] = round(gc_info["eden_after_mb"], 1)
        if gc_info.get("survivor_before_mb") is not None:
            event["survivor_before_mb"] = round(gc_info["survivor_before_mb"], 1)
            event["survivor_after_mb"] = round(gc_info["survivor_after_mb"], 1)
        if gc_info.get("metaspace_used_kb"):
            event["metaspace_used_kb"] = gc_info["metaspace_used_kb"]

        self.gc_events.append(event)

        if is_full:
            self.anomalies.append({
                "line": start_line,
                "type": "full_gc",
                "pause_ms": pause_ms,
                "description": f"Full GC detected: {pause_ms:.1f}ms",
            })

        # Calculate CPU utilization from detailed [Times] output
        cpu_utilization = None
        if self._jdk8_times_detailed and self._jdk8_gc_workers:
            user_sys = self._jdk8_times_detailed["user"] + self._jdk8_times_detailed["sys"]
            real = self._jdk8_times_detailed["real"]
            workers = self._jdk8_gc_workers
            if real > 0 and workers > 0:
                cpu_utilization = round((user_sys / (workers * real)) * 100, 1)

        # Save real time for next safepoint correlation
        self._last_gc_real_time_sec = pause_sec

        # Feed to heap trend analyzer (non-G1 path)
        if gc_info.get("heap_after_mb") and gc_info.get("timestamp"):
            ts_sec = self._timestamp_to_seconds(gc_info["timestamp"])
            if ts_sec is not None:
                self.heap_trend.add_point(
                    ts_sec,
                    gc_info["heap_after_mb"],
                    is_full_gc=is_full,
                )

        # Add detailed metrics to event
        if cpu_utilization is not None:
            event["cpu_utilization_percent"] = cpu_utilization
        if self._jdk8_gc_workers:
            event["gc_workers"] = self._jdk8_gc_workers
        if self._jdk8_object_copy:
            event["object_copy_ms"] = self._jdk8_object_copy
        if self._jdk8_worker_start:
            event["worker_start_ms"] = self._jdk8_worker_start
        if self._jdk8_times_detailed:
            event["times"] = self._jdk8_times_detailed
        if self._jdk8_survivor_threshold:
            event["survivor_threshold"] = self._jdk8_survivor_threshold

        # Reset detailed tracking for next GC
        self._jdk8_gc_workers = None
        self._jdk8_object_copy = None
        self._jdk8_worker_start = None
        self._jdk8_times_detailed = None
        self._jdk8_survivor_threshold = None

    def _process_safepoint(self, timestamp, total_stopped_sec, stopping_sec, line_num):
        """Process a safepoint line and detect non-GC safepoint pauses."""
        gc_pause_sec = 0
        # Heuristic: correlate with last GC only if times are reasonably close
        if self._last_gc_real_time_sec:
            tolerance = max(0.05, self._last_gc_real_time_sec * 0.2)
            if abs(total_stopped_sec - self._last_gc_real_time_sec) <= tolerance:
                gc_pause_sec = self._last_gc_real_time_sec

        non_gc_pause_sec = total_stopped_sec - gc_pause_sec

        event = {
            "line": line_num,
            "timestamp": str(timestamp) if timestamp else None,
            "total_stopped_sec": round(total_stopped_sec, 4),
            "stopping_sec": round(stopping_sec, 4),
            "gc_pause_sec": round(gc_pause_sec, 4),
            "non_gc_pause_sec": round(max(0, non_gc_pause_sec), 4),
        }
        self.safepoint_events.append(event)

        self._last_gc_real_time_sec = None

    def _build_summary(self):
        """Build the analysis summary, with collector-specific metrics."""
        summary = {
            "file": str(self.filepath),
            "line_count": self.line_count,
            "detected_format": self.format or "unknown",
            "detected_collector": self.collector or "unknown",
        }

        if self.pause_times:
            sorted_pauses = sorted(self.pause_times)
            n = len(sorted_pauses)
            p50 = sorted_pauses[n // 2]
            p95_idx = int(n * 0.95) if n >= 20 else n - 1
            p95 = sorted_pauses[p95_idx]
            # Only report p99 when sample size >= 100; otherwise use p95 with note
            p99 = sorted_pauses[int(n * 0.99)] if n >= 100 else None
            # p99.5 requires >= 200 samples, p99.9 requires >= 500
            p995 = sorted_pauses[int(n * 0.995)] if n >= 200 else None
            p999 = sorted_pauses[int(n * 0.999)] if n >= 500 else None

            runtime_estimate_ms, runtime_is_estimated = self._estimate_runtime_ms()
            throughput = 100.0
            if runtime_estimate_ms > 0:
                throughput = max(0, 100.0 - (self.total_pause_ms / runtime_estimate_ms * 100))

            summary["runtime_is_estimated"] = runtime_is_estimated
            summary["estimated_runtime_ms"] = round(runtime_estimate_ms, 2)

            # Collector-specific metrics
            if self.collector == "ZGC":
                summary["metrics"] = self._build_zgc_metrics(
                    sorted_pauses, n, p50, p95, p99, p995, p999, throughput, runtime_estimate_ms
                )
            else:
                summary["metrics"] = self._build_standard_metrics(
                    sorted_pauses, n, p50, p95, p99, p995, p999, throughput, runtime_estimate_ms
                )
        else:
            summary["metrics"] = {"total_gc_events": 0}

        # Count anomaly types
        anomaly_types = defaultdict(int)
        for a in self.anomalies:
            anomaly_types[a["type"]] += 1
        summary["anomaly_counts"] = dict(anomaly_types)
        summary["anomalies"] = self.anomalies[:100]
        summary["anomaly_count"] = len(self.anomalies)

        # Startup vs steady-state analysis
        startup_analysis = self._build_startup_analysis()
        if startup_analysis:
            summary["startup_analysis"] = startup_analysis

        # Recent events sample
        summary["recent_events_sample"] = self.gc_events[-10:] if len(self.gc_events) >= 10 else self.gc_events

        # NEW: Concurrent cycles summary
        if self.concurrent_cycles:
            durations = []
            for c in self.concurrent_cycles:
                start = c.get('start_timestamp')
                end = c.get('end_timestamp')
                if start is not None and end is not None:
                    durations.append((end - start) * 1000)
            reset_count = sum(1 for c in self.concurrent_cycles if c.get('reset_for_overflow'))
            summary["concurrent_cycles"] = {
                "count": len(self.concurrent_cycles),
                "algorithm": self.concurrent_cycles[0].get('algorithm', 'unknown'),
                "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else None,
                "max_duration_ms": round(max(durations), 2) if durations else None,
                "reset_for_overflow_count": reset_count,
            }

        # NEW: Heap trend analysis
        heap_trend_result = self.heap_trend.regression_analysis(max_heap_mb=self._max_heap_mb)
        if heap_trend_result.get('samples', 0) > 0:
            summary["heap_trend"] = heap_trend_result

        # NEW: G1 detail phase stats (JDK 8)
        if self.g1_detail_phases:
            summary["g1_detail_phases"] = {
                name: round(sum(values) / len(values), 3)
                for name, values in self.g1_detail_phases.items()
                if values
            }

        # NEW: G1 detail phase stats (JDK 9+)
        if not summary.get("g1_detail_phases") and self._jdk9_phases_by_gc_id:
            jdk9_phase_stats = defaultdict(list)
            for event in self.gc_events:
                for phase in event.get('phases', []):
                    jdk9_phase_stats[phase['name']].append(phase['duration_ms'])
            if jdk9_phase_stats:
                summary["g1_detail_phases"] = {
                    name: round(sum(values) / len(values), 3)
                    for name, values in jdk9_phase_stats.items()
                }

        # P0-1: Pause-by-type statistics
        pause_by_type = self._build_pause_by_type()
        if pause_by_type:
            summary["pause_by_type"] = pause_by_type

        # P0-2: VM operations overhead
        vm_ops = self._build_vm_operations()
        if vm_ops:
            summary["vm_operations"] = vm_ops

        # P1-1: Memory efficiency
        mem_eff = self._build_memory_efficiency()
        if mem_eff:
            summary["memory_efficiency"] = mem_eff

        # P1-2: Promotion
        promo = self._build_promotion()
        if promo:
            summary["promotion"] = promo

        # P1-3: Pause intervals
        intervals = self._build_pause_intervals()
        if intervals:
            summary["pause_intervals_ms"] = intervals

        # P0: GC efficiency
        gc_eff = self._build_gc_efficiency()
        if gc_eff:
            summary["gc_efficiency"] = gc_eff

        # P0: GC causes
        gc_causes = self._build_gc_causes()
        if gc_causes:
            summary["gc_causes"] = gc_causes

        # P1: Full GC summary
        full_gc_summary = self._build_full_gc_summary()
        if full_gc_summary:
            summary["full_gc_summary"] = full_gc_summary

        # P2: Heap trigger stats
        heap_trigger = self._build_heap_trigger_stats()
        if heap_trigger:
            summary["heap_trigger_stats"] = heap_trigger

        # Level 3: Coordinate data for Phase 2 deep dive
        top_pauses = self._build_top_pauses(n=20)
        if top_pauses:
            summary["top_pauses"] = top_pauses

        full_gc_events = self._build_full_gc_events()
        if full_gc_events:
            summary["full_gc_events"] = full_gc_events

        top_by_type = self._build_top_by_type(n=10)
        if top_by_type:
            summary["top_by_type"] = top_by_type

        top_by_cause = self._build_top_by_cause(n=10)
        if top_by_cause:
            summary["top_by_cause"] = top_by_cause

        gc_cadence = self._build_gc_cadence(window_seconds=60)
        if gc_cadence:
            summary["gc_cadence"] = gc_cadence

        heap_samples = self._build_heap_samples(max_points=20)
        if heap_samples:
            summary["heap_samples"] = heap_samples

        safepoint_events = self._build_safepoint_events(n=20)
        if safepoint_events:
            summary["safepoint_events"] = safepoint_events

        promotion_spikes = self._build_promotion_spikes(n=10)
        if promotion_spikes:
            summary["promotion_spikes"] = promotion_spikes

        return summary

    def _build_zgc_metrics(self, sorted_pauses, n, p50, p95, p99, p995, p999, throughput, runtime_estimate_ms):
        """Build metrics specific to ZGC."""
        metrics = {
            "stw_pause_count": n,
            "stw_max_ms": round(max(self.pause_times), 3),
            "stw_min_ms": round(min(self.pause_times), 3),
            "stw_avg_ms": round(sum(self.pause_times) / n, 3),
            "stw_p50_ms": round(p50, 3),
            "stw_p95_ms": round(p95, 3),
            "allocation_stall_count": sum(1 for a in self.anomalies if a["type"] == "allocation_stall"),
            "allocation_stall_ms": round(sum(a.get("pause_ms", 0) for a in self.anomalies
                                             if a["type"] == "allocation_stall"), 3),
        }
        if p99 is not None:
            metrics["stw_p99_ms"] = round(p99, 3)
        else:
            metrics["stw_p99_note"] = "Sample size < 100; use p95 instead"
        if p995 is not None:
            metrics["stw_p995_ms"] = round(p995, 3)
        else:
            metrics["stw_p995_note"] = "Sample size < 200; use p99 instead"
        if p999 is not None:
            metrics["stw_p999_ms"] = round(p999, 3)
        else:
            metrics["stw_p999_note"] = "Sample size < 500; use p995 instead"

        # MMU stats
        if self.mmu_stats:
            metrics["mmu"] = self.mmu_stats

        # ZGC cycle times (total, including concurrent phases)
        if self.zgc_cycle_times:
            sorted_cycles = sorted(self.zgc_cycle_times)
            cycle_n = len(sorted_cycles)
            metrics["cycle_count"] = cycle_n
            metrics["cycle_max_ms"] = round(max(self.zgc_cycle_times), 2)
            metrics["cycle_min_ms"] = round(min(self.zgc_cycle_times), 2)
            metrics["cycle_avg_ms"] = round(sum(self.zgc_cycle_times) / cycle_n, 2)
            metrics["cycle_p95_ms"] = round(sorted_cycles[int(cycle_n * 0.95)] if cycle_n >= 20 else sorted_cycles[-1], 2)
            if cycle_n >= 100:
                metrics["cycle_p99_ms"] = round(sorted_cycles[int(cycle_n * 0.99)], 2)
            if cycle_n >= 200:
                metrics["cycle_p995_ms"] = round(sorted_cycles[int(cycle_n * 0.995)], 2)
            if cycle_n >= 500:
                metrics["cycle_p999_ms"] = round(sorted_cycles[int(cycle_n * 0.999)], 2)

        if runtime_estimate_ms > 0:
            freq_per_min = len(self.zgc_cycle_times) / (runtime_estimate_ms / 1000 / 60) if self.zgc_cycle_times else 0
            metrics["gc_frequency_per_minute"] = round(freq_per_min, 2)

        return metrics

    def _build_standard_metrics(self, sorted_pauses, n, p50, p95, p99, p995, p999, throughput, runtime_estimate_ms):
        """Build standard metrics for G1GC, Parallel, Serial, Shenandoah."""
        metrics = {
            "total_gc_events": n,
            "total_pause_ms": round(self.total_pause_ms, 2),
            "max_pause_ms": round(max(self.pause_times), 2),
            "min_pause_ms": round(min(self.pause_times), 2),
            "avg_pause_ms": round(sum(self.pause_times) / n, 2),
            "p50_pause_ms": round(p50, 2),
            "p95_pause_ms": round(p95, 2),
            "full_gc_count": self.full_gc_count,
            "throughput_percent": round(throughput, 2),
        }
        if p99 is not None:
            metrics["p99_pause_ms"] = round(p99, 2)
        else:
            metrics["p99_note"] = "Sample size < 100; use p95 instead"
        if p995 is not None:
            metrics["p995_pause_ms"] = round(p995, 2)
        else:
            metrics["p995_note"] = "Sample size < 200; use p99 instead"
        if p999 is not None:
            metrics["p999_pause_ms"] = round(p999, 2)
        else:
            metrics["p999_note"] = "Sample size < 500; use p995 instead"

        if runtime_estimate_ms > 0:
            freq_per_min = n / (runtime_estimate_ms / 1000 / 60)
            metrics["gc_frequency_per_minute"] = round(freq_per_min, 2)

        return metrics

    def _estimate_runtime_ms(self):
        """Estimate total runtime from timestamps or uptime values.

        Returns:
            (runtime_ms, is_estimated): runtime_ms is the estimated total
            runtime in milliseconds; is_estimated is True when the value is
            a heuristic fallback rather than derived from actual timestamps.
        """
        if isinstance(self.first_timestamp, datetime) and isinstance(self.last_timestamp, datetime):
            return (self.last_timestamp - self.first_timestamp).total_seconds() * 1000, False
        elif isinstance(self.first_timestamp, (int, float)) and isinstance(self.last_timestamp, (int, float)):
            return (self.last_timestamp - self.first_timestamp) * 1000, False
        estimated = max(self.total_pause_ms * 20, 60000)
        return estimated, True

    def _build_startup_analysis(self):
        """Analyze startup period vs steady state for G1GC JDK8 logs."""
        if not self.gc_events:
            return None

        # Determine startup period: first 5 minutes or first 30 GC events
        startup_end_time = None
        if isinstance(self.first_timestamp, datetime):
            startup_end_time = self.first_timestamp + timedelta(minutes=5)

        startup_events = []
        steady_events = []

        for ev in self.gc_events:
            ts = ev.get("timestamp")
            if ts and startup_end_time:
                try:
                    ev_dt = datetime.fromisoformat(ts)
                    if ev_dt <= startup_end_time:
                        startup_events.append(ev)
                    else:
                        steady_events.append(ev)
                except (ValueError, TypeError):
                    steady_events.append(ev)
            else:
                # Fallback: first 30 events as startup
                if len(startup_events) < 30:
                    startup_events.append(ev)
                else:
                    steady_events.append(ev)

        if not startup_events or not steady_events:
            return None

        def _avg_cpu(events):
            vals = [e.get("cpu_utilization_percent") for e in events if e.get("cpu_utilization_percent") is not None]
            return round(sum(vals) / len(vals), 1) if vals else None

        def _avg_worker_start_diff(events):
            vals = [e.get("worker_start_ms", {}).get("diff") for e in events if e.get("worker_start_ms")]
            return round(sum(vals) / len(vals), 2) if vals else None

        def _avg_object_copy(events):
            vals = [e.get("object_copy_ms", {}).get("avg") for e in events if e.get("object_copy_ms")]
            return round(sum(vals) / len(vals), 2) if vals else None

        def _eden_std(events):
            vals = [e.get("eden_before_mb") for e in events if e.get("eden_before_mb")]
            return round(statistics.stdev(vals), 2) if len(vals) > 1 else None

        startup_cpu = _avg_cpu(startup_events)
        steady_cpu = _avg_cpu(steady_events)
        startup_worker_diff = _avg_worker_start_diff(startup_events)
        steady_worker_diff = _avg_worker_start_diff(steady_events)
        startup_obj_copy = _avg_object_copy(startup_events)
        steady_obj_copy = _avg_object_copy(steady_events)
        startup_eden_std = _eden_std(startup_events)
        steady_eden_std = _eden_std(steady_events)

        analysis = {
            "startup_event_count": len(startup_events),
            "steady_event_count": len(steady_events),
            "log_duration_minutes": round((self.last_timestamp - self.first_timestamp).total_seconds() / 60, 2) if isinstance(self.first_timestamp, datetime) and isinstance(self.last_timestamp, datetime) else None,
        }

        if startup_cpu is not None and steady_cpu is not None:
            analysis["cpu_utilization"] = {
                "startup_avg": startup_cpu,
                "steady_avg": steady_cpu,
                "diff": round(startup_cpu - steady_cpu, 1),
            }

        if startup_worker_diff is not None and steady_worker_diff is not None:
            analysis["worker_start_diff_ms"] = {
                "startup_avg": startup_worker_diff,
                "steady_avg": steady_worker_diff,
                "diff": round(startup_worker_diff - steady_worker_diff, 2),
            }

        if startup_obj_copy is not None and steady_obj_copy is not None:
            analysis["object_copy_ms"] = {
                "startup_avg": startup_obj_copy,
                "steady_avg": steady_obj_copy,
            }

        if startup_eden_std is not None and steady_eden_std is not None:
            analysis["eden_before_std_mb"] = {
                "startup": startup_eden_std,
                "steady": steady_eden_std,
                "diff": round(startup_eden_std - steady_eden_std, 2),
            }

        # Annotate anomalies with time-since-startup
        for a in self.anomalies:
            a_line = a["line"]
            nearest = None
            for ev in self.gc_events:
                if abs(ev["line"] - a_line) < 50:
                    nearest = ev
                    break
            if nearest and nearest.get("timestamp"):
                try:
                    ev_dt = datetime.fromisoformat(nearest["timestamp"])
                    if isinstance(self.first_timestamp, datetime):
                        seconds_since_start = (ev_dt - self.first_timestamp).total_seconds()
                        a["seconds_since_startup"] = round(seconds_since_start, 2)
                        a["in_startup_period"] = seconds_since_start <= 300
                except (ValueError, TypeError):
                    pass

        # Non-GC safepoint summary
        if self.safepoint_events:
            non_gc_pauses = [s["non_gc_pause_sec"] * 1000 for s in self.safepoint_events if s.get("non_gc_pause_sec", 0) > 0]
            analysis["safepoint_summary"] = {
                "total_safepoints": len(self.safepoint_events),
                "non_gc_count": len(non_gc_pauses),
                "max_non_gc_pause_ms": round(max(non_gc_pauses), 2) if non_gc_pauses else 0,
            }

        return analysis

    def _build_pause_by_type(self):
        """Group GC events by type and compute per-type pause statistics."""
        from collections import defaultdict
        groups = defaultdict(list)
        for e in self.gc_events:
            pause = e.get("pause_ms", 0)
            if pause <= 0:
                continue
            type_name = e.get("type", "Unknown")
            # Exclude ZGC collection total events (cycle duration, not STW pause)
            if type_name.startswith("ZGC") and "Collection (total)" in type_name:
                continue
            groups[type_name].append(pause)
        if not groups:
            return None
        result = {}
        for type_name, pauses in sorted(groups.items(), key=lambda x: -sum(x[1])):
            n = len(pauses)
            sorted_p = sorted(pauses)
            entry = {
                "count": n,
                "min_ms": round(min(pauses), 2),
                "max_ms": round(max(pauses), 2),
                "avg_ms": round(sum(pauses) / n, 2),
                "median_ms": round(sorted_p[n // 2], 2),
                "p95_ms": round(sorted_p[int(n * 0.95)] if n >= 20 else sorted_p[-1], 2),
                "sum_ms": round(sum(pauses), 2),
                "sum_percent": round(sum(pauses) / self.total_pause_ms * 100, 1) if self.total_pause_ms > 0 else 0,
            }
            if n >= 200:
                entry["p995_ms"] = round(sorted_p[int(n * 0.995)], 2)
            if n >= 500:
                entry["p999_ms"] = round(sorted_p[int(n * 0.999)], 2)
            result[type_name] = entry
        return result

    def _build_vm_operations(self):
        """Aggregate non-GC safepoint pauses from safepoint events."""
        vm_events = [s for s in self.safepoint_events if s.get("non_gc_pause_sec", 0) > 0]
        if not vm_events:
            return None
        pauses_ms = [s["non_gc_pause_sec"] * 1000 for s in vm_events]
        n = len(pauses_ms)
        sorted_p = sorted(pauses_ms)
        return {
            "count": n,
            "total_ms": round(sum(pauses_ms), 2),
            "avg_ms": round(sum(pauses_ms) / n, 2),
            "min_ms": round(min(pauses_ms), 2),
            "max_ms": round(max(pauses_ms), 2),
            "median_ms": round(sorted_p[n // 2], 2),
            "p95_ms": round(sorted_p[int(n * 0.95)] if n >= 20 else sorted_p[-1], 2),
        }

    def _build_memory_efficiency(self):
        """Compute total and average memory freed per GC event."""
        gc_freed = []
        full_gc_freed = []
        for e in self.gc_events:
            before = e.get("heap_before_mb")
            after = e.get("heap_after_mb")
            if before is not None and after is not None:
                freed = before - after
                if freed > 0:
                    gc_freed.append(freed)
                    if e.get("is_full_gc"):
                        full_gc_freed.append(freed)
        if not gc_freed:
            return None
        result = {
            "total_freed_mb": round(sum(gc_freed), 1),
            "avg_freed_per_gc_mb": round(sum(gc_freed) / len(gc_freed), 1),
        }
        if full_gc_freed:
            result["total_freed_by_full_gc_mb"] = round(sum(full_gc_freed), 1)
            result["avg_freed_per_full_gc_mb"] = round(sum(full_gc_freed) / len(full_gc_freed), 1)
        return result

    def _build_promotion(self):
        """Approximate object promotion to tenured from heap/eden/survivor deltas."""
        promotions = []
        for e in self.gc_events:
            if not all(k in e for k in (
                "heap_before_mb", "heap_after_mb",
                "eden_before_mb", "eden_after_mb",
                "survivor_before_mb", "survivor_after_mb"
            )):
                continue
            tenured_before = (
                e["heap_before_mb"] - e["eden_before_mb"] - e["survivor_before_mb"]
            )
            tenured_after = (
                e["heap_after_mb"] - e["eden_after_mb"] - e["survivor_after_mb"]
            )
            promoted = tenured_after - tenured_before
            if promoted > 0:
                promotions.append(promoted)
        if not promotions:
            return None
        return {
            "total_promoted_mb": round(sum(promotions), 1),
            "avg_promoted_per_gc_mb": round(sum(promotions) / len(promotions), 1),
            "max_promoted_mb": round(max(promotions), 1),
        }

    def _build_pause_intervals(self):
        """Compute statistics for intervals between consecutive STW events."""
        stw_events = []
        for e in self.gc_events:
            pause = e.get("pause_ms", 0)
            if pause > 0 and "timestamp" in e:
                # Skip ZGC collection total events (full cycle, not individual STW)
                if e.get("type", "").startswith("ZGC") and "Collection (total)" in e.get("type", ""):
                    continue
                ts = self._timestamp_to_seconds(e["timestamp"])
                if ts is not None:
                    stw_events.append((ts, e))
        if len(stw_events) < 2:
            return None
        stw_events.sort(key=lambda x: x[0])
        intervals = []
        for i in range(1, len(stw_events)):
            interval_ms = (stw_events[i][0] - stw_events[i - 1][0]) * 1000
            if interval_ms > 0:
                intervals.append(interval_ms)
        if not intervals:
            return None
        n = len(intervals)
        sorted_i = sorted(intervals)
        return {
            "avg": round(sum(intervals) / n, 2),
            "min": round(min(intervals), 2),
            "max": round(max(intervals), 2),
            "median": round(sorted_i[n // 2], 2),
            "p95": round(sorted_i[int(n * 0.95)] if n >= 20 else sorted_i[-1], 2),
        }

    def _build_gc_efficiency(self):
        """Compute GC efficiency metrics: freed memory per minute and per ms pause."""
        total_freed = 0.0
        full_gc_freed = 0.0
        full_gc_pause_ms = 0.0

        for e in self.gc_events:
            before = e.get("heap_before_mb")
            after = e.get("heap_after_mb")
            if before is not None and after is not None:
                freed = before - after
                if freed > 0:
                    total_freed += freed
                    if e.get("is_full_gc"):
                        full_gc_freed += freed

        for e in self.gc_events:
            if e.get("is_full_gc") and e.get("pause_ms", 0) > 0:
                full_gc_pause_ms += e["pause_ms"]

        if total_freed <= 0 or self.total_pause_ms <= 0:
            return None

        runtime_estimate_ms, _ = self._estimate_runtime_ms()
        if runtime_estimate_ms <= 0:
            return None

        result = {
            "freed_mem_per_minute": round(total_freed / (runtime_estimate_ms / 60000), 2),
            "avg_performance_mbps": round(total_freed / self.total_pause_ms, 3),
        }

        if full_gc_freed > 0 and full_gc_pause_ms > 0:
            result["full_gc_performance_mbps"] = round(full_gc_freed / full_gc_pause_ms, 3)

        regular_freed = total_freed - full_gc_freed
        regular_pause = self.total_pause_ms - full_gc_pause_ms
        if regular_freed > 0 and regular_pause > 0:
            result["regular_gc_performance_mbps"] = round(regular_freed / regular_pause, 3)

        return result

    def _build_gc_causes(self):
        """Group GC events by trigger cause and compute per-cause statistics."""
        groups = defaultdict(list)
        for e in self.gc_events:
            pause = e.get("pause_ms", 0)
            if pause <= 0:
                continue
            type_name = e.get("type", "")
            # Exclude ZGC collection total events
            if type_name.startswith("ZGC") and "Collection (total)" in type_name:
                continue
            cause = e.get("gc_cause")
            if not cause:
                # Derive from type: extract content in parentheses
                if "(" in type_name:
                    cause = type_name.split("(", 1)[1].split(")", 1)[0]
                else:
                    cause = type_name
            if not cause:
                cause = "Unknown"
            groups[cause].append(pause)

        if not groups:
            return None

        result = {}
        for cause, pauses in sorted(groups.items(), key=lambda x: -sum(x[1])):
            n = len(pauses)
            result[cause] = {
                "count": n,
                "total_pause_ms": round(sum(pauses), 2),
                "avg_pause_ms": round(sum(pauses) / n, 2),
                "max_pause_ms": round(max(pauses), 2),
            }
        return result

    def _build_full_gc_summary(self):
        """Aggregate statistics for Full GC events only."""
        full_gc_events = [e for e in self.gc_events if e.get("is_full_gc") and e.get("pause_ms", 0) > 0]
        if not full_gc_events:
            return None

        pauses = [e["pause_ms"] for e in full_gc_events]
        result = {
            "count": len(pauses),
            "total_pause_ms": round(sum(pauses), 2),
            "avg_pause_ms": round(sum(pauses) / len(pauses), 2),
            "max_pause_ms": round(max(pauses), 2),
            "min_pause_ms": round(min(pauses), 2),
        }

        full_gc_freed = []
        for e in full_gc_events:
            before = e.get("heap_before_mb")
            after = e.get("heap_after_mb")
            if before is not None and after is not None:
                freed = before - after
                if freed > 0:
                    full_gc_freed.append(freed)

        if full_gc_freed:
            result["total_freed_mb"] = round(sum(full_gc_freed), 1)
            result["avg_freed_mb"] = round(sum(full_gc_freed) / len(full_gc_freed), 1)

        return result

    def _build_heap_trigger_stats(self):
        """Approximate heap usage ratio at GC trigger time."""
        usage_percents = []
        max_heap = self._max_heap_mb

        # Fallback: estimate max heap from max observed heap value (before or after) * 1.1
        if max_heap is None:
            heap_values = []
            for e in self.gc_events:
                if e.get("heap_before_mb") is not None:
                    heap_values.append(e["heap_before_mb"])
                if e.get("heap_after_mb") is not None:
                    heap_values.append(e["heap_after_mb"])
            if heap_values:
                max_heap = max(heap_values) * 1.1

        if max_heap is None or max_heap <= 0:
            return None

        for e in self.gc_events:
            before = e.get("heap_before_mb")
            if before is not None:
                usage_percents.append(before / max_heap * 100)

        if len(usage_percents) < 5:
            return None

        return {
            "avg_usage_percent": round(sum(usage_percents) / len(usage_percents), 1),
            "max_usage_percent": round(max(usage_percents), 1),
            "min_usage_percent": round(min(usage_percents), 1),
            "high_usage_count": sum(1 for u in usage_percents if u > 80),
            "approximate_max_heap_mb": round(max_heap, 1),
            "note": "Approximate: max heap inferred from GC events. Accurate IOF requires -XX:+PrintAdaptiveSizePolicy.",
        }

    def _event_to_coordinate(self, event):
        """Extract coordinate fields from a gc_event for Level 3 output."""
        result = {
            "line_number": event.get("line"),
            "pause_ms": event.get("pause_ms"),
            "gc_type": event.get("type"),
        }
        ts = event.get("timestamp")
        if ts is not None:
            result["timestamp"] = str(ts) if isinstance(ts, datetime) else ts
        if event.get("gc_cause"):
            result["gc_cause"] = event["gc_cause"]
        if event.get("is_full_gc") is not None:
            result["is_full_gc"] = event["is_full_gc"]
        if event.get("heap_before_mb") is not None:
            result["heap_before_mb"] = event["heap_before_mb"]
        if event.get("heap_after_mb") is not None:
            result["heap_after_mb"] = event["heap_after_mb"]
        return result

    def _build_top_pauses(self, n=20):
        """Top N STW pauses by pause_ms, descending."""
        candidates = []
        for e in self.gc_events:
            pause = e.get("pause_ms", 0)
            if pause <= 0:
                continue
            # Skip ZGC collection total events (full cycle, not individual STW)
            type_name = e.get("type", "")
            if type_name.startswith("ZGC") and "Collection (total)" in type_name:
                continue
            candidates.append(e)
        if not candidates:
            return None
        sorted_events = sorted(candidates, key=lambda e: e.get("pause_ms", 0), reverse=True)
        result = []
        for rank, event in enumerate(sorted_events[:n], start=1):
            coord = self._event_to_coordinate(event)
            coord["rank"] = rank
            result.append(coord)
        return result

    def _build_full_gc_events(self):
        """All Full GC events with coordinates."""
        full_events = [e for e in self.gc_events if e.get("is_full_gc") and e.get("pause_ms", 0) > 0]
        if not full_events:
            return None
        return [self._event_to_coordinate(e) for e in full_events]

    def _build_top_by_type(self, n=10):
        """Top N events per GC type, grouped by type."""
        from collections import defaultdict
        groups = defaultdict(list)
        for e in self.gc_events:
            pause = e.get("pause_ms", 0)
            if pause <= 0:
                continue
            type_name = e.get("type", "Unknown")
            # Skip ZGC collection total events
            if type_name.startswith("ZGC") and "Collection (total)" in type_name:
                continue
            groups[type_name].append(e)
        if not groups:
            return None
        result = {}
        for type_name, events in sorted(groups.items()):
            sorted_events = sorted(events, key=lambda e: e.get("pause_ms", 0), reverse=True)
            result[type_name] = [self._event_to_coordinate(e) for e in sorted_events[:n]]
        return result

    def _build_top_by_cause(self, n=10):
        """Top N events per GC cause, grouped by cause."""
        from collections import defaultdict
        groups = defaultdict(list)
        for e in self.gc_events:
            pause = e.get("pause_ms", 0)
            if pause <= 0:
                continue
            type_name = e.get("type", "")
            if type_name.startswith("ZGC") and "Collection (total)" in type_name:
                continue
            cause = e.get("gc_cause")
            if not cause:
                if "(" in type_name:
                    cause = type_name.split("(", 1)[1].split(")", 1)[0]
                else:
                    cause = type_name or "Unknown"
            groups[cause].append(e)
        if not groups:
            return None
        result = {}
        for cause, events in sorted(groups.items()):
            sorted_events = sorted(events, key=lambda e: e.get("pause_ms", 0), reverse=True)
            result[cause] = [self._event_to_coordinate(e) for e in sorted_events[:n]]
        return result

    def _build_gc_cadence(self, window_seconds=60):
        """GC count and total pause per time window."""
        events_with_ts = []
        for e in self.gc_events:
            pause = e.get("pause_ms", 0)
            if pause <= 0:
                continue
            type_name = e.get("type", "")
            if type_name.startswith("ZGC") and "Collection (total)" in type_name:
                continue
            ts = e.get("timestamp")
            if ts is None:
                continue
            ts_sec = self._timestamp_to_seconds(ts)
            if ts_sec is not None:
                events_with_ts.append((ts_sec, pause))
        if len(events_with_ts) < 2:
            return None
        events_with_ts.sort(key=lambda x: x[0])
        first_ts = events_with_ts[0][0]
        windows = defaultdict(lambda: {"gc_count": 0, "total_pause_ms": 0.0})
        for ts_sec, pause in events_with_ts:
            bucket = int((ts_sec - first_ts) // window_seconds)
            window_start = first_ts + bucket * window_seconds
            windows[window_start]["gc_count"] += 1
            windows[window_start]["total_pause_ms"] += pause
        if not windows:
            return None
        sorted_windows = []
        for start_ts in sorted(windows.keys()):
            w = windows[start_ts]
            # Format start_time: use ISO if first_timestamp is datetime, else uptime seconds
            if isinstance(self.first_timestamp, datetime):
                start_dt = datetime.fromtimestamp(start_ts)
                start_str = start_dt.isoformat()
            else:
                start_str = round(start_ts, 3)
            sorted_windows.append({
                "start_time": start_str,
                "gc_count": w["gc_count"],
                "total_pause_ms": round(w["total_pause_ms"], 2),
            })
        return {
            "window_seconds": window_seconds,
            "windows": sorted_windows,
        }

    def _build_heap_samples(self, max_points=20):
        """Uniformly sampled heap_after_mb points over time."""
        candidates = []
        for idx, e in enumerate(self.gc_events):
            if e.get("heap_after_mb") is None:
                continue
            ts = e.get("timestamp")
            if ts is None:
                continue
            candidates.append({
                "timestamp": str(ts) if isinstance(ts, datetime) else ts,
                "heap_after_mb": e["heap_after_mb"],
                "gc_event_index": idx,
            })
        if not candidates:
            return None
        if len(candidates) <= max_points:
            return candidates
        step = len(candidates) // max_points
        return candidates[::step][:max_points]

    def _build_safepoint_events(self, n=20):
        """Top N non-GC safepoint events by non-GC pause time."""
        candidates = []
        for s in self.safepoint_events:
            non_gc_sec = s.get("non_gc_pause_sec", 0)
            if non_gc_sec <= 0:
                continue
            event = {
                "line_number": s.get("line"),
                "total_stopped_ms": round(s.get("total_stopped_sec", 0) * 1000, 2),
                "stopping_ms": round(s.get("stopping_sec", 0) * 1000, 2),
                "non_gc_pause_ms": round(non_gc_sec * 1000, 2),
            }
            ts = s.get("timestamp")
            if ts is not None:
                event["timestamp"] = ts
            candidates.append((non_gc_sec, event))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [event for _, event in candidates[:n]]

    def _build_promotion_spikes(self, n=10):
        """Top N events by promoted MB to tenured generation."""
        candidates = []
        for e in self.gc_events:
            if not all(k in e for k in (
                "heap_before_mb", "heap_after_mb",
                "eden_before_mb", "eden_after_mb",
                "survivor_before_mb", "survivor_after_mb"
            )):
                continue
            tenured_before = e["heap_before_mb"] - e["eden_before_mb"] - e["survivor_before_mb"]
            tenured_after = e["heap_after_mb"] - e["eden_after_mb"] - e["survivor_after_mb"]
            promoted = tenured_after - tenured_before
            if promoted > 0:
                coord = self._event_to_coordinate(e)
                coord["promoted_mb"] = round(promoted, 2)
                candidates.append((promoted, coord))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        result = []
        for rank, (_, coord) in enumerate(candidates[:n], start=1):
            coord["rank"] = rank
            result.append(coord)
        return result

    def extract_window_by_line(self, start_line, end_line):
        """Extract log lines within a line number range."""
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if start_line <= i <= end_line:
                    print(line.rstrip("\n\r"))
                if i > end_line:
                    break

    def extract_window(self, start_time, end_time):
        """Extract log lines within a time window.

        For JDK 8 legacy logs, GC events span multiple lines but only the
        start line has a timestamp. We track whether we are inside a windowed
        event and include continuation lines so the extracted context stays
        readable.
        """
        start_dt = None
        end_dt = None
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError:
            pass

        if not start_dt or not end_dt:
            print("Error: Invalid time format. Use ISO-8601 like '2024-01-15T10:23:45'", file=sys.stderr)
            sys.exit(1)

        in_window = False
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_stripped = line.rstrip("\n\r")
                if not line_stripped.strip():
                    if in_window:
                        print(line_stripped)
                    continue

                ts = None
                if self.format == "jdk9_unified":
                    ts = parse_jdk9_timestamp(line_stripped)
                elif self.format == "jdk8_legacy":
                    ts = parse_jdk8_timestamp(line_stripped)

                if ts and start_dt and end_dt:
                    if isinstance(ts, datetime):
                        ts_naive = ts.replace(tzinfo=None) if ts.tzinfo else ts
                        if start_dt <= ts_naive <= end_dt:
                            in_window = True
                            print(line_stripped)
                        else:
                            in_window = False
                else:
                    # Continuation line of a GC event (common in JDK8).
                    # Keep it only if it belongs to the current windowed event.
                    if in_window:
                        print(line_stripped)

    def extract_anomaly_context(self, context_lines=5):
        """Extract context around each anomaly."""
        results = []
        for anomaly in self.anomalies:
            line_num = anomaly["line"]
            start = max(1, line_num - context_lines)
            end = min(self.line_count, line_num + context_lines)

            context = []
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if start <= i <= end:
                        context.append(line.rstrip("\n\r"))
                    if i > end:
                        break

            results.append({
                **anomaly,
                "context_lines": context,
                "context_range": f"{start}-{end}",
            })

        return results


def main():
    parser = argparse.ArgumentParser(description="Parse Java GC logs and extract metrics")
    parser.add_argument("logfile", help="Path to GC log file")
    parser.add_argument("--summary", action="store_true", help="Output JSON summary")
    parser.add_argument("--anomalies", action="store_true", help="Output anomalies with context")
    parser.add_argument("--window-start", help="Window start time (ISO-8601)")
    parser.add_argument("--window-end", help="Window end time (ISO-8601)")
    parser.add_argument("--window-start-line", type=int, help="Window start line number")
    parser.add_argument("--window-end-line", type=int, help="Window end line number")
    parser.add_argument("--context-lines", type=int, default=5, help="Context lines around anomalies")

    args = parser.parse_args()

    analyzer = GCLogAnalyzer(args.logfile)

    if args.summary:
        summary = analyzer.analyze()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    elif args.anomalies:
        analyzer.analyze()
        anomalies = analyzer.extract_anomaly_context(args.context_lines)
        print(json.dumps(anomalies, indent=2, ensure_ascii=False))
    elif args.window_start and args.window_end:
        analyzer.analyze()
        analyzer.extract_window(args.window_start, args.window_end)
    elif args.window_start_line and args.window_end_line:
        analyzer.analyze()
        analyzer.extract_window_by_line(args.window_start_line, args.window_end_line)
    else:
        summary = analyzer.analyze()
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
