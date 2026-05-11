---
name: gc-log-analyzer
description: |
  Analyze and diagnose Java GC (garbage collection) logs. Use this skill whenever the user asks about GC logs, JVM memory issues, garbage collection performance, STW pauses, heap analysis, or tuning JVM garbage collectors (G1GC, ZGC, Shenandoah, Parallel, Serial). Trigger even if the user only mentions vague symptoms like "application pauses", "latency spikes", "JVM memory problems", or provides a gc.log file without explicitly asking for analysis. Also trigger when the user mentions JVM tuning, heap dumps, or wants to understand GC behavior from logs.
---

# GC Log Analyzer

Analyze Java GC logs to diagnose performance issues, identify abnormal GC events, and provide actionable tuning recommendations.

## Audience

Experienced Java engineers who understand Java but may not be deeply familiar with GC internals. Explanations should be accessible — connect GC behavior to application-level symptoms (latency spikes, throughput drops) and explain the "why" behind each observation.

## Core Principles

1. **Two-phase analysis**: Always do a global scan first to build a system-wide GC pressure profile, then drill down into anomalies. Never jump straight to individual GC events without context.
2. **Evidence-based conclusions**: Every anomaly claim must cite the original log snippet (2-5 lines, with timestamps). Include line numbers or time ranges so the user can verify.
3. **Principle over prescription**: Provide analysis direction and judgment logic. Reference values and thresholds are guidelines, not absolutes — they depend on workload characteristics and SLAs.
4. **Connect to application symptoms**: Always explain what the GC pattern means for the running application (e.g., "this 200ms STW pause directly causes tail latency spikes in your API responses").

## Input Handling

### File Size Strategy

GC logs can be very large (hundreds of MB to GBs). Never attempt to read the entire file into context.

1. **Run the extraction script first**: Use `scripts/gc_log_parser.py` to generate a statistical summary. This script handles both JDK 8 (`-XX:+PrintGCDetails`) and JDK 9+ (`-Xlog:gc*`) formats.
   ```bash
   python3 scripts/gc_log_parser.py /path/to/gc.log --summary > gc_summary.json
   ```
2. **Read the summary** to identify:
   - GC algorithm
   - Total GC count, total pause time, max pause time
   - Throughput (time spent not in GC)
   - Anomaly timestamps (pauses above threshold, memory pressure spikes)
3. **Selective deep read**: Based on the summary, use the script to extract specific time windows:
   ```bash
   python3 scripts/gc_log_parser.py /path/to/gc.log --window-start "2024-01-15T10:23:45" --window-end "2024-01-15T10:24:00" > window.log
   ```
4. **If the log is small** (< 5000 lines), you may read it directly, but still run the script for structured metrics.

### Format Detection

GC logs come in multiple formats. Detection order:

1. **JDK 9+ Unified Logging** (`-Xlog:gc*`): Contains `[gc]` tags, bracketed metadata like `[0.234s][info][gc]`.
2. **JDK 8 Legacy** (`-XX:+PrintGCDetails -XX:+PrintGCDateStamps`): Starts with timestamps like `2024-01-15T10:23:45.123+0800` or `[GC ...]` without tags.
3. **Plain `-XX:+PrintGC`** (minimal): Only basic pause info, lacks phase breakdown. Flag this to the user as insufficient for deep analysis.

If the format is ambiguous, examine the first 20 lines and match against known patterns. See `references/jdk_formats.md` for detailed format signatures.

### JVM Arguments

If available, also read the JVM startup parameters (often in application logs or provided by the user). Key parameters to check:
- `-Xms`, `-Xmx` (heap size)
- `-XX:+UseG1GC`, `-XX:+UseZGC`, `-XX:+UseShenandoahGC`, `-XX:+UseParallelGC`
- `-XX:MaxGCPauseMillis`, `-XX:G1HeapRegionSize`
- `-XX:ConcGCThreads`, `-XX:ParallelGCThreads`

These parameters provide critical context for interpreting GC behavior. For example, a 5-second pause may be normal for a 100GB heap with default settings, but alarming for a 4GB heap tuned for 100ms pauses.

## Phase 1: Global Scan

Build a system-wide GC pressure profile. Do not skip this phase.

### Step 1: Identify GC Algorithm

Determine which collector is in use. Look for:
- G1GC: `[gc,start ] GC(42) Pause Young (Normal)`, `[gc,start ] GC(42) Pause Full`
- ZGC: `[gc,start ] GC(42) Pause Mark Start`, `[gc ] GC(42) Concurrent Mark`
- Shenandoah: `[gc,start ] GC(42) Pause Init Mark`, `[gc ] GC(42) Concurrent evacuation`
- Parallel: `[gc,start ] PSYoungGen: ...`, `[Full GC ...]`

Read `references/gc_algorithms.md` for the complete list of format signatures and key metrics per algorithm.

### Step 2: Extract Key Metrics

For **all algorithms**, collect:
- **Throughput**: Percentage of total runtime NOT spent in GC pauses. Target: > 95% for most applications, > 99% for latency-sensitive.
- **Pause time distribution**: Min / avg / p50 / p95 / p99 / max STW pause.
- **GC frequency**: Events per minute.
- **Heap pressure**: Peak used vs committed heap over time.

For **G1GC specifically**:
- Young GC frequency and duration
- Mixed GC frequency (indicates old-gen pressure)
- Full GC count (should be zero in healthy systems)
- Humongous object allocation frequency
- To-space exhausted events (indicates allocation rate exceeding evacuation speed)

For **ZGC specifically**:
- Mark/Relocate cycle duration
- Allocation stall events (critical — indicates heap exhaustion during concurrent phase)
- Page cache hit rate

For **Shenandoah specifically**:
- Pacing delays (indicates allocation pressure)
- Degenerated/full GC fallbacks (should be rare)
- Concurrent mark/compact durations

### Step 3: Flag Anomaly Events

Flag events matching these patterns (adjust thresholds based on application SLA):

| Anomaly | Typical Threshold | Why It Matters |
|---------|------------------|----------------|
| Long STW pause | > 200ms (G1), > 10ms (ZGC/Shenandoah) | Directly impacts latency |
| Full GC | Any occurrence | Stop-the-world evacuation of entire heap, usually indicates failure of incremental collection |
| Frequent Young GC | > 20/min | High allocation rate or undersized young gen |
| Increasing old-gen usage | Steady upward trend across cycles | Memory leak or promotion rate exceeding collection rate |
| To-space exhausted (G1) | Any occurrence | Evacuation failure — objects couldn't be copied fast enough |
| Allocation stall (ZGC) | Any occurrence | Application threads blocked waiting for memory |
| Humongous allocation (G1) | Frequent occurrences | Bypasses normal allocation path, can trigger premature GC |

### Step 4: Health Overview

Summarize in 3-5 bullet points:
- Overall GC pressure level (Low / Moderate / High / Critical)
- Whether the system is meeting its pause-time goals
- The most significant anomaly category
- Time windows where problems concentrate

#### Load Pattern Inference (must include in executive summary)

Based on GC frequency stability, pause time distribution, and memory usage trends, infer the application's workload pattern:

**Sustained High Pressure**
- Signals: GC frequency consistently high (>15/min) with little variance; pause times gradually worsen; heap usage climbs steadily between GCs; no quiet periods.
- What it means: The application is under constant heavy load — likely a high-throughput service processing requests at capacity. GC pressure is not caused by a burst but by sustained allocation rate exceeding collection rate.
- Example: "GC occurs every 3-4 seconds like clockwork, with Young GC pauses growing from 8ms to 100ms over 30 seconds. This indicates the application is running flat-out, not handling a temporary spike."

**Occasional Peaks / Bursts**
- Signals: GC frequency has a clear baseline (e.g., 2-5/min) with sudden clusters of frequent GC; long pauses are isolated and correlated with specific timestamps; heap usage spikes then recovers.
- What it means: The application has a normal steady-state load, but experiences periodic bursts — possibly scheduled jobs, batch processing, traffic spikes, or cache warming.
- Example: "GC runs every 15-20 seconds normally, but at 10:23:45 there were 5 GCs in 10 seconds with a 400ms pause. This isolated burst suggests a specific event (batch job, cache refresh, or traffic spike) rather than systemic overload."

**Idle / Low Load with Background Pressure**
- Signals: GC frequency very low (<1/min); pauses are short; heap usage is stable or slowly creeping up; occasional long pause when GC finally triggers.
- What it means: The application is mostly idle, but some background process (timer, heartbeat, scheduled task) allocates objects periodically. A slowly creeping heap may indicate a minor leak that only becomes visible over long idle periods.
- Example: "Only 3 GCs in 5 minutes, each <20ms. Heap sits at 30% with gradual 1% per hour growth. The system is nearly idle, but the slow heap growth warrants monitoring for a small leak."

**Bimodal / Cyclic Pattern**
- Signals: GC metrics oscillate between two distinct states (e.g., quiet periods with rare GC, then intense GC bursts); pattern repeats at regular intervals.
- What it means: The application has distinct load phases — possibly day/night cycles, on/off-peak traffic, or alternating batch and real-time processing.
- Example: "GC is quiet for 10 minutes (1 GC/min), then suddenly 20 GCs/min for 2 minutes. This 12-minute cycle matches a known batch job schedule."

**Diurnal / Time-of-Day Pattern**
- Signals: Metrics change dramatically based on time of day (e.g., timestamps show morning vs. evening).
- What it means: Business-hours traffic pattern. GC issues may only manifest during peak hours.
- Example: "From 02:00-06:00, GC pauses average 15ms. From 09:00-18:00, they average 120ms with frequent Full GCs. The problem is load-dependent, not a code leak."

> **Important**: Always state your confidence level (high/medium/low) and what additional data would strengthen the inference (e.g., application QPS metrics, CPU usage, business event logs).

## Phase 2: Deep Dive

For each anomaly flagged in Phase 1, perform a root-cause analysis.

### Step 1: Prioritize Anomalies

Sort by impact:
1. **Allocation stalls / Full GCs** — application threads blocked
2. **Long STW pauses** — tail latency impact
3. **Frequent GC** — throughput impact
4. **Memory pressure trends** — risk of future failures

### Step 2: Extract Complete Trace

Locate the full GC event in the raw log. For a significant pause, you need:
- The complete log lines for that single GC event (may span 10-50 lines for G1)
- 2-3 events immediately before and after (for trend context)
- The exact timestamp and line number range

### Step 3: Phase Breakdown

Break down the pause into its constituent phases. For example, a G1 Young GC:

```
[0.234s][info][gc] GC(42) Pause Young (Normal) (G1 Evacuation Pause) 128M->64M(256M) 12.345ms
[0.234s][info][gc] GC(42) Phase 1: Mark live objects 2.1ms
[0.236s][info][gc] GC(42) Phase 2: Prepare for compaction 1.3ms
[0.238s][info][gc] GC(42) Phase 3: Adjust pointers 3.2ms
[0.241s][info][gc] GC(42) Phase 4: Compact heap 5.7ms
```

Identify which phase dominates the pause time. This is the key to root cause.

Read `references/gc_algorithms.md` for the phase breakdown structure of each collector.

### Step 4: Contextual Analysis

Examine the surrounding events:
- Is this an isolated spike or part of a sustained pattern?
- What was the heap state before the GC? (High occupancy reduces headroom for concurrent phases.)
- Was there a burst of allocation immediately before?
- For G1: was this preceded by a series of concurrent marking cycles?

### Step 5: Root Cause & Recommendation — The Reasoning Chain

For each anomaly, build a **reasoning chain** that walks from the observed phenomenon to the root cause. Do NOT jump directly to conclusions. The audience knows Java but may not know GC internals — explain each step.

**Required structure for every root cause explanation:**

```
1. 现象（Observed Phenomenon）: 从日志中看到什么具体数据
2. 机制（GC Mechanism）: 这个 GC phase/指标在正常情况下做什么，什么因素会影响它的耗时
3. 推导（Deduction）: 结合日志中的其他证据，一步步推导出为什么会这样
4. 根因（Root Cause）: 最终的根因判断
5. 验证（Validation）: 这个根因是否能解释所有观察到的现象
```

**Example — G1GC Evacuation Phase Dominating Pause:**

*现象*: Evacuate Collection Set 耗时 78.2ms，占总 pause 95%。

*机制*: 
- **什么是 Collection Set (CSet)**：CSet 是本次 GC 决定回收的一组 region，通常包含所有 Eden region 和部分 Survivor/Old region。
- **什么是 Evacuation**：GC 遍历 CSet 中所有存活对象，把它们复制到新分配的 region 中。Eden 中的存活对象 → Survivor；Survivor 中熬过多轮 GC 的对象 → Old Gen。
- **什么因素决定 evacuation 耗时**：(1) CSet 中存活对象的数量和大小；(2) 对象之间的引用复杂度（需要更新引用）；(3) 可用的空闲 region 是否充足（如果不足，需要额外分配，耗时增加）。

*推导*:
- 观察 1: evacuation 占 95% → 问题出在对象复制阶段。
- 观察 2: GC 后 Eden 从 64 regions 降到 0，但 Survivor 从 24 膨胀到 32 → 说明 Eden 中大量对象存活了下来，需要被复制到 Survivor。
- 观察 3: Survivor 持续膨胀（24→32→40）→ 这些对象在 Survivor 中熬过一轮又一轮，迟迟未能被回收或晋升到老年代。
- 观察 4: 老年代 region 数始终 128，没有减少 → 老年代也没有被有效回收。
- 综合: 大量短生命周期对象没有被及时回收，导致每次 Young GC 都需要复制大量数据。Survivor 空间不足时，触发 to-space exhausted。

*根因*: **存活对象率过高 + Survivor 空间不足**。可能原因：(a) 应用分配了大量临时大对象；(b) 某些对象的生命周期比预期长（如缓存、会话）；(c) 堆太小，Survivor 空间被压缩。

*验证*: 这个根因同时解释了：(1) evacuation 时间长；(2) Survivor 膨胀；(3) to-space exhausted；(4) 最终 Full GC。如果是单纯分配速率问题，evacuation 时间会随对象大小波动；但这里 Survivor 持续膨胀，说明是存活率问题。

---

**Example — ZGC Allocation Stall:**

*现象*: Allocation stall 30.5ms，应用线程被阻塞。

*机制*:
- **ZGC 如何分配对象**：ZGC 使用 page-based 分配。应用线程从当前 page 的顶部 bump-pointer 分配对象。
- **什么时候会 stall**：当当前 page 已满，且 GC 的 concurrent relocate 尚未释放足够的空 page 时，应用线程必须等待。
- **为什么 ZGC 选择 stall 而不是 OOM**：ZGC 的设计目标是在并发阶段完成几乎所有工作，但并发阶段需要时间。如果分配速率超过并发回收速率，就只能阻塞分配者。

*推导*:
- 观察 1: Mark Start 时堆始终 100% 满 → 几乎没有空闲 page。
- 观察 2: Relocate End 后只降到 87% → GC 回收的效率在下降（GC200 能降到 75%，GC201+ 只能降到 87%）。
- 观察 3: Stall 时间从 15ms 恶化到 30ms → 等待时间越来越长，说明回收越来越跟不上分配。
- 综合: 存活对象集在增长，或者分配速率在增加，导致 ZGC 的并发 relocate 无法及时释放足够空间。

*根因*: **堆空间相对于存活对象集 + 分配速率来说不足**。不是 ZGC 的 STW pause 问题（STW 确实 <1ms），而是并发回收的吞吐量不够。

*验证*: 如果增大堆到 16GB，Mark Start 时堆使用率降到 50%，allocation stall 应该消失。如果 stall 依然存在，说明是分配速率突增或内存泄漏。

---

**Quick Reference for Common GC Behaviors**

| 观察到的现象 | 背后的 GC 机制 | 可能的根因方向 |
|-------------|--------------|--------------|
| Survivor 区域持续膨胀 | 对象在 Survivor 中熬过多次 GC 仍未被回收或晋升 | 短生命周期对象过多；对象生命周期被延长（缓存、session）；Survivor 空间不足 |
| Eden regions 每次 GC 后恢复数量减少 | Eden 空间被压缩，GC 触发更频繁 | 堆整体不足；老年代占用挤压了 Eden 空间 |
| Evacuation 时间占总 pause 的 80%+ | 存活对象量大，复制成本高 | 存活率过高；对象体积大；引用关系复杂 |
| Pre Evacuate 时间长 | Root set 扫描耗时 | 线程数多；JNI/global reference 多 |
| Post Evacuate 时间长 | Remembered set 更新、清理 | 跨 region 引用多；card table 扫描量大 |
| Concurrent Mark 时间长 | 遍历的对象图大 | 老年代存活对象多；存在深引用链 |
| Full GC 后老年代残留持续增长 | 每次 Full GC 都有对象无法回收 | 内存泄漏；静态缓存持续增长；session 未过期 |
| Allocation stall 持续恶化 | 并发回收速率 < 分配速率 | 堆不足；分配速率增加；存活对象集增长 |
| ZGC heap 使用率 Mark Start 始终 >90% | 几乎没有 headroom 给并发阶段 | 堆太小；泄漏；或应用设计需要更大堆 |

---

**Tuning Recommendations by Pattern**

**G1GC:**
- *Long evacuation phase + to-space exhausted*: 存活对象率过高或 Survivor 不足。先检查对象生命周期（是否有过期缓存），再考虑增大堆或 `-XX:SurvivorRatio`。
- *Frequent Full GC with high old-gen occupancy*: 并发标记跟不上。降低 `-XX:InitiatingHeapOccupancyPercent`（如从 45 降到 35），让标记更早启动。
- *Humongous allocations dominating*: 增大 `-XX:G1HeapRegionSize`（2 的幂次：1M, 2M, 4M...32M）。注意 region 大小决定 humongous 阈值（>= 1/2 region size）。

**ZGC:**
- *Allocation stalls*: 增大堆是最有效的手段。如果业务负载稳定但 stall 出现，优先增大堆；如果负载在增长，需排查泄漏。
- *Long concurrent mark*: 老年代对象图大。检查是否有超大对象树或深层嵌套结构。

**General principles:**
- Always prefer increasing heap size before adding GC threads (more threads = more CPU contention).
- Memory leaks are diagnosed by sustained upward trend in old-gen occupancy across multiple full cycles, not by a single high value.
- For latency-sensitive applications, the 99th percentile pause matters more than average pause.

## Report Template

ALWAYS output the final analysis using this structure:

```markdown
# GC 诊断报告：{一句话结论}

## 1. 执行摘要
- GC 算法：{类型}（JDK {版本推断}）
- 整体健康度：{优秀/良好/警告/严重}
- 负载特征：{持续高压/偶尔峰值/空闲低负载/周期性波动}（置信度：{高/中/低}）
- 核心问题：{1-2句话概括最严重的发现}

## 2. 关键指标
| 指标 | 值 | 评估 |
|------|-----|------|
| 吞吐量 | X% | {OK/警告/严重} |
| 最大 STW 停顿 | Xms | {OK/警告/严重} |
| P99 停顿 | Xms | {OK/警告/严重} |
| GC 频率 | X 次/分钟 | {OK/警告/严重} |
| Full GC 次数 | X | {OK/警告/严重} |

## 3. 异常事件分析

### 事件 1：{简短描述}
- **时间**：{timestamp}（日志第 X 行）
- **原始日志**：
  ```
  {2-5 行原始日志}
  ```
- **根因**：{结合 GC 原理解释为什么这一步慢}
- **影响**：{对应用的具体影响}
- **建议**：{调优方向}

### 事件 2：...

## 4. 趋势与模式
- {内存使用趋势}
- {GC 频率/停顿时间趋势}
- {是否为孤立事件 or 系统性问题}

## 5. 优化建议（按优先级排序）
1. {高优先级，通常解决最严重的问题}
2. {中优先级}
3. {低优先级或预防性措施}
```

## Critical Reminders

1. **Never skip Phase 1.** Even if the user points to a specific long pause, always provide the global context first.
2. **Cite evidence for every claim.** "Long pause" is not enough — say "Pause of 450ms at 10:23:45 (line 1242), driven by 380ms evacuation phase."
3. **Explain the why.** Don't just say "increase heap" — explain that "the concurrent marking cycle couldn't complete before old gen filled, forcing a Full GC. A larger heap gives the concurrent phase more headroom."
4. **Distinguish correlation from causation.** High GC frequency after a deployment might be due to new code allocating more, not a GC tuning issue.
5. **Be honest about uncertainty.** If the log doesn't contain enough information to determine root cause (e.g., missing JVM args), say so and explain what additional information would help.
