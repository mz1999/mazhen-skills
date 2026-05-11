# GC Algorithm Reference

Quick reference for identifying and analyzing each supported GC algorithm.

## Identification Guide

| Algorithm | Log Signature | JDK Default |
|-----------|--------------|-------------|
| G1GC | `Pause Young (Normal)`, `Pause Young (Concurrent Start)`, `Pause Full` | JDK 9+ |
| ZGC | `Pause Mark Start`, `Pause Mark End`, `Pause Relocate Start`, `Concurrent` phases | JDK 17+ (server) |
| Shenandoah | `Pause Init Mark`, `Pause Final Mark`, `Concurrent marking` | JDK 17+ (some distros) |
| Parallel | `PSYoungGen`, `PSOldGen`, `ParOldGen` | JDK 8 (server) |
| Serial | `DefNew`, `Tenured` | JDK 8 (client/single-core) |

---

## GC Internal Mechanisms Reference

This section provides detailed explanations of GC concepts used in root cause analysis. When writing reports, use these to build reasoning chains from observation to root cause.

### The Generational Heap Model

Most JVM GCs (except ZGC/Shenandoah in some modes) divide the heap into generations based on the **weak generational hypothesis**: most objects die young.

**Young Generation (New Gen)**
- **Eden**: Where all new objects are allocated. Most objects die here and are never copied out.
- **Survivor Spaces (S0, S1)**: Two equally-sized spaces that alternate roles. Objects that survive a Young GC in Eden are copied to the current "to" Survivor space. Objects that survive multiple Young GCs in Survivor are promoted to Old Gen.
- **Promotion**: When an object has survived enough Young GCs (controlled by `-XX:MaxTenuringThreshold`, default 15), it is moved to Old Gen.

**Old Generation (Tenured)**
- Holds long-lived objects and objects that don't fit in Young Gen (e.g., humongous objects in G1).
- Collected less frequently but with more expensive algorithms.

### What Happens During a Young GC

1. **Stop-The-World (STW)**: All application threads pause.
2. **Root Scanning**: Find all root references (stack variables, static fields, JNI references, etc.).
3. **Mark Live Objects in Young Gen**: Starting from roots, trace reachable objects in Eden and current Survivor space.
4. **Copy (Evacuate) Live Objects**: Copy live objects from Eden + current Survivor to the other Survivor space (or to Old Gen if tenuring threshold reached).
5. **Clear Eden + old Survivor**: The now-empty Eden and old Survivor are reclaimed.
6. **Resume Application Threads**.

**Key Insight**: Young GC is fast because:
- Eden is typically large, but most objects die young → few objects need copying
- The copy operation is sequential and cache-friendly
- If too many objects survive, Young GC slows down dramatically

### What is "Evacuation"

Evacuation is the act of copying live objects from one memory area to another. It is the defining operation of **copying collectors** (which most Young Gen collectors are).

- **Evacuation source**: The Collection Set (CSet) — regions being collected
- **Evacuation destination**: Free regions (for Eden survivors → Survivor; for Survivor veterans → Old Gen)
- **Why it's expensive**: Every copied object requires (1) allocating space in destination, (2) copying bytes, (3) updating all references pointing to the old location

**When evacuation becomes slow**:
- Many objects survive (high survival rate)
- Objects are large (more bytes to copy)
- Objects have many references (more pointer updates)
- Destination space is fragmented or nearly full

### What is "Collection Set (CSet)"

The Collection Set is the set of heap regions selected for collection in a given GC cycle.

- **Young GC CSet**: Typically all Eden regions + optionally some Survivor regions
- **Mixed GC CSet (G1)**: Eden + some Old Gen regions with high garbage ratio
- **Full GC CSet**: The entire heap

The CSet is chosen to maximize reclaimable space while staying within the pause time target. If the CSet is too large for the pause budget, G1 may need to split the work across multiple cycles.

### What is "To-Space Exhausted"

To-space exhausted occurs when the destination space (Survivor or free regions) cannot accommodate all objects that need to be evacuated.

**What happens when to-space is exhausted**:
1. G1 tries to allocate a new region for evacuation → fails (no free regions)
2. G1 falls back to allocating directly in Old Gen (premature promotion)
3. If Old Gen is also full → objects cannot be moved → **evacuation failure**
4. This often forces a Full GC

**Why it happens**:
- Heap is too small relative to live data
- Survivor spaces are too small (`-XX:SurvivorRatio` too high)
- Object survival rate is unexpectedly high
- Humongous objects are consuming regions that could be used for evacuation

### What is a "Humongous" Object

In G1, a humongous object is any object that is **>= 1/2 of a G1 region size**.

- **Allocation**: Humongous objects are allocated directly in Old Gen, bypassing Eden entirely.
- **Why this matters**: 
  - They don't benefit from Young GC's fast copying
  - They can span multiple contiguous regions
  - They may cause fragmentation if not perfectly aligned
  - They consume regions that could otherwise be used for normal evacuation
- **Threshold**: Default region size is automatically determined by heap size:
  - Heap < 4GB → 1MB regions → humongous threshold = 512KB
  - Heap 4-8GB → 2MB regions → humongous threshold = 1MB
  - Heap 8-16GB → 4MB regions → humongous threshold = 2MB
  - ...up to 32MB regions

### What is "Concurrent Marking"

Concurrent marking is the process of finding all live objects in Old Gen **while application threads continue running**.

**Why it's needed**: Old Gen is large; scanning it during STW would take too long. So the collector marks live objects in the background.

**The challenge**: Application threads are allocating and mutating objects while marking is happening. The collector uses **snapshot-at-the-beginning (SATB)** to track changes.

**When it fails**:
- If Old Gen fills up before concurrent marking completes, the collector has no choice but to do a Full GC
- This is why `-XX:InitiatingHeapOccupancyPercent` (IHOP) matters — it triggers concurrent marking when Old Gen reaches a percentage of total heap

### What is "Allocation Stall" (ZGC)

In ZGC, application threads allocate objects by bumping a pointer in a page. When the current page is full:

1. Thread requests a new page from ZGC's page cache
2. If no free pages exist, thread must wait for concurrent relocation to free pages
3. **This waiting is the allocation stall**

**Why it's worse than STW pause**:
- STW pauses in ZGC are predictable and short (< 1ms target)
- Allocation stalls are unbounded — they last as long as it takes for ZGC to free enough pages
- They affect individual application threads at different times, making them harder to correlate with GC logs

**The root cause chain**:
Allocation stall → heap nearly full at mark start → either (a) heap too small, or (b) live set growing (leak), or (c) allocation rate spiking

### What is "Remembered Set (RSet)"

The Remembered Set tracks which Old Gen regions have references pointing into a given region.

**Why it's needed**: During Young GC, the collector must know which Old Gen objects reference Young Gen objects (so those Young Gen objects are not incorrectly collected). Without RSets, the collector would need to scan ALL of Old Gen during every Young GC — prohibitively expensive.

**RSet maintenance cost**: Every time a reference is written (e.g., `oldObj.field = youngObj`), the JVM must update the RSet. This is done via a **write barrier** and a **card table**.

**When RSets cause problems**:
- Many cross-region references → large RSets → more memory overhead
- Frequent reference mutations → high write barrier cost → application slowdown
- In G1, "RSet processing time" may appear in GC logs as a significant phase

---

## G1GC (Garbage First)

### Key Characteristics
- Region-based heap (1MB-32MB regions, default based on heap size)
- Primarily concurrent old-gen collection with STW young-gen evacuation
- Target pause time: `-XX:MaxGCPauseMillis` (default 200ms)

### Log Format (JDK 9+)
```
[0.234s][info][gc,start     ] GC(42) Pause Young (Normal) (G1 Evacuation Pause)
[0.234s][info][gc,phases    ] GC(42) Pre Evacuate Collection Set: 0.2ms
[0.234s][info][gc,phases    ] GC(42) Evacuate Collection Set: 8.5ms
[0.243s][info][gc,phases    ] GC(42) Post Evacuate Collection Set: 1.3ms
[0.244s][info][gc           ] GC(42) Pause Young (Normal) (G1 Evacuation Pause) 128M->64M(256M) 12.345ms
```

### Critical Events to Watch

**To-space exhausted**
```
[gc             ] GC(42) To-space exhausted
```
- Meaning: Survivor/eden regions couldn't accommodate evacuated objects
- Impact: Triggers Full GC or premature old-gen promotion
- Action: Increase heap, increase region size (if humongous objects), reduce allocation rate

**Humongous allocation**
```
[gc,humongous   ] GC(42) Humongous region 125 object size 1048592 start ...
```
- Meaning: Object >= 1/2 region size, allocated directly in old gen
- Impact: Can trigger unnecessary GC, fragments heap
- Action: Increase `-XX:G1HeapRegionSize` (powers of 2: 1M, 2M, 4M, ..., 32M)

**Concurrent marking**
```
[gc,start       ] GC(42) Concurrent Cycle
[gc             ] GC(42) Concurrent Cycle 234.5ms
```
- Normal background operation. If it doesn't complete before IHOP threshold, Full GC may occur.

### Phase Breakdown (Young GC)
1. **Pre Evacuate**: Root scanning, thread state setup
2. **Evacuate Collection Set**: Copy live objects to new regions (usually dominant phase)
3. **Post Evacuate**: Cleanup, update remembered sets

### Phase Breakdown (Mixed GC)
Similar to Young GC but includes old-gen regions in the collection set.

### Phase Breakdown (Full GC)
1. **Mark live objects**: Single-threaded or parallel mark
2. **Prepare for compaction**: Calculate destination addresses
3. **Adjust pointers**: Update all references
4. **Compact heap**: Move objects (dominant phase for large heaps)

---

## ZGC

### Key Characteristics
- Concurrent collector with minimal STW pauses (target: < 10ms, often < 1ms)
- Uses colored pointers and load barriers
- Does NOT compact in the traditional sense (relocates pages concurrently)

### Log Format (JDK 9+)
```
[0.234s][info][gc,start] GC(42) Pause Mark Start
[0.235s][info][gc      ] GC(42) Pause Mark Start 0.234ms
[0.235s][info][gc,start] GC(42) Concurrent Mark
[0.456s][info][gc      ] GC(42) Concurrent Mark 221.0ms
[0.456s][info][gc,start] GC(42) Pause Mark End
[0.457s][info][gc      ] GC(42) Pause Mark End 0.123ms
[0.457s][info][gc,start] GC(42) Concurrent Process Non-Strong References
[0.478s][info][gc,start] GC(42) Concurrent Reset Relocation Set
[0.489s][info][gc,start] GC(42) Pause Relocate Start
[0.490s][info][gc      ] GC(42) Pause Relocate Start 0.345ms
[0.490s][info][gc,start] GC(42) Concurrent Relocate
[0.567s][info][gc      ] GC(42) Concurrent Relocate 77.0ms
```

### Critical Events to Watch

**Allocation stall**
```
[gc,alloc      ] GC(42) Allocation Stall for application-thread 15.234ms
```
- Meaning: Application thread blocked waiting for memory
- Impact: Direct latency hit, often worse than a GC pause
- Action: Increase heap size, check for memory leak, tune `-XX:ZCollectionInterval`

**Relocation failure**
```
[gc,reloc      ] GC(42) Relocation failed
```
- Meaning: Couldn't relocate all objects in a page
- Impact: Page remains in place, fragmentation
- Action: Usually transient, monitor for patterns

### Cycle Phases
1. **Pause Mark Start** (< 1ms STW): Initiate concurrent mark
2. **Concurrent Mark**: Traverse object graph concurrently
3. **Pause Mark End** (< 1ms STW): Finalize marking
4. **Concurrent Prepare Relocation Set**: Select pages to relocate
5. **Pause Relocate Start** (< 1ms STW): Initiate relocation
6. **Concurrent Relocate**: Move objects, fix pointers via load barriers

---

## Shenandoah

### Key Characteristics
- Concurrent marking and compaction
- Brooks pointers for concurrent evacuation
- Target pause times similar to ZGC

### Log Format (JDK 9+)
```
[0.234s][info][gc,start] GC(42) Pause Init Mark
[0.234s][info][gc      ] GC(42) Pause Init Mark 0.123ms
[0.234s][info][gc,start] GC(42) Concurrent marking
[0.456s][info][gc      ] GC(42) Concurrent marking 222.0ms
[0.456s][info][gc,start] GC(42) Pause Final Mark
[0.457s][info][gc      ] GC(42) Pause Final Mark 0.456ms
[0.457s][info][gc,start] GC(42) Concurrent evacuation
[0.678s][info][gc      ] GC(42) Concurrent evacuation 221.0ms
[0.678s][info][gc,start] GC(42) Pause Init Update Refs
```

### Critical Events to Watch

**Degenerated GC**
```
[gc      ] GC(42) Degenerated GC
```
- Meaning: Concurrent cycle couldn't finish, fell back to STW
- Impact: Longer pause than normal Shenandoah pause
- Action: Usually indicates allocation pressure or heap too small

**Full GC fallback**
```
[gc      ] GC(42) Pause Full
```
- Meaning: Complete failure of concurrent approach
- Impact: Very long STW pause
- Action: Critical — increase heap significantly, check for leaks

**Pacing**
```
[gc,pacing] GC(42) Pacing application threads for ...
```
- Meaning: Slowing down mutators to let GC keep up
- Impact: Application throughput reduction
- Action: May be normal under heavy load; monitor frequency

---

## Parallel GC

### Key Characteristics
- Multi-threaded STW collector for both young and old gen
- Throughput-oriented, not latency-oriented
- Default for JDK 8 server-class machines

### Log Format (JDK 8)
```
2024-01-15T10:23:45.123+0800: [GC [PSYoungGen: 1280K->192K(1536K)] 1280K->704K(4608K), 0.0023456 secs]
2024-01-15T10:23:46.234+0800: [Full GC [PSYoungGen: 192K->0K(1536K)] [ParOldGen: 512K->448K(3072K)] 704K->448K(4608K), 0.0234567 secs]
```

### Key Metrics
- Young GC duration (typically 10-100ms)
- Full GC duration (can be seconds for large heaps)
- Throughput is the primary concern

### Tuning Direction
- `-XX:ParallelGCThreads` for young gen
- `-XX:MaxGCPauseMillis` has limited effect (only hints at adaptive sizing)
- For large heaps with latency concerns, migrate to G1GC or ZGC

---

## Serial GC

### Key Characteristics
- Single-threaded, simplest collector
- Default for single-core machines or small heaps (< 1792MB in JDK 8)
- Not suitable for production server workloads

### Log Format (JDK 8)
```
[GC [DefNew: 1280K->192K(1536K)] 1280K->704K(4608K), 0.0034567 secs]
[Full GC [Tenured: 512K->448K(3072K)] 704K->448K(4608K), 0.0456789 secs]
```

### Recommendation
If Serial GC is detected on a multi-core server, flag this as a likely misconfiguration. The JVM may have been started with `-client` or on a VM with limited reported cores.
