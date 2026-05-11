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
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


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
    r"Heap:\s+([\d.]+)([KMGTB]?)\([^)]+\)->([\d.]+)([KMGTB]?)\([^)]+\)\]"
)
# Match Metaspace line
JDK8_METASPACE_LINE = re.compile(
    r"Metaspace\s+used\s+([\d]+)K,\s+capacity\s+([\d]+)K,\s+committed\s+([\d]+)K"
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

    def analyze(self):
        """Main analysis routine - single pass over the file."""
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                self.line_count = line_num
                line = line.rstrip("\n\r")
                if not line.strip():
                    continue

                if self.format is None:
                    self.format = detect_format(line)

                if self.collector is None:
                    detected = detect_collector(line, self.format)
                    if detected:
                        self.collector = detected

                self._process_line(line, line_num)

        # Handle any pending GC at EOF
        if self._jdk8_pending_gc:
            self._finalize_jdk8_gc(self._jdk8_pending_gc, self._jdk8_gc_start_line, None)

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

            event = {
                "line": line_num,
                "gc_id": gc_id,
                "type": pause_type,
                "pause_ms": pause_ms,
                "is_full_gc": is_full,
                "raw": line[:200],
            }
            if ts:
                event["timestamp"] = str(ts) if isinstance(ts, datetime) else ts

            self.gc_events.append(event)

            if pause_ms > 200 and self.collector in ("G1GC", "Parallel", "Serial"):
                self.anomalies.append({
                    "line": line_num,
                    "type": "long_pause",
                    "pause_ms": pause_ms,
                    "description": f"Long STW pause: {pause_ms:.1f}ms",
                })
            elif pause_ms > 10 and self.collector in ("ZGC", "Shenandoah"):
                self.anomalies.append({
                    "line": line_num,
                    "type": "long_pause",
                    "pause_ms": pause_ms,
                    "description": f"Long STW pause for {self.collector}: {pause_ms:.1f}ms",
                })

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
            }
            if ts:
                event["timestamp"] = str(ts) if isinstance(ts, datetime) else ts

            self.gc_events.append(event)

            if pause_ms > 10:
                self.anomalies.append({
                    "line": line_num,
                    "type": "long_pause",
                    "pause_ms": pause_ms,
                    "description": f"Long ZGC STW pause ({gen} {pause_type}): {pause_ms:.1f}ms",
                })

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

            event = {
                "line": line_num,
                "gc_id": gc_id,
                "type": f"ZGC {coll_type} Collection (total)",
                "pause_ms": round(cycle_ms, 2),
                "is_full_gc": False,
                "raw": line[:200],
                "heap_before": heap_before,
                "heap_after": heap_after,
            }
            if ts:
                event["timestamp"] = str(ts) if isinstance(ts, datetime) else ts

            self.gc_events.append(event)

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

        # Check for G1GC pause start
        m = JDK8_G1_PAUSE_START.match(line)
        if m:
            # Finalize any pending GC
            if self._jdk8_pending_gc:
                self._finalize_jdk8_gc(self._jdk8_pending_gc, self._jdk8_gc_start_line, None)

            trigger = m.group(1)
            gen = m.group(2)
            self._jdk8_pending_gc = {
                "trigger": trigger,
                "gen": gen,
                "line": line_num,
                "timestamp": str(ts) if ts else None,
                "heap_before_mb": None,
                "heap_after_mb": None,
                "eden_before_mb": None,
                "eden_after_mb": None,
                "survivor_before_mb": None,
                "survivor_after_mb": None,
                "metaspace_used_kb": None,
                "is_full_gc": False,
            }
            self._jdk8_gc_start_line = line_num
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
            # Check for [Times: ... real=X secs]
            m = JDK8_TIMES_PATTERN.search(line)
            if m:
                pause_sec = float(m.group(1))
                self._jdk8_pending_gc["pause_sec"] = pause_sec
                self._finalize_jdk8_gc(self._jdk8_pending_gc, self._jdk8_gc_start_line, line_num)
                self._jdk8_pending_gc = None
                return

            # Check for simple trailing pause (Parallel GC style)
            # Only match on actual GC summary lines, not reference processing lines
            m = JDK8_SIMPLE_PAUSE.search(line)
            if m and not self._jdk8_pending_gc.get("pause_sec"):
                if "[GC" in line or "[Full GC" in line:
                    pause_sec = float(m.group(1))
                    self._jdk8_pending_gc["pause_sec"] = pause_sec
                    self._finalize_jdk8_gc(self._jdk8_pending_gc, self._jdk8_gc_start_line, line_num)
                    self._jdk8_pending_gc = None
                    return

            # Check for Eden/Survivors/Heap line
            m = JDK8_HEAP_LINE.search(line)
            if m:
                self._jdk8_pending_gc["eden_before_mb"] = self._to_mb(float(m.group(1)), m.group(2))
                self._jdk8_pending_gc["eden_after_mb"] = self._to_mb(float(m.group(3)), m.group(4))
                self._jdk8_pending_gc["survivor_before_mb"] = self._to_mb(float(m.group(5)), m.group(6))
                self._jdk8_pending_gc["survivor_after_mb"] = self._to_mb(float(m.group(7)), m.group(8))
                self._jdk8_pending_gc["heap_before_mb"] = self._to_mb(float(m.group(9)), m.group(10))
                self._jdk8_pending_gc["heap_after_mb"] = self._to_mb(float(m.group(11)), m.group(12))
                return

            # Check for Metaspace line
            m = JDK8_METASPACE_LINE.search(line)
            if m:
                self._jdk8_pending_gc["metaspace_used_kb"] = int(m.group(1))
                return

    def _to_mb(self, val, unit):
        """Convert value + unit to MB."""
        multipliers = {"": 1/1024/1024, "B": 1/1024/1024, "K": 1/1024, "M": 1, "G": 1024, "T": 1024*1024}
        return val * multipliers.get(unit, 1)

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

        # Flag anomalies
        if pause_ms > 200:
            self.anomalies.append({
                "line": start_line,
                "type": "long_pause",
                "pause_ms": pause_ms,
                "description": f"Long STW pause: {pause_ms:.1f}ms",
            })

        if is_full:
            self.anomalies.append({
                "line": start_line,
                "type": "full_gc",
                "pause_ms": pause_ms,
                "description": f"Full GC detected: {pause_ms:.1f}ms",
            })

        # Flag frequent Metadata GC Threshold events
        if trigger == "Metadata GC Threshold":
            self.anomalies.append({
                "line": start_line,
                "type": "metadata_gc_threshold",
                "pause_ms": pause_ms,
                "description": f"Metadata GC Threshold triggered GC: {pause_ms:.1f}ms",
            })

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

            runtime_estimate_ms = self._estimate_runtime_ms()
            throughput = 100.0
            if runtime_estimate_ms > 0:
                throughput = max(0, 100.0 - (self.total_pause_ms / runtime_estimate_ms * 100))

            # Collector-specific metrics
            if self.collector == "ZGC":
                summary["metrics"] = self._build_zgc_metrics(
                    sorted_pauses, n, p50, p95, p99, throughput, runtime_estimate_ms
                )
            else:
                summary["metrics"] = self._build_standard_metrics(
                    sorted_pauses, n, p50, p95, p99, throughput, runtime_estimate_ms
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

        summary["health_assessment"] = self._assess_health(summary.get("metrics", {}))

        # Recent events sample
        summary["recent_events_sample"] = self.gc_events[-10:] if len(self.gc_events) >= 10 else self.gc_events

        return summary

    def _build_zgc_metrics(self, sorted_pauses, n, p50, p95, p99, throughput, runtime_estimate_ms):
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

        if runtime_estimate_ms > 0:
            freq_per_min = len(self.zgc_cycle_times) / (runtime_estimate_ms / 1000 / 60) if self.zgc_cycle_times else 0
            metrics["gc_frequency_per_minute"] = round(freq_per_min, 2)

        return metrics

    def _build_standard_metrics(self, sorted_pauses, n, p50, p95, p99, throughput, runtime_estimate_ms):
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

        if runtime_estimate_ms > 0:
            freq_per_min = n / (runtime_estimate_ms / 1000 / 60)
            metrics["gc_frequency_per_minute"] = round(freq_per_min, 2)

        return metrics

    def _estimate_runtime_ms(self):
        """Estimate total runtime from timestamps or uptime values."""
        if isinstance(self.first_timestamp, datetime) and isinstance(self.last_timestamp, datetime):
            return (self.last_timestamp - self.first_timestamp).total_seconds() * 1000
        elif isinstance(self.first_timestamp, (int, float)) and isinstance(self.last_timestamp, (int, float)):
            return (self.last_timestamp - self.first_timestamp) * 1000
        return max(self.total_pause_ms * 20, 60000)

    def _assess_health(self, metrics):
        """Assess overall GC health, with collector-specific rules."""
        issues = []

        if self.collector == "ZGC":
            # ZGC health checks
            if metrics.get("stw_max_ms", 0) > 10:
                issues.append(f"ZGC STW pause too long: {metrics['stw_max_ms']}ms (target <1ms)")
            if metrics.get("allocation_stall_count", 0) > 0:
                issues.append(f"Allocation stall detected: {metrics['allocation_stall_count']} events")
            if metrics.get("cycle_max_ms", 0) > 2000:
                issues.append(f"GC cycle time too long: {metrics['cycle_max_ms']}ms")
            # MMU check
            mmu_5ms = metrics.get("mmu", {}).get(5, 100)
            if mmu_5ms < 95:
                issues.append(f"Low MMU (5ms): {mmu_5ms}%")
        else:
            # Standard collectors (G1GC, Parallel, Serial, Shenandoah)
            if metrics.get("throughput_percent", 100) < 95:
                issues.append("Low throughput")
            if metrics.get("throughput_percent", 100) < 90:
                issues.append("Very low throughput")
            if metrics.get("max_pause_ms", 0) > 200:
                issues.append("Long maximum pause")
            if metrics.get("full_gc_count", 0) > 0:
                issues.append("Full GCs detected")
            if metrics.get("gc_frequency_per_minute", 0) > 20:
                issues.append("High GC frequency")

        # Check for metadata GC threshold anomalies
        metadata_count = sum(1 for a in self.anomalies if a["type"] == "metadata_gc_threshold")
        if metadata_count > 3:
            issues.append(f"Frequent Metadata GC Threshold events ({metadata_count})")

        if not issues:
            return {"status": "healthy", "issues": []}
        elif len(issues) <= 2:
            return {"status": "warning", "issues": issues}
        else:
            return {"status": "critical", "issues": issues}

    def extract_window(self, start_time, end_time):
        """Extract log lines within a time window."""
        start_dt = None
        end_dt = None
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError:
            pass

        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.rstrip("\n\r")
                if not line.strip():
                    print(line)
                    continue

                ts = None
                if self.format == "jdk9_unified":
                    ts = parse_jdk9_timestamp(line)
                elif self.format == "jdk8_legacy":
                    ts = parse_jdk8_timestamp(line)

                if ts and start_dt and end_dt:
                    if isinstance(ts, datetime):
                        if start_dt <= ts <= end_dt:
                            print(line)
                else:
                    print(line)

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
    else:
        summary = analyzer.analyze()
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
