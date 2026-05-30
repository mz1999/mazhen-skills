---
name: gc-log-analyzer
description: |
  Analyze Java GC logs to diagnose performance issues, identify abnormal GC events, and provide tuning recommendations. Trigger when the user explicitly asks to analyze a GC log file, or mentions "GC log", "garbage collection analysis", or "analyze gc.log".
---

# GC Log Analyzer

Analyze Java GC logs to diagnose performance issues, identify abnormal GC events, and provide actionable tuning recommendations.

## Audience

Experienced Java engineers who understand Java but may not be deeply familiar with GC internals. Explanations should be accessible — connect GC behavior to application-level symptoms (latency spikes, throughput drops) and explain the "why" behind each observation.

## Core Principles

1. **Two-phase analysis**: A global scan first builds the system-wide GC pressure profile, preventing cherry-picked conclusions. Contextless deep dives on individual events often misinterpret startup spikes or isolated outliers as systemic problems.
2. **Evidence-based conclusions**: Every anomaly claim must cite the original log snippet (2-5 lines, with timestamps). Include line numbers or time ranges so the user can verify.
3. **Principle over prescription**: Provide analysis direction and judgment logic. Reference values and thresholds are guidelines, not absolutes — they depend on workload characteristics and SLAs.
4. **Connect to application symptoms**: Always explain what the GC pattern means for the running application (e.g., "this 200ms STW pause directly causes tail latency spikes in your API responses").
5. **Startup behavior ≠ steady-state problems**: Anomalies during the startup period (first 3-5 minutes or ~30 GC events) are usually self-recovering. Flag them with a【启动期】label, but do not treat them with the same tuning urgency as steady-state issues unless they also appear post-startup.

## Input Handling

### File Size Strategy

GC logs can be very large (hundreds of MB to GBs). Reading the entire file into context wastes tokens and risks truncation. Use the parser script for large files.

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

Build a system-wide GC pressure profile. Skipping the global scan makes it impossible to distinguish isolated spikes from systemic problems.

### Step 1: Extract Key Metrics

读取 parser 输出的完整 summary JSON。**所有字段的精确语义、计算方式和出现条件见 `references/parser_output.md`**——在开始分析前，先快速浏览该文件建立对输出结构的认知。

重点关注以下维度：

**核心指标（所有收集器通用）**：
- 停顿分布：`metrics.max_pause_ms` / `min_pause_ms` / `avg_pause_ms` / `p50_pause_ms` / `p95_pause_ms` / `p99_pause_ms`
- 吞吐：`metrics.throughput_percent`
- 频率：`metrics.gc_frequency_per_minute`
- 总量：`metrics.total_gc_events` / `metrics.total_pause_ms` / `metrics.full_gc_count`
- 零容忍异常：`anomaly_counts` / `anomalies`

**按收集器重点关注的维度**：
- **G1**：`pause_by_type`、`concurrent_cycles`、`g1_detail_phases`、`promotion`、`heap_trigger_stats`
- **ZGC**：`metrics.allocation_stall_count` / `allocation_stall_ms`、`metrics.cycle_*`、`metrics.mmu`
- **Shenandoah**：`anomaly_counts.degenerated_gc`、`concurrent_cycles`

**通用分析维度（按需提取）**：
- 堆趋势：`heap_trend`
- 触发原因：`gc_causes`
- VM 开销：`vm_operations`
- 内存效率：`memory_efficiency` / `gc_efficiency`
- 启动期：`startup_analysis`
- 近期样本：`recent_events_sample`
- 间隔规律：`pause_intervals_ms`

**Phase 2 定位坐标（用于提取具体事件上下文）**：
- 最长停顿：`top_pauses`
- Full GC 清单：`full_gc_events`
- 按类型 Top：`top_by_type`
- 按原因 Top：`top_by_cause`
- GC 节奏：`gc_cadence`
- 堆采样：`heap_samples`
- Safepoint 事件：`safepoint_events`
- 晋升风暴：`promotion_spikes`

### Step 2: Flag Anomaly Events

基于 Step 1 提取的指标标记异常。开始前先理解 parser 的异常检测边界：

**parser 的 `anomalies` 数组只包含"零容忍型异常"**——任何一次出现即代表 JVM 行为超出正常设计范围的事件（如 Full GC、allocation stall、evacuation failure 等）。parser 不做阈值判断，不做频率统计。完整类型列表见 `references/parser_output.md`。

**以下异常类型 parser 不标记，需要你从 Step 1 的指标中自行判断**：
- 长停顿、频繁 GC、VM 操作开销、堆泄漏、Metaspace 不足、Mixed GC 低效、晋升过快等
- 以上列表不穷尽。结合所有聚合数据主动发现其他模式，例如停顿时间的双峰分布、GC 频率的突然跳变、堆占用的周期性波动、并发周期的持续延长

**重要**：如果 `anomalies` 数组为空，不代表系统健康。必须从 `metrics`、`pause_by_type`、`heap_trend`、`gc_causes`、`pause_intervals_ms`、`concurrent_cycles` 等聚合数据中做完整分析。

根据应用 SLA 调整阈值，标记以下异常：

- **零容忍（任何出现即异常）**：Full GC、To-space exhausted、Allocation stall、Humongous allocation、Degenerated GC、Concurrent mark overflow
- **超过算法典型阈值**：G1 STW > 200ms、ZGC/Shenandoah STW > 1ms、Young GC 频率 > 20/分钟
- **结合 `heap_trend` 判断**：堆斜率显著为正且 R² > 0.7、Full GC 后堆仍持续增长

> **注意**：启动期（前 3-5 分钟）出现的异常同样要标记，不要在 Step 2 中过滤掉。如果 parser 已提供 `in_startup_period`，将该标识作为异常属性一并记录（Report 中标注【启动期】）。若 `in_startup_period` 缺失，可从 `recent_events_sample` 前几个事件的时间戳或 `gc_cadence` 最初几分钟的频率推断。
>
> 特别地，**启动期高频 GC（>20/分钟）要标记**——虽然这是常见的启动期行为，但不要预先判断"这是正常的所以跳过"。标记即可，AI 自行判断分析深度。

### Step 2b: Heap Trend & Leak Risk Assessment

读取 `heap_trend`（需 `numpy`/`scipy`，否则跳过）：

- `leak_risk` 为 medium/high → 标记异常；`estimated_hours_to_oom` < 24h → 紧急
- `post_full_gc_slope_kbps > 0` → Full GC 后堆仍在增长，结合老年代趋势判断
- **注意**：`confidence: low` 时（样本不足，通常 < 10 个 GC 事件；或缺少 `numpy`/`scipy`），不输出泄漏风险判断

### Step 2c: VM Operations & Pause Interval Check

- `vm_operations.max_ms` > 200ms
- `vm_operations.total_ms` / `estimated_runtime_ms` > 1%
- `pause_intervals_ms.min` < 100ms
- `pause_intervals_ms.p95` / `avg` > 3x
- `pause_intervals_ms.avg` 明显偏低（如 < 1 秒）。判断"持续下降"需手动切分时间窗口对比，parser 单次输出不提供趋势序列

### Step 3: Health Overview

Summarize in 3-5 bullet points:
- Overall GC pressure level (Low / Moderate / High / Critical)
- Whether the system is meeting its pause-time goals
- The most significant anomaly category
- Time windows where problems concentrate

### Step 3a: GC Efficiency Check

读取 `gc_efficiency`，作为健康评估的参考维度：

- `avg_performance_mbps < 0.1`
- `full_gc_performance_mbps` >> `regular_gc_performance_mbps`
- `freed_mem_per_minute` 低但 `gc_frequency_per_minute` > 20

### Step 3b: GC Cause Distribution Check

读取 `gc_causes`，分析触发原因分布：

- 高频原因及其 `avg_pause_ms` 与整体平均的对比
- 启动期 vs 稳态的原因分布差异

#### 负载模式推断（必须包含在执行摘要中）

根据 GC 频率、暂停分布和内存趋势推断应用负载模式（持续高压/偶尔峰值/空闲低负载/周期性波动/昼夜模式），声明置信度（高/中/低）。

## Phase 2: Deep Dive

For each anomaly flagged in Phase 1, perform a root-cause analysis.

### Step 1: Prioritize Anomalies

Sort by impact:
1. **零容忍异常**（Allocation stalls、Full GCs、To-space exhausted、Degenerated GC、Humongous allocation、Concurrent mark overflow）
2. **Long STW pauses**
3. **Frequent GC**
4. **Memory pressure trends**

**Startup-period adjustment**: If a long pause occurred within the first 5 minutes of JVM startup, downgrade its priority *for tuning recommendations* but **not** for root-cause explanation. The question shifts from "how do I tune GC?" to "what startup-phase mechanism caused this, and will it recur in steady state?"

### Step 2: Extract Complete Trace

获取每个异常事件的原始日志证据。每个异常在 summary 中都有坐标（行号或时间戳），不要只盯着单个事件——必须同时看"前因"和"后果"。

- parser 标记的 `anomalies` → 使用 `--anomalies --context-lines N` 直接获取附带上下文的输出
- 其他异常 → 从 summary 中找到行号或时间戳，使用 `--window-start-line` / `--window-end-line` 或 `--window-start` / `--window-end` 提取

提取范围 AI 自行判断：
- **往前回溯**：看问题是怎么累积的。例如，一个长 Young GC 往前看几个同类型 GC，对比 Eden 占用、晋升量、回收幅度的变化，才能判断是突增还是持续恶化。
- **往后观察**：看事件后系统是恢复、反复还是恶化。例如，Full GC 后观察接下来几分钟的 GC 模式，判断堆是否真正释放了压力。

记录精确的时间戳和行号范围。

### Step 3: Phase Breakdown

按收集器拆解停顿，找出占主导地位的 phase 或环节。

**G1GC**（JDK 8 和 JDK 9+）：
- 检查 `g1_detail_phases`，找出平均耗时最长的 phase

**ZGC**：
- STW phases 在 `pause_by_type` 中，对比各 phase 耗时分布
- 结合 `metrics.cycle_*` 分析并发阶段健康度
- `metrics.allocation_stall_count` 和 `allocation_stall_ms`
- `metrics.mmu` 中各窗口达标率

**Shenandoah**：
- STW phases 在 `pause_by_type` 中，对比各 phase 耗时分布
- `anomaly_counts.degenerated_gc` 和 `concurrent_cycles`

**Parallel / Serial**：
- 无 phase 分解。直接分析 `full_gc_events` 和 `top_pauses`
- 关注 `gc_causes` 中触发原因的分布

若 `full_gc_summary` 存在：
- Full GC 次数 > 0 时，无论停顿多长，**必须标记为 P0 问题**
- 对比 `full_gc_summary.avg_pause_ms` 与整体 `avg_pause_ms`，评估 Full GC 对总停顿的贡献
- 若 `full_gc_summary.total_freed_mb` 存在，评估 Full GC 的内存回收效率

### Step 4: Contextual Analysis

分析异常事件的上下文，判断它是孤立 spike 还是系统性问题的一部分。以下维度是常见分析角度，**不穷尽**——你应结合所有可用数据主动发现其他关联。

**时间维度**（数据来源：`timestamp`, `seconds_since_startup`, `gc_cadence`, `pause_intervals_ms`）：
- 是否发生在启动期？→ 查 `in_startup_period`
- 前后是否有同类事件密集发生？→ 查 `gc_cadence` 中该时间窗口的 `gc_count`

**堆状态维度**（数据来源：`heap_before_mb`, `heap_after_mb`, `heap_trigger_stats`, `heap_trend`）：
- GC 前堆是否接近满堆？→ 对比 `heap_before_mb` 与 `heap_trigger_stats` 的范围
- GC 后回收幅度是否正常？→ 对比 `heap_before_mb` 与 `heap_after_mb` 的差值
- 是否发生在堆增长加速期？→ 对比事件时间与 `heap_samples` 的陡峭上升段

**前序事件累积分析**：
- 分配压力趋势：事件前几个同类型 GC 的 `eden_before_mb` 是稳定还是逐次递增
- 老年代压力趋势：`promotion`（如有）或连续 Young GC 后 `heap_after_mb` 的增量是突增还是持续累积
- 恶化趋势：同类型 GC 的 `pause_ms` 是否在持续拉长

**后序事件恢复分析**：
- 停顿是否回归基线？→ 后续同类型 GC 的 `pause_ms` 是否回到平均水平
- 是否反复触发？→ 短期内是否出现第二次同类异常
- 堆是否恢复稳态？→ `heap_after_mb` 是否回到正常范围，还是持续高位

**前置并发周期**：
- 事件前 30 秒内是否有并发周期结束？
- `concurrent_cycles.reset_for_overflow_count` > 0 → 标记与当前事件的潜在关联

**异常间因果关联**：
- 检查异常事件之间的时间邻近性和潜在因果关系（按时间戳关联）
- 多个异常的时间是否集中？

**与 Phase 1 趋势的对齐**：
- Phase 1 识别的每个趋势应在 Phase 2 得到解释
- 如果某个异常无法解释 Phase 1 的趋势 → 可能遗漏了关联事件，或需要更宽的时间窗口

### Step 5: Root Cause & Recommendation — The Reasoning Chain

For each anomaly, build a **reasoning chain** that walks from the observed phenomenon to the root cause. Jumping straight to conclusions skips the validation step and often produces plausible-sounding but incorrect root causes. The audience knows Java but may not know GC internals — explaining the mechanism builds trust and helps them verify your logic.

**Required structure for every root cause explanation:**

```
1. 现象（Observed Phenomenon）: 从数据中看到什么具体异常（单个事件的数值 / 一段时间的模式）
2. 机制（GC Mechanism）: 这个 GC phase/指标正常情况下做什么，什么因素会影响它的表现
3. 推导（Deduction）: 结合其他证据（日志片段 / 聚合指标），一步步推导出为什么会这样
4. 根因（Root Cause）: 最终的根因判断
5. 验证（Validation）: 这个根因是否能解释所有观察到的现象
```



## Report Structure

Every GC analysis produces **both** a markdown report and a self-contained HTML report. The markdown report is the primary analytical artifact; the HTML report is a visual, shareable companion with the same analytical depth plus inline SVG charts.

### Delivery Checklist

Before finishing any GC analysis, confirm both deliverables are complete:

- [ ] **Markdown report** — save to `{gc_log_dir}/gc_report.md`; also output the complete markdown content directly in your final response so the user can read it inline
- [ ] **Self-contained HTML report** — save to `{gc_log_dir}/gc_report.html`, inline all CSS and SVG charts, zero external dependencies

> Both deliverables are required regardless of whether the log appears healthy. Do not skip the HTML report for "simple" or "healthy" cases.
> `{gc_log_dir}` is the directory containing the analyzed GC log file. Extract it from the log file path and create the directory if it does not exist (`mkdir -p`).

### Markdown Report

Use this as a **framework**, not a rigid template. Skip sections that have no meaningful content. The goal is to communicate findings efficiently — a healthy log should still include all sections, but each can be brief.

```markdown
# GC 诊断报告：{一句话结论}

## 1. 执行摘要
- **GC 算法**：{类型}（JDK {版本推断}）
- **日志覆盖**：{时长}，共 {事件数} 个 GC 事件（启动期 {N} 个 / 稳定期 {M} 个）
- **整体健康度**：{优秀/良好/警告/严重}
- **关键健康观察**：
  - {2-3 条帮助读者建立整体认知的观察}
- **负载特征**：{...}（置信度：{高/中/低}）
- **核心问题**：{1-2 句话概括最严重的发现}

### 1.1 问题总览（按严重程度排序）

| # | 问题 | 类型 | 严重程度 | 详见 | 根因方向 |
|---|------|------|---------|------|---------|
| 1 | {问题简述} | 异常事件/趋势/模式 | P0/P1/P2 | 第 3.X / 4.X 节 | {根因方向} |

> **严重程度定义**：P0 = 影响可用性或 SLA，必须立即处理；P1 = 影响性能或存在明确恶化趋势，建议本周内处理；P2 = 潜在风险或预防性优化。

## 2. 关键指标（体检单）

只列最核心的指标，不做展开解读。解读放在第 4 节对应子节。

| 指标 | 值 | 评估 |
|------|-----|------|
| 吞吐量 | X% | {OK/警告/严重} |
| 最大 STW 停顿 | Xms | {OK/警告/严重} |
| 平均 STW 停顿 | Xms | {OK/警告/严重} |
| 中位数停顿 | Xms | {OK/警告/严重} |
| P95 停顿 | Xms | {OK/警告/严重} |
| GC 频率 | X 次/分钟 | {OK/警告/严重} |
| Full GC 次数 | X | {OK/警告/严重} |
| {按收集器选择 2-4 个额外指标} | ... | ... |

> **整体评估**：{一句话总结}

## 3. 异常事件分析（详细病历）

**P0 异常**：每个单独分析，使用完整的 5 步推理链（现象 → 机制 → 推导 → 根因 → 验证）。

**P1/P2 异常**：可单独分析，也可将**同类、同根因、同时间窗口**的异常合并分析。例如：3 个 Full GC 集中在同一分钟内 → 合并为一个分析条目，归纳共同模式。

### 事件 1 [#1]：{简短描述}
- **严重程度**：{P0/P1/P2}
- **时间**：{timestamp}（日志第 X 行，距启动 {T+Xm}）**【启动期 / 稳态】**
- **原始日志**：
  ```
  {2-5 行原始日志}
  ```
- **根因分析**：
  1. **现象**：{从数据中看到什么}
  2. **机制**：{这个 phase/指标正常做什么，什么因素影响它}
  3. **推导**：{结合证据一步步推导}
  4. **根因**：{最终判断}
  5. **验证**：{根因是否解释所有观察到的现象}
- **影响**：{对应用的具体影响。启动期事件需说明是否会稳态复现}

### 事件 2：{或"事件 2-4：同类异常合并分析"}
...

## 4. 趋势与模式分析（专科检查）

本节对第 2 节指标进行**解读和关联分析**。针对第 1.1 节中标注为"趋势/模式"类型的问题，回答"这个数据说明什么"和"与其他指标有什么关联"。

**按需选择子节**，不要为没有问题的维度硬写分析。

### 4.1 {问题名称}
- **数据**：{相关指标的具体数值}
- **说明**：{这个数据说明什么——不要罗列，要解释}
- **关联**：{与其他指标的因果关系}

{可选参考维度（按需选择，不强制全部）：}
- **GC 频率与停顿趋势**：`gc_cadence`、`pause_intervals_ms`
- **堆内存趋势**：`heap_trend`、`heap_samples`、`heap_trigger_stats`
- **并发周期健康度**：`concurrent_cycles`
- **暂停类型分布**：`pause_by_type`
- **VM 操作开销**：`vm_operations`、`safepoint_events`
- **GC 效率**：`gc_efficiency`
- **GC 触发原因分布**：`gc_causes`
- **Full GC 专项**：`full_gc_summary`
- **晋升与内存效率**：`promotion`、`memory_efficiency`

## 5. 优化建议（按优先级排序）

每条建议**引用前面的具体证据**，给出**预期效果**和**验证方法**。次要建议可简写。

### 5.1 {高优先级}：{建议标题}
- **对应问题**：第 1.1 节 #X — {问题简述}
- **证据**：{引用具体指标和数值}
- **根因**：{一句话解释为什么这个建议能解决问题}
- **具体建议**：{参数调整或架构修改}
- **预期效果**：{量化预期}
- **验证方法**：{如何确认生效}

### 5.2 {中/低优先级}：{建议标题}
- {关键字段保留，次要字段可简写}
```

### HTML Report

After completing the markdown analysis, generate a single-file HTML report and save it to `{gc_log_dir}/gc_report.html` (same directory as the analyzed GC log).

**1. Get chart assets**

```bash
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
import html_report
summary = json.load(open('summary.json'))
assets = html_report.generate_chart_assets(summary)
print(json.dumps(assets))
"
```

Assets returned:

| Key | Content | Data Source |
|-----|---------|-------------|
| `heap_trend_svg` | Area + line chart SVG | `heap_samples` |
| `gc_cadence_svg` | Bar + dashed line dual-axis SVG | `gc_cadence.windows` |
| `pause_scatter_svg` | Scatter plot, log Y-axis SVG | `top_pauses` |
| `pause_by_type_svg` | Horizontal bar chart SVG | `pause_by_type` |
| `gc_causes_svg` | Doughnut chart SVG | `gc_causes` |
| `startup_timeline_svg` | Timeline bar chart SVG | `anomalies` |
| `metrics_grid_html` | Metrics grid HTML | `metrics` |
| `anomaly_table_html` | Anomaly table HTML | `anomalies` |

**2. Design reference**

Read `references/visual-design-system.md` for CSS tokens, typography, layout patterns, and components. Inline all CSS in a `<style>` tag. Zero external dependencies (no CDN, no frameworks).

**3. Layout principles**

- **Content type**: Report → stacked `.panel` sections
- **Components**: `.panel`, `.data-table`, `.banner`, `.chip`, `.metrics-grid`, `.layout-split` (for side-by-side charts)
- **Chart containers**: wrap each SVG in `.chart-wrap` with `overflow-x: auto`

**4. Structural outline** (framework, not rigid template)

- Header (eyebrow + `.t-display` title + subtitle)
- Metrics grid + key finding banner
- Charts: heap trend → GC cadence → pause scatter → (pause by type + GC causes side-by-side) → startup timeline
- Anomaly detail table
- Analysis sections (executive summary, deep dive, trends, recommendations) rendered from markdown content
- Footer

**5. Content conversion from markdown to HTML**

- Subsection headings → `<h3 class="t-h3">`
- Paragraphs → `<p class="t-body">`
- Log snippets → `<pre class="code-block"><code>`
- Bullet lists → `<ul>` / `<li>`
- Reasoning chains → `<ol>` with `<li><strong>现象</strong>: ...</li>` format

## Critical Reminders

1. **Phase 1 is the foundation.** Skipping the global scan makes it impossible to distinguish isolated spikes from systemic problems, and often leads to over-tuning the wrong thing.
2. **Cite evidence for every claim.** 包含时间戳、行号和具体数值。
3. **Explain the why.** 不要只给结论，解释背后的 GC 机制。
4. **Distinguish correlation from causation.**
5. **Be honest about uncertainty.** 信息不足时明确说明，并指出需要什么额外数据。
6. **HTML report is mandatory.** Both markdown and HTML reports are required deliverables for every analysis, regardless of log health.
7. **Markdown report must be displayed inline.** Always output the complete markdown report content directly in your final response, not just a file path reference.
