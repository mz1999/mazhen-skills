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

1. **Ensure dependencies are installed**: The parser uses `numpy`/`scipy` for heap trend regression analysis.
   ```bash
   pip3 install numpy scipy
   ```
   If unavailable, trend analysis gracefully degrades to `insufficient_data`.

2. **Run the extraction script first**: Use `scripts/gc_log_parser.py` to generate a statistical summary. This script handles both JDK 8 (`-XX:+PrintGCDetails`) and JDK 9+ (`-Xlog:gc*`) formats.
   ```bash
   python3 scripts/gc_log_parser.py /path/to/gc.log --summary > gc_summary.json
   ```
   解析器输出的字段精确语义见 `references/parser_output.md`。
3. **Read the summary** to identify:
   - GC algorithm
   - Total GC count, total pause time, max pause time
   - Throughput (time spent not in GC)
   - Anomaly timestamps (pauses above threshold, memory pressure spikes)
4. **Selective deep read**: Based on the summary, use the script to extract specific time windows:
   ```bash
   python3 scripts/gc_log_parser.py /path/to/gc.log --window-start "2024-01-15T10:23:45" --window-end "2024-01-15T10:24:00" > window.log
   ```
   For JDK 8 legacy logs where GC events span multiple lines and timestamp parsing can be unreliable, prefer line-number-based extraction (the summary includes line numbers for every anomaly):
   ```bash
   python3 scripts/gc_log_parser.py /path/to/gc.log --window-start-line 1240 --window-end-line 1260 > window.log
   ```
5. **Extract anomaly context**: For Phase 2 deep dive, get each anomaly with surrounding raw log lines:
   ```bash
   python3 scripts/gc_log_parser.py /path/to/gc.log --anomalies --context-lines 5 > anomalies.json
   ```
   Output: anomaly objects with `context_lines` (raw log array) and `context_range` (line numbers).
   Note: `--context-lines N` means N lines before and N lines after the anomaly line, totaling approximately `2N+1` lines.
6. **If the log is small** (< 5000 lines), you may read it directly, but still run the script for structured metrics.

## Phase 1: Global Scan

Build a system-wide GC pressure profile. Do not skip this phase.

### Understanding Parser Output: What anomalies are and are not

**`anomalies` 数组只包含"零容忍型异常"**——任何一次出现即代表 JVM 行为超出正常设计范围的事件。parser 不做阈值判断，不做频率统计。

当前 parser 标记的零容忍异常：
- `full_gc` — Full GC（所有收集器）
- `allocation_stall` — ZGC 分配停顿（应用线程被阻塞）
- `to_space_exhausted` — G1 To-space 耗尽（evacuation failure）
- `humongous_allocation` — G1 Humongous 对象分配
- `degenerated_gc` — Shenandoah 退化 GC（并发失败回退 STW）
- `concurrent_mark_overflow` — G1 并发标记溢出重置

**以下异常 parser 不标记，需要你从聚合数据中自行判断**（参考阈值见 Step 2）：
- 长停顿 → 从 `metrics.max_pause_ms` / `pause_by_type` 判断（参考：G1 STW > 200ms、ZGC/Shenandoah > 10ms 即视为异常）
- 频繁 GC → 从 `metrics.gc_frequency_per_minute` 判断（参考：Young GC > 20/分钟需关注）
- VM 操作开销 → 从 `vm_operations` 判断（参考：`total_ms / total_pause_ms > 10%` 或 `max_ms > 200ms`）
- 堆泄漏 → 从 `heap_trend` 判断（参考：`leak_risk` 为 medium/high，或 `post_full_gc_slope_kbps > 0`）
- Metaspace 不足 → 从 `gc_causes` 中 "Metadata GC Threshold" 的次数判断（参考：> 3 次需关注）
- Mixed GC 低效 → 从 `pause_by_type` 中 Mixed vs Young 对比判断（参考：Mixed avg > 2x Young avg）
- 晋升过快 → 从 `promotion` 判断（参考：`avg_promoted_per_gc_mb` > Survivor 空间大小）

**以上列表是常见异常类型，但不穷尽**。你应结合所有聚合数据主动发现其他异常模式，例如：
- 停顿时间的双峰分布（大多数 Young GC 正常，但偶尔跳到异常高值）
- GC 频率的突然跳变（`pause_intervals_ms.p95 / avg > 3x` 表明间隔高度不规则）
- 堆占用的周期性波动（`heap_trigger_stats` 中占用率规律性地接近上限）
- 并发周期的持续延长（`concurrent_cycles` 中 avg 逐段上升）

**重要**：如果 `anomalies` 数组为空，不代表系统健康。必须从 `metrics`、`pause_by_type`、`heap_trend`、`gc_causes`、`pause_intervals_ms`、`concurrent_cycles` 等聚合数据中做完整分析。

### Step 1: Extract Key Metrics

读取 parser 输出的完整 summary JSON（所有字段的精确语义见 `references/parser_output.md`），重点关注以下维度：

**核心指标（所有收集器通用）**：
- 停顿分布：`metrics.max_pause_ms` / `min_pause_ms` / `avg_pause_ms` / `p50_pause_ms` / `p95_pause_ms` / `p99_pause_ms`
- 吞吐：`metrics.throughput_percent`
- 频率：`metrics.gc_frequency_per_minute`
- 总量：`metrics.total_gc_events` / `metrics.total_pause_ms` / `metrics.full_gc_count`
- 零容忍异常：`anomaly_counts` / `anomalies`

**按收集器重点关注的维度**：
- **G1**：`pause_by_type`（Mixed vs Young 对比）、`concurrent_cycles`（reset-for-overflow）、`g1_detail_phases`、`promotion`、`heap_trigger_stats`
- **ZGC**：`metrics.allocation_stall_count` / `allocation_stall_ms`、`metrics.cycle_*`、`metrics.mmu`
- **Shenandoah**：`anomaly_counts.degenerated_gc`、`concurrent_cycles`

**通用分析维度（按需提取）**：
- 堆趋势：`heap_trend`（泄漏检测与 OOM 预估）
- 触发原因：`gc_causes`（Metaspace/GCLocker/System.gc 等问题）
- VM 开销：`vm_operations`（非 GC safepoint）
- 内存效率：`memory_efficiency` / `gc_efficiency`
- 启动期：`startup_analysis`（区分启动期行为 vs 稳态问题）
- 近期样本：`recent_events_sample`（快速了解最近 10 个 GC 事件）
- 间隔规律：`pause_intervals_ms`（分配速率突增、GC 压力变化）

**Phase 2 定位坐标（用于提取具体事件上下文）**：
- 最长停顿：`top_pauses`（前 20 个 STW 事件，含行号）
- Full GC 清单：`full_gc_events`（全部 Full GC，含行号）
- 按类型 Top：`top_by_type`（Mixed/Young 等类型各自的最长事件）
- 按原因 Top：`top_by_cause`（Metadata GC Threshold/GCLocker 等各自的最长事件）
- GC 节奏：`gc_cadence`（每分钟 GC 次数，定位频率突增窗口）
- 堆采样：`heap_samples`（堆占用时间序列，验证泄漏趋势）
- Safepoint 事件：`safepoint_events`（非 GC safepoint，含行号）
- 晋升风暴：`promotion_spikes`（晋升量最大的事件）

### Step 2: Flag Anomaly Events

根据应用 SLA 调整阈值，标记以下异常。**记录每个异常的时间戳和行号，用于 Step 4 的启动期判断。**

- **零容忍（任何出现即异常）**：Full GC（所有收集器）、To-space exhausted（G1）、Allocation stall（ZGC）、Humongous allocation（G1）、Degenerated GC（Shenandoah）、Concurrent mark overflow（G1）
- **超过算法典型阈值**：G1 STW > 200ms、ZGC/Shenandoah STW > 1ms、Young GC 频率 > 20/分钟
- **结合 `heap_trend` 判断**：堆斜率显著为正且 R² > 0.7、Full GC 后堆仍持续增长

> **注意**：启动期（前 3-5 分钟）出现的异常同样要标记，不要在 Step 2 中过滤掉。启动期的上下文在 Step 4 和 Phase 2 中处理。
>
> 特别地，**启动期高频 GC（>20/分钟）要标记**——虽然这是常见的启动期行为，但不要预先判断"这是正常的所以跳过"。标记后交给 Step 4 做启动期确认，在 Report 中标注【启动期】。

### Step 2b: Heap Trend & Leak Risk Assessment

读取 `heap_trend`（需 `numpy`/`scipy`，否则跳过）：

- `leak_risk` 为 medium/high → 标记异常；`estimated_hours_to_oom` < 24h → 紧急
- `post_full_gc_slope_kbps > 0` → Full GC 后堆仍在增长，结合老年代趋势判断是否为泄漏或静态缓存增长
- **注意**：`confidence: low` 时（样本不足，通常 < 10 个 GC 事件；或缺少 `numpy`/`scipy`），不输出泄漏风险判断

### Step 2c: VM Operations & Pause Interval Check

- `vm_operations.max_ms` > 200ms → 单个非 GC safepoint 极长
- `vm_operations.total_ms` / `estimated_runtime_ms` > 1% → 非 GC safepoint 累计时间占运行时间比例过高
- `pause_intervals_ms.min` < 100ms → 两次 GC 间隔极短
- `pause_intervals_ms.p95` / `avg` > 3x → 间隔高度不规则
- `pause_intervals_ms.avg` 明显偏低（如 < 1 秒）→ 分配速率突增或 GC 压力高。判断"持续下降"需手动切分时间窗口对比，parser 单次输出不提供趋势序列

### Step 3: Health Overview

Summarize in 3-5 bullet points:
- Overall GC pressure level (Low / Moderate / High / Critical)
- Whether the system is meeting its pause-time goals
- The most significant anomaly category
- Time windows where problems concentrate

### Step 3c: GC Efficiency Check

读取 `gc_efficiency`，作为健康评估的参考维度：

- `avg_performance_mbps < 0.1` → 可能正在 thrashing（高频率、极低单产）
- `full_gc_performance_mbps` >> `regular_gc_performance_mbps` → 普通 GC 回收能力不足的警告信号
- `freed_mem_per_minute` 低但 `gc_frequency_per_minute` > 20 → 分配速率可能超过 GC 吞吐能力

### Step 3d: GC Cause Distribution Check

读取 `gc_causes`，分析触发原因分布：

- "Metadata GC Threshold" 频繁 → Metaspace 增长模式，关注启动期 vs 稳态分布
- "GCLocker Initiated GC" 频繁 → JNI critical section 使用模式
- "System.gc()" 出现 → 代码中可能存在显式调用
- 任一原因的 `avg_pause_ms` > 2x 整体 avg → 该原因触发的 GC  disproportionately expensive

#### 负载模式推断（必须包含在执行摘要中）

根据 GC 频率、暂停分布和内存趋势推断应用负载模式（持续高压/偶尔峰值/空闲低负载/周期性波动/昼夜模式），声明置信度（高/中/低）。

### Step 4: Time Context & Startup Period Analysis

Phase 1 结束前必须做时间上下文检查，防止将启动期行为误判为稳态问题。

启动期定义：JVM 启动后前 3-5 分钟，或前 ~30 个 GC 事件（取较大者）。

检查：
1. 日志覆盖多长（分钟/小时/天）
2. 异常时间：使用 parser 的 `seconds_since_startup` 和 `in_startup_period`（若存在；uptime-only 日志可能缺失）
3. 对比 `startup_analysis` 中启动期与稳态的指标差异（字段可能缺失，取决于日志格式和详细程度）

判断与行动：
- **启动期异常** → 在 Report 中明确标注「启动期」。分析深度由 AI 自行判断。无论哪种情况，**调优建议优先级下调**。核心关注点是"该启动期机制是否会自恢复、是否会在稳态复现"
- **启动期和稳态都有** → 系统性问题。按全 severity 进入 Phase 2
- **仅在稳态出现** → 真正的调优/退化问题。进入 Phase 2，聚焦持续负载因素

## Phase 2: Deep Dive

For each anomaly flagged in Phase 1, perform a root-cause analysis.

### Step 1: Prioritize Anomalies

Sort by impact:
1. **零容忍异常**（Allocation stalls、Full GCs、To-space exhausted、Degenerated GC、Humongous allocation、Concurrent mark overflow）— application threads blocked or concurrent GC failed
2. **Long STW pauses** — tail latency impact
3. **Frequent GC** — throughput impact
4. **Memory pressure trends** — risk of future failures

**Startup-period adjustment**: If a long pause occurred within the first 5 minutes of JVM startup, downgrade its priority *for tuning recommendations* but **not** for root-cause explanation. The question shifts from "how do I tune GC?" to "what startup-phase mechanism caused this, and will it recur in steady state?"

### Step 2: Extract Complete Trace

获取每个异常事件的原始日志证据：

- **对于 parser 标记的零容忍异常**（`anomalies` 数组中的事件）：使用 `--anomalies --context-lines N` 直接获取附带上下文的输出
- **对于长停顿**：从 `top_pauses` 中找超过阈值的事件，用其 `line_number` 提取 `--window-start-line` / `--window-end-line`
- **对于 Full GC**：从 `full_gc_events` 中提取每个事件的上下文
- **对于 Mixed GC 低效**：从 `top_by_type` 的对应类型中找最长事件提取上下文
- **对于 Metaspace/GCLocker 频繁触发**：从 `top_by_cause` 的对应 cause 中提取上下文
- **对于频繁 GC**：从 `gc_cadence` 找 `gc_count` 突增的分钟窗口，按时间提取
- **对于堆泄漏**：`heap_samples` 提供趋势验证，通常不需要提取特定窗口（趋势是全局的）
- **对于 VM 操作开销**：从 `safepoint_events` 中提取高 `non_gc_pause_ms` 事件的上下文
- **对于晋升风暴**：从 `promotion_spikes` 中提取具体事件上下文
- 如需更宽范围：完整 GC 事件（G1 可能跨 10-50 行）+ 前后 2-3 个事件（趋势上下文）
- 记录精确的时间戳和行号范围

### Step 3: Phase Breakdown

按收集器拆解停顿，找出占主导地位的 phase 或环节。

**G1GC**（JDK 8 和 JDK 9+）：
- 检查 `g1_detail_phases`，找出平均耗时最长的 phase
- 常见瓶颈及诊断方向：
  - `Object Copy` 占比最高 → 存活对象量大，检查 `promotion` 和对象生命周期
  - `Ext Root Scanning` > 10ms → 线程数过多或 JNI/global reference 膨胀
  - `Update RS` > 10ms → 跨 region 引用更新频繁

**ZGC**：
- STW phases 在 `pause_by_type` 中：对比 Pause Mark End / Pause Relocate End / Pause Mark Start 的耗时分布
- 若 STW 低但 `metrics.cycle_avg_ms` 高 → 并发阶段是瓶颈（老年代对象图大）
- 检查 `metrics.allocation_stall_count`：分配停顿比 STW 更直接影响可用性

**Shenandoah**：
- STW phases 在 `pause_by_type` 中：对比 Init Mark / Final Mark / Init Update Refs / Final Update Refs
- 若 `anomaly_counts.degenerated_gc` > 0 → 并发失败，检查 `concurrent_cycles` 的耗时和模式
- `Final Mark` 占比过高 → 并发标记阶段未完成，老年代存活率过高

**Parallel / Serial**：
- 无 phase 分解。直接分析 `full_gc_events` 和 `top_pauses`
- 关注 `gc_causes` 中触发原因的分布

若 `full_gc_summary` 存在：
- Full GC 次数 > 0 时，无论停顿多长，**必须标记为 P0 问题**
- 对比 `full_gc_summary.avg_pause_ms` 与整体 `avg_pause_ms`，评估 Full GC 对总停顿的贡献
- 若 `full_gc_summary.total_freed_mb` 存在，评估 Full GC 的内存回收效率

### Step 3b: Collector-Specific Deep Dive

**ZGC**：
- 分配停顿分析：检查 `metrics.allocation_stall_count` 和 `allocation_stall_ms`
  - stall 次数 > 0 → P0 问题，优先增大堆
- 并发周期分析：检查 `metrics.cycle_*`（cycle_avg_ms / cycle_max_ms）
  - cycle 时间逐段增长 → 老年代对象图膨胀，检查是否有超大对象树
- MMU 检查：`metrics.mmu` 中各窗口的达标率

**Shenandoah**：
- 退化 GC 分析：检查 `anomaly_counts.degenerated_gc`
  - 任何非零值 → 并发失败，检查 `concurrent_cycles` 的耗时和模式
- STW phases 分布：从 `pause_by_type` 看 Init Mark / Final Mark / Update Refs 的比例
  - Final Mark 占比过高 → 并发标记阶段未完成，老年代存活率过高

### Step 4: Contextual Analysis

分析异常事件的上下文，判断它是孤立 spike 还是系统性问题的一部分。以下维度是常见分析角度，**不穷尽**——你应结合所有可用数据主动发现其他关联。

**时间维度**（数据来源：`timestamp`, `seconds_since_startup`, `gc_cadence`, `pause_intervals_ms`）：
- 是否发生在启动期？→ 查 `in_startup_period`
- 前后是否有同类事件密集发生？→ 查 `gc_cadence` 中该时间窗口的 `gc_count`
- 参考：前后 5 分钟内多次同类事件 → 倾向持续模式；孤立一次 → 倾向 spike

**堆状态维度**（数据来源：`heap_before_mb`, `heap_after_mb`, `heap_trigger_stats`, `heap_trend`）：
- GC 前堆是否接近满堆？→ 对比 `heap_before_mb` 与 `heap_trigger_stats` 的范围
- GC 后回收幅度是否正常？→ `heap_before_mb - heap_after_mb`，若 < 10% 则回收效率极低
- 是否发生在堆增长加速期？→ 对比事件时间与 `heap_samples` 的陡峭上升段

**前置并发周期（G1/ZGC/Shenandoah）**（数据来源：`concurrent_cycles`）：
- 事件前 30 秒内是否有并发周期结束？
- `concurrent_cycles.reset_for_overflow_count` > 0 → 标记与当前事件的潜在关联

**异常间因果关联**（数据来源：`anomalies`, `top_pauses`, `full_gc_events`）：
- `concurrent_mark_overflow` 后是否跟随 Full GC / 长 Mixed GC？（按时间戳关联）
- `to_space_exhausted` 后是否跟随 Full GC？
- 多个异常的时间是否集中？（同一分钟内多个异常 → 系统性压力）

**与 Phase 1 趋势的对齐**：
- Phase 1 识别的每个趋势（泄漏、频率升高、Mixed GC 低效等）应在 Phase 2 得到解释
- 如果某个异常无法解释 Phase 1 的趋势 → 可能遗漏了关联事件，或需要更宽的时间窗口

### Step 5: Root Cause & Recommendation — The Reasoning Chain

For each anomaly, build a **reasoning chain** that walks from the observed phenomenon to the root cause. Do NOT jump directly to conclusions. The audience knows Java but may not know GC internals — explain each step.

**Required structure for every root cause explanation:**

```
1. 现象（Observed Phenomenon）: 从数据中看到什么具体异常（单个事件的数值 / 一段时间的模式）
2. 机制（GC Mechanism）: 这个 GC phase/指标正常情况下做什么，什么因素会影响它的表现
3. 推导（Deduction）: 结合其他证据（日志片段 / 聚合指标），一步步推导出为什么会这样
4. 根因（Root Cause）: 最终的根因判断
5. 验证（Validation）: 这个根因是否能解释所有观察到的现象
```



## Report Template

ALWAYS output the final analysis using this structure:

```markdown
# GC 诊断报告：{一句话结论}

## 1. 执行摘要
- **GC 算法**：{类型}（JDK {版本推断}）
- **日志覆盖**：{时长}，共 {事件数} 个 GC 事件（启动期 {N} 个 / 稳定期 {M} 个）
- **整体健康度**：{优秀/良好/警告/严重}
- **关键健康观察**（即使是正常状态也列出，帮助读者快速建立整体认知）：
  - {如"老年代无压力，100% Young GC，无 Mixed/Full GC"}
  - {如"堆稳态稳定在 XGB/YGB，无泄漏迹象"}
  - {如"并发标记周期健康，无 overflow"}
- **负载特征**：{持续高压/偶尔峰值/空闲低负载/周期性波动}（置信度：{高/中/低}）
- **核心问题**：{1-2 句话概括最严重的发现}

### 1.1 问题总览（按严重程度排序）

**只包含 Phase 1 Step 2 标记的 anomaly**。健康评估的观察（如 GC efficiency、GC cause 分布）和正常指标，不要放入此表——它们在第 2 节（体检单）和第 4 节（趋势分析）中呈现。

| # | 问题 | 类型 | 严重程度 | 详见 | 根因方向 |
|---|------|------|---------|------|---------|
| 1 | {问题简述} | 异常事件/趋势/模式 | P0/P1/P2 | 第 3.X / 4.X 节 | {根因方向} |
| 2 | ... | ... | ... | ... | ... |

> **严重程度定义**：P0 = 影响可用性或 SLA，必须立即处理；P1 = 影响性能或存在明确恶化趋势，建议本周内处理；P2 = 潜在风险或预防性优化。

## 2. 关键指标（体检单）

只列最核心的指标，不做展开解读。解读放在第 4 节对应子节。

| 指标 | 值 | 评估 |
|------|-----|------|
| 吞吐量 | X% | {OK/警告/严重} |
| 最大 STW 停顿 | Xms | {OK/警告/严重} |
| **平均 STW 停顿** | Xms | {OK/警告/严重} |
| **中位数停顿** | Xms | {OK/警告/严重} |
| **P95 停顿** | Xms | {OK/警告/严重} |
| P99 停顿 | Xms | {OK/警告/严重} |
| GC 频率 | X 次/分钟 | {OK/警告/严重} |
| Full GC 次数 | X | {OK/警告/严重} |
| **暂停类型分布**（按 `pause_by_type`）| Mixed GC avg / Young GC avg = {ratio}x | {若 ratio > 2 为警告} |
| **晋升量**（G1GC，`promotion.avg`）| X MB/次 | {若 > Survivor 空间大小 为警告} |
| **VM 操作开销**（`vm_operations.total_ms`）| X ms（占总停顿 {X%}）| {若 > 10% 为警告} |
| **内存效率**（`memory_efficiency.avg_freed_per_gc_mb`）| X MB/次 | {若 < 10 MB 且频率 > 20/min 为警告} |
| **平均暂停间隔**（`pause_intervals_ms.avg`）| X ms | {若明显偏低（如 < 1s）或为警告；"持续下降"需多窗口对比验证} |
| **并发周期平均耗时**（`concurrent_cycles.avg_duration_ms`）| X ms | {若 > 2000ms 为警告} |

> **整体评估**：{一句话总结系统整体状态，如"老年代无压力，堆稳定，GC 效率极高，系统处于健康状态。唯一关注点是启动期 470ms 峰值。"}

## 3. 异常事件分析（详细病历）

每个异常事件独立分析。如果事件与第 1.1 节的问题总览中的某条对应，请在标题中标注编号。

### 事件 1 [#1]：{简短描述}
- **严重程度**：{P0/P1/P2}
- **时间**：{timestamp}（日志第 X 行，距启动 {T+Xm}）**【启动期 / 稳态】**
- **原始日志**：
  ```
  {2-5 行原始日志}
  ```
- **根因分析**：
  1. **现象**：{从日志中看到什么具体数据，如"Object Copy 占 pause 的 82%（412ms/502ms）"}
  2. **机制**：{这个 GC phase/指标正常情况下做什么，什么因素影响耗时}
  3. **推导**：{结合日志中的其他证据，一步步推导为什么会这样}
  4. **根因**：{最终判断}
  5. **验证**：{这个根因是否能解释所有观察到的现象——如果还有无法解释的数据，说明分析不完整}
- **影响**：{对应用的具体影响。如果是启动期事件，需明确说明这是启动期特有的行为，还是会在稳态复现的系统性问题}

### 事件 2：...

## 4. 趋势与模式分析（专科检查）

本节对第 2 节指标进行**解读和关联分析**。针对第 1.1 节中标注为"趋势/模式"类型的问题，回答"这个数据说明什么"和"与其他指标有什么关联"。

{根据问题总览中列出的趋势/模式问题，逐个组织子节。以下维度是常见分析角度，按需选择，不强制全部填写：}

### 4.1 {问题名称，如"启动期 GC 频率骤降模式"}
- **数据**：{相关指标的具体数值}
- **说明**：{这个数据说明什么——不要罗列，要解释}
- **关联**：{与其他指标的因果关系}

### 4.2 {问题名称，如"堆增长后稳定模式"}
...

{可选参考维度（按需选择）：}
- **GC 频率与停顿趋势**：`gc_cadence`、`pause_intervals_ms` —— 频率变化、间隔规律、孤立事件 vs 系统性问题
- **堆内存趋势**：`heap_trend`、`heap_samples`、`heap_trigger_stats` —— 泄漏风险、增长斜率、触发占用
- **并发周期健康度**：`concurrent_cycles` —— 周期时长、reset-for-overflow、与 STW 停顿的关联
- **暂停类型分布**：`pause_by_type` —— Mixed vs Young 占比、avg/max/p95 对比
- **VM 操作开销**：`vm_operations`、`safepoint_events` —— 非 GC safepoint 的频率与幅度
- **GC 效率**：`gc_efficiency` —— thrashing 判断、Full GC vs 普通 GC 效率对比
- **GC 触发原因分布**：`gc_causes` —— 原因占比、与暂停的关联
- **Full GC 专项**：`full_gc_summary` —— 任何 Full GC 都是 P0
- **晋升与内存效率**：`promotion`、`memory_efficiency` —— 晋升量、回收效率、暂停间隔四者关联

## 5. 优化建议（按优先级排序）

每条建议必须**引用前面的具体证据**，并给出**预期效果**和**验证方法**。

### 5.1 {高优先级}：{建议标题}
- **对应问题**：第 1.1 节 #X — {问题简述}
- **证据**：{引用具体指标和数值，如"基于 4.4 中 pause_by_type 数据，Mixed GC 平均 380ms，占总暂停 30%"}
- **根因**：{一句话解释为什么这个建议能解决该问题}
- **具体建议**：{参数调整或架构修改}
- **预期效果**：{量化预期，如"Mixed GC 平均耗时降至 Young GC 的 2 倍以内"}
- **验证方法**：{如何确认建议生效，如"观察后续日志中 Mixed GC p95 是否 < 200ms"}

### 5.2 {中优先级}：{建议标题}
- **对应问题**：第 1.1 节 #X
- **证据**：...
- **根因**：...
- **具体建议**：...
- **预期效果**：...
- **验证方法**：...

### 5.3 {低优先级或预防性}：{建议标题}
- **对应问题**：...
- **证据**：...
- **根因**：...
- **具体建议**：...
- **预期效果**：...
- **验证方法**：...
```

## Critical Reminders

1. **Never skip Phase 1.**
2. **Cite evidence for every claim.** 包含时间戳、行号和具体数值。
3. **Explain the why.** 不要只给结论，解释背后的 GC 机制。
4. **Distinguish correlation from causation.**
5. **Be honest about uncertainty.** 信息不足时明确说明，并指出需要什么额外数据。
6. **Always check startup period first.** 用 parser 的 `startup_analysis` 和 `seconds_since_startup` 验证异常是否发生在启动期。
