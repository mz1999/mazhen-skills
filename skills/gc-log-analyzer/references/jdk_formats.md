# JDK GC Log Format Reference

GC log formats changed significantly between JDK 8 and JDK 9. This reference helps identify which format you're dealing with.

## JDK 8 Legacy Format

Enabled by:
```bash
-XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:gc.log
# Optional: -XX:+PrintGCTimeStamps for relative time since JVM start
# Optional: -XX:+PrintGCApplicationStoppedTime for safepoint info
# Optional: -XX:+PrintAdaptiveSizePolicy for sizing decisions
```

### Format Characteristics
- Timestamps: ISO-8601 with timezone (`2024-01-15T10:23:45.123+0800:`)
- No bracketed tags like `[gc,start]`
- Collector name embedded in event: `[GC`, `[Full GC`, `[CMS-concurrent-mark-start]`
- Heap info in same line: `[PSYoungGen: before->after(committed)]`

### Example: Parallel GC
```
2024-01-15T10:23:45.123+0800: [GC [PSYoungGen: 1280K->192K(1536K)] 1280K->704K(4608K), 0.0023456 secs] [Times: user=0.01 sys=0.00, real=0.00 secs]
2024-01-15T10:23:46.234+0800: [Full GC [PSYoungGen: 192K->0K(1536K)] [ParOldGen: 512K->448K(3072K)] 704K->448K(4608K) [PSPermGen: 256K->256K(2048K)], 0.0234567 secs] [Times: user=0.05 sys=0.00, real=0.02 secs]
```

### Example: G1GC
```
2024-01-15T10:23:45.123+0800: [GC pause (G1 Evacuation Pause) (young), 0.0123456 secs]
   [Parallel Time: 8.5 ms, GC Workers: 4]
      [GC Worker Start (ms):  234.5  234.6  234.7  234.8]
      [Ext Root Scanning (ms): 1.2 1.3 1.1 1.4]
      ...
   [Code Root Fixup: 0.1 ms]
   [Clear CT: 0.3 ms]
   [Other: 3.5 ms]
      [Choose CSet: 0.1 ms]
      [Ref Proc: 2.1 ms]
      [Ref Enq: 0.2 ms]
      [Free CSet: 0.8 ms]
   [Eden: 128.0M(128.0M)->0.0B(128.0M) Survivors: 16.0M->16.0M Heap: 256.0M(512.0M)->192.0M(512.0M)]
```

### Example: CMS (for reference, not analyzed)
```
2024-01-15T10:23:45.123+0800: [GC [1 CMS-initial-mark: 512K(3072K)] 704K(4608K), 0.0012345 secs]
2024-01-15T10:23:45.125+0800: [CMS-concurrent-mark-start]
2024-01-15T10:23:45.345+0800: [CMS-concurrent-mark: 0.220/0.220 secs]
```

---

## JDK 9+ Unified Logging Format

Enabled by:
```bash
-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=10,filesize=100m
```

Components of the `-Xlog` syntax:
- `gc*` — selector, matches all gc-related log tags
- `file=gc.log` — output to file
- `time,uptime,level,tags` — decorations to include
- `filecount=10,filesize=100m` — rotation

### Format Characteristics
- Decorations in brackets: `[time][uptime][level][tags]`
- Level: `trace`, `debug`, `info`, `warning`, `error`
- Tags: `gc`, `gc,start`, `gc,phases`, `gc,heap`, `gc,ergo`, etc.
- GC events numbered: `GC(42)`, `GC(43)`, etc.

### Example: G1GC
```
[2024-01-15T10:23:45.123+0800][234.567s][info][gc,start     ] GC(42) Pause Young (Normal) (G1 Evacuation Pause)
[2024-01-15T10:23:45.123+0800][234.567s][info][gc,task      ] GC(42) Using 4 workers of 4 for evacuation
[2024-01-15T10:23:45.125+0800][234.569s][info][gc,phases    ] GC(42) Pre Evacuate Collection Set: 0.2ms
[2024-01-15T10:23:45.133+0800][234.577s][info][gc,phases    ] GC(42) Evacuate Collection Set: 7.8ms
[2024-01-15T10:23:45.135+0800][234.579s][info][gc,phases    ] GC(42) Post Evacuate Collection Set: 1.5ms
[2024-01-15T10:23:45.135+0800][234.579s][info][gc           ] GC(42) Pause Young (Normal) (G1 Evacuation Pause) 128M->64M(256M) 12.012ms
[2024-01-15T10:23:45.135+0800][234.579s][info][gc,heap      ] GC(42) Eden regions: 64->0(64)
[2024-01-15T10:23:45.135+0800][234.579s][info][gc,heap      ] GC(42) Survivor regions: 8->8(9)
[2024-01-15T10:23:45.135+0800][234.579s][info][gc,heap      ] GC(42) Old regions: 32->32
[2024-01-15T10:23:45.135+0800][234.579s][info][gc,heap      ] GC(42) Humongous regions: 0->0
```

### Example: ZGC
```
[2024-01-15T10:23:45.123+0800][234.567s][info][gc,start] GC(42) Pause Mark Start
[2024-01-15T10:23:45.124+0800][234.568s][info][gc      ] GC(42) Pause Mark Start 0.234ms
[2024-01-15T10:23:45.124+0800][234.568s][info][gc,start] GC(42) Concurrent Mark
[2024-01-15T10:23:45.345+0800][234.789s][info][gc      ] GC(42) Concurrent Mark 221.0ms
[2024-01-15T10:23:45.345+0800][234.789s][info][gc,start] GC(42) Pause Mark End
[2024-01-15T10:23:45.346+0800][234.790s][info][gc      ] GC(42) Pause Mark End 0.123ms
[2024-01-15T10:23:45.346+0800][234.790s][info][gc,start] GC(42) Concurrent Prepare Relocation Set
[2024-01-15T10:23:45.367+0800][234.811s][info][gc      ] GC(42) Concurrent Prepare Relocation Set 21.0ms
[2024-01-15T10:23:45.367+0800][234.811s][info][gc,start] GC(42) Pause Relocate Start
[2024-01-15T10:23:45.368+0800][234.812s][info][gc      ] GC(42) Pause Relocate Start 0.345ms
[2024-01-15T10:23:45.368+0800][234.812s][info][gc,start] GC(42) Concurrent Relocate
[2024-01-15T10:23:45.445+0800][234.889s][info][gc      ] GC(42) Concurrent Relocate 77.0ms
```

---

## Quick Format Detection

Look at the first 5-10 lines:

1. **Contains `[gc,start]` or `[gc,phases]` with bracketed tags?** → JDK 9+ Unified Logging
2. **Starts with ISO timestamp like `2024-01-15T...` followed by `[GC` or `[Full GC`?** → JDK 8 Legacy
3. **Contains `GC(42)` with numbered events?** → JDK 9+ Unified Logging
4. **Contains `PSYoungGen`, `ParOldGen`, `DefNew`, `Tenured`?** → JDK 8 Legacy (or explicitly configured in JDK 9+)
5. **Minimal format: just `[GC ...]` with no heap details?** → `-XX:+PrintGC` only, insufficient for analysis

---

## Common Decorations

| Decoration | Example | Meaning |
|------------|---------|---------|
| `time` | `[2024-01-15T10:23:45.123+0800]` | Wall-clock timestamp |
| `uptime` | `[234.567s]` | Seconds since JVM start |
| `level` | `[info]` | Log level |
| `tags` | `[gc,start]` | Log tags (category) |
| `pid` | `[12345]` | Process ID |
| `tid` | `[67890]` | Thread ID |

---

## Important Note on Mixed Formats

JDK 9+ can still output legacy-style GC logs if explicitly configured with the old flags (they are mapped to unified logging internally). The output may look like a hybrid. In such cases:
- If you see both `[gc,start]` tags AND legacy `PSYoungGen` format, treat as JDK 9+ Unified Logging with legacy backend
- The `-Xlog:gc*` format is preferred for analysis because it has more detailed phase breakdowns
