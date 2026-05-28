# GC Log Parser Output Reference

准确说明 `gc_log_parser.py --summary` 输出的每个字段的语义、计算方式和出现条件。

---

## 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | string | 输入文件路径 |
| `line_count` | int | 日志总行数 |
| `detected_format` | string | `"jdk8_legacy"` / `"jdk9_unified"` / `"unknown"` |
| `detected_collector` | string | `"G1GC"` / `"ZGC"` / `"Shenandoah"` / `"Parallel"` / `"Serial"` / `"CMS"` / `"unknown"` |
| `metrics` | object | 收集器特定的核心指标（见下方） |
| `anomaly_counts` | object | 零容忍型异常类型出现次数的映射，如 `{"full_gc": 2, "concurrent_mark_overflow": 1}`。阈值判断和频率统计类异常不在此列。 |
| `anomalies` | array | 异常事件列表，最多 100 条 |
| `anomaly_count` | int | 异常总数 |
| `startup_analysis` | object? | 启动期 vs 稳态分析（仅 JDK 8 G1 日志且数据充足时出现） |
| `recent_events_sample` | array | 最近 10 个 GC 事件样本 |
| `concurrent_cycles` | object? | 并发 GC 周期统计（仅当日志包含并发阶段时出现） |
| `heap_trend` | object? | 堆趋势回归分析（只要有堆数据点即出现；需 `numpy`/`scipy` 才能完成回归，否则 `confidence: low`） |
| `g1_detail_phases` | object? | G1 详细阶段平均耗时映射（JDK 8 或 JDK 9+ G1 有详细日志时出现） |
| `pause_by_type` | object? | 按事件类型分组的停顿统计（有 pause_ms > 0 的事件时出现） |
| `vm_operations` | object? | 非 GC safepoint 停顿统计（有 safepoint 日志且存在非 GC 停顿时出现） |
| `memory_efficiency` | object? | 内存回收效率（有 heap_before/after 数据时出现） |
| `promotion` | object? | 对象晋升统计（需 Eden/Survivor/Heap 全量数据，仅 JDK 8 G1 PrintGCDetails 时出现） |
| `pause_intervals_ms` | object? | STW 事件间隔统计（至少 2 个带时间戳的 STW 事件时出现） |
| `gc_efficiency` | object? | GC 效率指标（`memory_efficiency` 存在且 `total_pause_ms > 0` 时出现） |
| `gc_causes` | object? | 按触发原因分组的 GC 统计（事件含 `gc_cause` 时出现） |
| `full_gc_summary` | object? | Full GC 专项汇总（`full_gc_count > 0` 时出现） |
| `heap_trigger_stats` | object? | GC 触发时堆占用比例近似值（>=5 个事件含 `heap_before_mb` 时出现） |
| `top_pauses` | array? | 前 20 个最长 STW 停顿（含行号坐标） |
| `full_gc_events` | array? | 全部 Full GC 事件列表（含行号坐标） |
| `top_by_type` | object? | 按 GC 类型分组的前 10 个事件 |
| `top_by_cause` | object? | 按 GC 触发原因分组的前 10 个事件 |
| `gc_cadence` | object? | 每分钟 GC 次数时间序列 |
| `heap_samples` | array? | 堆占用均匀采样序列（最多 20 个点） |
| `safepoint_events` | array? | 非 GC safepoint 事件列表（最多 20 个） |
| `promotion_spikes` | array? | 按晋升量排序的前 10 个事件 |

---

## metrics — 标准收集器（G1GC / Parallel / Serial / Shenandoah）

由 `_build_standard_metrics()` 生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_gc_events` | int | STW 停顿事件总数（不含并发阶段） |
| `total_pause_ms` | float | 所有 STW 停顿时间之和 |
| `max_pause_ms` | float | 最大单次 STW 停顿 |
| `min_pause_ms` | float | 最小单次 STW 停顿 |
| `avg_pause_ms` | float | 平均 STW 停顿 |
| `p50_pause_ms` | float | STW 停顿 P50 |
| `p95_pause_ms` | float | STW 停顿 P95 |
| `p99_pause_ms` | float? | STW 停顿 P99（样本 >=100 时出现） |
| `p99_note` | string? | 样本 <100 时出现，提示使用 P95 |
| `p995_pause_ms` | float? | STW 停顿 P99.5（样本 >=200 时出现） |
| `p995_note` | string? | 样本 <200 时出现，提示使用 P99 |
| `p999_pause_ms` | float? | STW 停顿 P99.9（样本 >=500 时出现） |
| `p999_note` | string? | 样本 <500 时出现，提示使用 P99.5 |
| `full_gc_count` | int | Full GC 事件数 |
| `throughput_percent` | float | `100 - (total_pause_ms / runtime_ms * 100)`，应用线程运行时间占比 |
| `gc_frequency_per_minute` | float? | 每分钟 GC 次数（能估算运行时间时出现） |
| `runtime_is_estimated` | bool | `estimated_runtime_ms` 是否为启发式估算 |
| `estimated_runtime_ms` | float | 估算的总运行时间（毫秒） |

---

## metrics — ZGC 特有

由 `_build_zgc_metrics()` 生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `stw_pause_count` | int | STW 子停顿数（Mark Start / Mark End / Relocate Start / Relocate End 等） |
| `stw_max_ms` / `stw_min_ms` / `stw_avg_ms` / `stw_p50_ms` / `stw_p95_ms` / `stw_p99_ms` | float | STW 停顿统计 |
| `stw_p99_note` | string? | 样本 <100 时出现 |
| `stw_p995_ms` | float? | STW 停顿 P99.5（样本 >=200 时出现） |
| `stw_p995_note` | string? | 样本 <200 时出现 |
| `stw_p999_ms` | float? | STW 停顿 P99.9（样本 >=500 时出现） |
| `stw_p999_note` | string? | 样本 <500 时出现 |
| `allocation_stall_count` | int | 分配停顿次数（从异常或 stats 中提取） |
| `allocation_stall_ms` | float | 分配停顿总时间 |
| `mmu` | object | MMU 统计，键为时间窗口(ms)，值为百分比，如 `{"5": 99.9, "10": 99.99}` |
| `cycle_count` | int | ZGC Major/Minor Collection 周期数 |
| `cycle_max_ms` / `cycle_min_ms` / `cycle_avg_ms` / `cycle_p95_ms` / `cycle_p99_ms` | float | 完整 GC 周期时间统计（含并发阶段） |
| `cycle_p995_ms` | float? | 周期时间 P99.5（cycle_n >= 200 时出现） |
| `cycle_p999_ms` | float? | 周期时间 P99.9（cycle_n >= 500 时出现） |
| `gc_frequency_per_minute` | float? | 每分钟 GC 周期数 |

**注意**：`cycle_*` 是完整 GC 周期（`ZGC Collection (total)`），包含并发阶段；`stw_*` 仅统计 STW 子停顿。

---

## startup_analysis

由 `_build_startup_analysis()` 生成。仅当 JDK 8 G1 日志有 datetime 时间戳且事件数充足时出现。

启动期定义：前 5 分钟或前 30 个事件（取先满足者）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `startup_event_count` | int | 启动期事件数 |
| `steady_event_count` | int | 稳态事件数 |
| `log_duration_minutes` | float? | 日志覆盖的总时长（分钟） |
| `cpu_utilization.startup_avg` / `steady_avg` / `diff` | float? | GC 线程 CPU 利用率（从 `[Times: user=X sys=Y, real=Z]` 计算） |
| `worker_start_diff_ms.startup_avg` / `steady_avg` / `diff` | float? | GC Worker 启动时间差异（ms） |
| `object_copy_ms.startup_avg` / `steady_avg` | float? | Object Copy 阶段平均耗时 |
| `eden_before_std_mb.startup` / `steady` / `diff` | float? | Eden 区 GC 前大小的标准差 |
| `safepoint_summary.total_safepoints` | int | 总 safepoint 数 |
| `safepoint_summary.non_gc_count` | int | 非 GC safepoint 数量（`non_gc_pause_sec > 0`） |
| `safepoint_summary.max_non_gc_pause_ms` | float | 最大非 GC safepoint 停顿（ms） |

---

## concurrent_cycles

由 `_build_summary()` 中内联代码生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | int | 并发周期总数 |
| `algorithm` | string | `"G1"` / `"ZGC"` / `"Shenandoah"` |
| `avg_duration_ms` | float? | 平均周期时长 |
| `max_duration_ms` | float? | 最大周期时长 |
| `reset_for_overflow_count` | int | G1 concurrent-mark-reset-for-overflow 次数 |

**数据来源**：
- G1：`concurrent-mark-start` → `concurrent-mark-end` 的时间差
- ZGC：`Concurrent Mark` / `Concurrent Relocate` 等行的时长
- Shenandoah：类似 ZGC

---

## heap_trend

由 `HeapTrendAnalyzer.regression_analysis()` 生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `heap_slope_kbps` | float | 堆内存增长斜率（KB/s），基于所有 GC 后堆大小做线性回归 |
| `r_squared` | float | 回归 R² |
| `p_value` | float | 回归 p 值 |
| `trend` | string | `"growing"` / `"shrinking"` / `"stable"`（斜率阈值 ±0.1 KB/s） |
| `leak_risk` | string | `"high"` / `"medium"` / `"low"` / `"none"` |
| `samples` | int | 回归样本数 |
| `estimated_hours_to_oom` | float? | 按当前增长速率到达 max_heap 的预计时间（小时），仅 slope > 0 时 |
| `post_full_gc_slope_kbps` | float? | 仅对 Full GC 后的堆大小做回归的斜率（>=5 个 Full GC 点时） |
| `full_gc_effectiveness` | string? | `"good"` / `"fair"` / `"poor"`，基于 post_full_gc_slope（>0.5 poor, >0.1 fair） |
| `confidence` | string? | `"low"`，样本 <10 或缺少 numpy/scipy 时出现 |
| `note` | string? | 缺少 numpy/scipy 时的安装提示 |

**泄漏风险规则**：
- high：`slope > 1.0 KB/s` 且 `r² > 0.7`
- medium：`slope > 0.5 KB/s` 且 `r² > 0.5`
- low：`slope > 0.1 KB/s`
- none：其他

**max_heap 估算**：优先使用检测到的最大堆容量，回退到 `max(heap_after) * 1.5`。

---

## g1_detail_phases

由 `_build_summary()` 中内联代码生成。支持 JDK 8 和 JDK 9+ G1 日志。

- **JDK 8**：从多行 G1 日志的 `[Times:` 和 phase 行解析
- **JDK 9+**：从 `[gc,phases]` 行解析，按 `gc_id` 关联后聚合

格式：`{"Object Copy": 45.234, "Ext Root Scanning": 2.123, ...}`

键为阶段名称（如 `"Object Copy"`、`"Ext Root Scanning"`、`"Update RS"` 等），值为该阶段在所有事件中的平均耗时（ms）。

---

## pause_by_type

由 `_build_pause_by_type()` 生成。

格式：`{"G1 Evacuation Pause (young)": {...}, "Full GC": {...}}`

每个类型的统计对象：

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | int | 该类型事件数 |
| `min_ms` / `max_ms` / `avg_ms` / `median_ms` / `p95_ms` | float | 该类型停顿统计 |
| `p995_ms` | float? | P99.5（该类型样本 >= 200 时出现） |
| `p999_ms` | float? | P99.9（该类型样本 >= 500 时出现） |
| `sum_ms` | float | 该类型总停顿时间 |
| `sum_percent` | float | 该类型总停顿占 `total_pause_ms` 的百分比 |

**注意**：
- 仅统计 `pause_ms > 0` 的事件
- ZGC `Collection (total)` 事件被排除（它是完整周期时长，不是单个 STW 停顿）
- 按 `sum_ms` 降序排列

---

## vm_operations

由 `_build_vm_operations()` 生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | int | 非 GC safepoint 次数 |
| `total_ms` | float | 非 GC safepoint 总时间 |
| `avg_ms` / `min_ms` / `max_ms` / `median_ms` / `p95_ms` | float | 统计值 |

**数据来源**：`Total time for which application threads were stopped: X seconds, Stopping threads took: Y seconds` 行。`non_gc_pause_sec = total_stopped_sec - gc_pause_sec`，其中 gc_pause_sec 通过与最近 GC 的 real time 关联得出。

---

## memory_efficiency

由 `_build_memory_efficiency()` 生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_freed_mb` | float | 所有 GC 累计释放内存（仅统计 freed > 0 的事件） |
| `avg_freed_per_gc_mb` | float | 每次 GC 平均释放内存 |
| `total_freed_by_full_gc_mb` | float? | Full GC 累计释放（有 Full GC 时出现） |
| `avg_freed_per_full_gc_mb` | float? | 每次 Full GC 平均释放（有 Full GC 时出现） |

**计算**：`freed = heap_before_mb - heap_after_mb`，仅当结果 > 0 时计入。

---

## promotion

由 `_build_promotion()` 生成。仅当事件包含完整的 heap/eden/survivor 前后数据时出现（JDK 8 G1 + PrintGCDetails）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_promoted_mb` | float | 累计晋升到老年代的内存 |
| `avg_promoted_per_gc_mb` | float | 每次 GC 平均晋升量 |
| `max_promoted_mb` | float | 单次 GC 最大晋升量 |

**计算方式**：
```
tenured_before = heap_before - eden_before - survivor_before
tenured_after  = heap_after  - eden_after  - survivor_after
promoted = tenured_after - tenured_before
```
仅当 `promoted > 0` 时计入。

**近似性说明**：G1 堆 = eden + survivor + tenured + humongous。若存在 humongous 对象变化，会被近似归入 tenured。这是 GCViewer 采用的相同近似。

---

## pause_intervals_ms

由 `_build_pause_intervals()` 生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `avg` / `min` / `max` / `median` / `p95` | float | 相邻 STW 事件的时间间隔统计（毫秒） |

**计算方式**：按 timestamp 排序后，`interval = (curr_ts - prev_ts) * 1000`。仅统计有 `timestamp` 且 `pause_ms > 0` 的事件，排除 ZGC `Collection (total)` 事件。

---

## anomalies 数组项

| 字段 | 类型 | 说明 |
|------|------|------|
| `line` | int | 异常所在行号 |
| `type` | string | 异常类型 |
| `pause_ms` | float? | 相关停顿时间（ms） |
| `description` | string | 异常描述 |
| `seconds_since_startup` | float? | 距 JVM 启动的时间（秒，仅 startup_analysis 成功计算时出现） |
| `in_startup_period` | bool? | 是否发生在启动期内（前 5 分钟） |

**type 枚举**（零容忍型事实异常，发生即代表 JVM 行为超出正常设计范围）：
- `full_gc`：Full GC 事件
- `allocation_stall`：ZGC 分配停顿（应用线程被阻塞）
- `to_space_exhausted`：G1 To-space 耗尽（evacuation failure）
- `humongous_allocation`：G1 Humongous 对象分配
- `degenerated_gc`：Shenandoah 退化 GC（并发失败回退 STW）
- `concurrent_mark_overflow`：G1 并发标记溢出重置

**以下类型 parser 不标记**，由分析层从聚合数据中自行判断：
- 长停顿 → 从 `metrics.max_pause_ms` / `pause_by_type` 判断
- Metaspace 不足 → 从 `gc_causes` 中 "Metadata GC Threshold" 的次数判断
- VM 操作开销 → 从 `vm_operations` 判断
- 频繁 GC → 从 `metrics.gc_frequency_per_minute` 判断

---

## gc_events 数组项（含 recent_events_sample）

| 字段 | 类型 | 说明 |
|------|------|------|
| `line` | int | 事件起始行号 |
| `gc_id` | int? | GC ID（JDK 9+ 统一日志中出现） |
| `type` | string | 事件类型描述 |
| `pause_ms` | float | 停顿时间（ms）。对 ZGC `Collection (total)` 是完整周期时间（秒转 ms） |
| `is_full_gc` | bool | 是否为 Full GC |
| `raw` | string | 原始日志片段（截断至 200 字符） |
| `timestamp` | string? | 时间戳（ISO 格式或 uptime 秒数） |
| `heap_before_mb` / `heap_after_mb` | float? | GC 前后堆大小（MB） |
| `eden_before_mb` / `eden_after_mb` | float? | Eden 区前后大小（MB，JDK 8 G1） |
| `survivor_before_mb` / `survivor_after_mb` | float? | Survivor 区前后大小（MB，JDK 8 G1） |
| `metaspace_used_kb` | int? | Metaspace 使用量（KB） |
| `phases` | array? | 详细阶段列表 `[{"name": "...", "duration_ms": ...}]` |
| `cpu_utilization_percent` | float? | GC 线程 CPU 利用率（JDK 8 详细模式） |
| `gc_workers` | int? | GC Worker 线程数 |
| `object_copy_ms` | object? | `{min, avg, max, diff, sum}`（JDK 8 G1） |
| `worker_start_ms` | object? | `{min, avg, max, diff}`（JDK 8 G1） |
| `times` | object? | `{user, sys, real}`（JDK 8 `[Times: ...]` 原始值） |
| `survivor_threshold` | object? | `{desired_bytes, new_threshold, max_threshold}` |
| `gc_cause` | string? | GC 触发原因（JDK 8 从 trigger 提取，JDK 9+ 从日志行提取，ZGC 为 "ZGC Y/O/Major/Minor"） |

---

## gc_efficiency

由 `_build_gc_efficiency()` 生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `freed_mem_per_minute` | float | 每分钟释放的内存量 (MB/min) = `total_freed_mb / (estimated_runtime_ms / 60000)` |
| `avg_performance_mbps` | float | 每毫秒暂停释放的内存 (MB/ms) = `total_freed_mb / total_pause_ms` |
| `full_gc_performance_mbps` | float? | Full GC 每毫秒释放的内存（有 Full GC 且释放 > 0 时出现） |
| `regular_gc_performance_mbps` | float? | 普通 GC 每毫秒释放的内存（非 Full GC 有释放时出现） |

**条件**：`memory_efficiency` 有数据且 `total_pause_ms > 0` 且 `estimated_runtime_ms > 0`。

---

## gc_causes

由 `_build_gc_causes()` 生成。

格式：`{"G1 Evacuation Pause": {"count": 320, "total_pause_ms": 14400, "avg_pause_ms": 45.0, "max_pause_ms": 1329.0}, ...}`

每个原因的统计对象：

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | int | 该原因触发次数 |
| `total_pause_ms` | float | 该原因触发的 GC 总暂停时间 |
| `avg_pause_ms` | float | 平均暂停 |
| `max_pause_ms` | float | 最大暂停 |

**排序**：按 `total_pause_ms` 降序。

**条件**：至少一个事件有 `gc_cause`。

---

## full_gc_summary

由 `_build_full_gc_summary()` 生成。仅当 `full_gc_count > 0` 时出现。

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | int | Full GC 次数 |
| `total_pause_ms` | float | Full GC 总暂停时间 |
| `avg_pause_ms` | float | 平均暂停 |
| `max_pause_ms` | float | 最大暂停 |
| `min_pause_ms` | float | 最小暂停 |
| `total_freed_mb` | float? | Full GC 累计释放内存（有 heap 数据时出现） |
| `avg_freed_mb` | float? | 每次 Full GC 平均释放（有 heap 数据时出现） |

---

## heap_trigger_stats

由 `_build_heap_trigger_stats()` 生成。

| 字段 | 类型 | 说明 |
|------|------|------|
| `avg_usage_percent` | float | GC 触发时平均堆占用比例 |
| `max_usage_percent` | float | 最高堆占用比例 |
| `min_usage_percent` | float | 最低堆占用比例 |
| `high_usage_count` | int | 触发时占用 >80% 的次数 |
| `approximate_max_heap_mb` | float | 推断的最大堆大小 |
| `note` | string | 说明这是近似值，准确 IOF 需要 `-XX:+PrintAdaptiveSizePolicy` |

**条件**：至少 5 个事件有 `heap_before_mb`。

**max_heap 估算方式**：
1. 优先使用从 G1 `Heap: X(Y)->Z(W)` 行提取的 capacity（W 值）
2. 回退到 `max(heap_before_mb, heap_after_mb for all events) * 1.1`

---

## Level 3: Coordinate Data

以下字段是**事实数据**（排序/采样/聚合），parser **不做阈值判断**。AI 从这些数据中自行判断哪些事件构成异常，并用其坐标（`line_number` / `timestamp`）提取原始日志上下文。

### Coordinate Event 公共字段

以下字段出现在 `top_pauses`、`full_gc_events`、`top_by_type`、`top_by_cause`、`promotion_spikes` 的每个条目中：

| 字段 | 类型 | 说明 |
|------|------|------|
| `line_number` | int | 事件在原始日志中的行号 |
| `timestamp` | string? | 时间戳（datetime 或 uptime） |
| `pause_ms` | float | STW 停顿毫秒数 |
| `gc_type` | string | GC 事件类型 |
| `gc_cause` | string? | 触发原因 |
| `is_full_gc` | bool? | 是否为 Full GC |
| `heap_before_mb` | float? | GC 前堆占用（MB） |
| `heap_after_mb` | float? | GC 后堆占用（MB） |

---

### top_pauses

由 `_build_top_pauses()` 生成。

**语义**：按 `pause_ms` 降序排列的前 20 个 STW 停顿事件。

**排除**：ZGC `Collection (total)` 事件（整周期时长，非 STW）。

**示例**：

```json
[
  {
    "rank": 1,
    "line_number": 15234,
    "timestamp": "2024-01-15T10:23:45.123",
    "pause_ms": 512.3,
    "gc_type": "G1 Evacuation Pause",
    "gc_cause": "G1 Evacuation Pause",
    "is_full_gc": false,
    "heap_before_mb": 2048,
    "heap_after_mb": 1536
  }
]
```

**条件**：至少 1 个 pause_ms > 0 的 STW 事件。

---

### full_gc_events

由 `_build_full_gc_events()` 生成。

**语义**：全部 Full GC 事件列表（通常数量极少，全量输出）。

**字段**：同 Coordinate Event 公共字段（不含 `rank`）。

**条件**：`full_gc_count > 0`。

---

### top_by_type

由 `_build_top_by_type()` 生成。

**语义**：按 GC `type` 分组，每组内按 `pause_ms` 降序取前 10 个。

**用途**：Mixed GC 低效分析——Mixed GC 平均耗时高但单个事件不够长，可能进不了 `top_pauses`。

**示例**：

```json
{
  "G1 Evacuation Pause": [
    {"line_number": 15234, "timestamp": "...", "pause_ms": 512.3, ...}
  ],
  "ZGC O: Mark End": [
    {"line_number": 3223, "timestamp": "...", "pause_ms": 0.096, ...}
  ]
}
```

**条件**：至少 1 个 pause_ms > 0 的 STW 事件。

---

### top_by_cause

由 `_build_top_by_cause()` 生成。

**语义**：按 GC `gc_cause` 分组，每组内按 `pause_ms` 降序取前 10 个。

**用途**：Metaspace 不足分析——`Metadata GC Threshold` 事件的 `pause_ms` 通常很短，不在 `top_pauses` 中。

**字段**：同 Coordinate Event 公共字段。

**条件**：至少 1 个事件含 `gc_cause`。

---

### gc_cadence

由 `_build_gc_cadence()` 生成。

**语义**：固定时间窗口（默认 60 秒）内 GC 次数和总停顿时间的时间序列。

**示例**：

```json
{
  "window_seconds": 60,
  "windows": [
    {"start_time": "2024-01-15T10:23:00", "gc_count": 3, "total_pause_ms": 450},
    {"start_time": "2024-01-15T10:24:00", "gc_count": 18, "total_pause_ms": 2100}
  ]
}
```

**`start_time` 格式**：
- 有绝对时间戳的日志：`ISO-8601` 字符串
- 仅有 uptime 的日志：`uptime_seconds` 浮点数

**用途**：定位频繁 GC 的时间段——找 `gc_count` 突增的窗口。

**条件**：至少 2 个带 `timestamp` 的 STW 事件。

---

### heap_samples

由 `_build_heap_samples()` 生成。

**语义**：从有 `heap_after_mb` 的 GC 事件中均匀采样（最多 20 个点）。

**示例**：

```json
[
  {"timestamp": "2024-01-15T10:23:00", "heap_after_mb": 1200, "gc_event_index": 45},
  {"timestamp": "2024-01-15T10:24:00", "heap_after_mb": 1450, "gc_event_index": 63}
]
```

**用途**：验证 `heap_trend` 的回归结论，观察堆增长的具体时间点。

**条件**：至少 1 个 GC 事件含 `heap_after_mb`。

---

### safepoint_events

由 `_build_safepoint_events()` 生成。

**语义**：非 GC safepoint 事件，按 `non_gc_pause_ms` 降序，最多 20 个。

**示例**：

```json
[
  {
    "line_number": 7890,
    "timestamp": "2024-01-15T10:25:30.500",
    "total_stopped_ms": 350.0,
    "stopping_ms": 2.5,
    "non_gc_pause_ms": 347.5
  }
]
```

**用途**：定位具体的 VM 操作停顿事件。

**条件**：日志包含 safepoint 数据（`-XX:+PrintGCApplicationStoppedTime`），且存在 `non_gc_pause_sec > 0` 的事件。

---

### promotion_spikes

由 `_build_promotion_spikes()` 生成。

**语义**：按晋升到老年代的 MB 数降序排列的前 10 个事件。

**晋升量计算**：`(heap_after - eden_after - survivor_after) - (heap_before - eden_before - survivor_before)`

**示例**：

```json
[
  {
    "rank": 1,
    "line_number": 5678,
    "timestamp": "2024-01-15T10:26:00",
    "promoted_mb": 1024.5,
    "gc_type": "G1 Evacuation Pause",
    "pause_ms": 320.0,
    "heap_before_mb": 4096,
    "heap_after_mb": 3072
  }
]
```

**用途**：定位晋升风暴的具体事件。

**条件**：至少 1 个 GC 事件同时含 `heap_before_mb`、`heap_after_mb`、`eden_before_mb`、`eden_after_mb`、`survivor_before_mb`、`survivor_after_mb`。

**注意**：仅 JDK 8 G1 `-XX:+PrintGCDetails` 日志通常包含完整 Eden/Survivor 数据。JDK 9+ 统一日志通常不提供这些字段，此时该字段不出现。
