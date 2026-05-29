"""Chart asset generator for GC HTML reports.

Provides inline SVG charts and HTML snippets from parser summary JSON.
Importable module — no CLI, no side effects.

Example:
    import json
    from html_report import generate_chart_assets

    with open("summary.json") as f:
        summary = json.load(f)
    assets = generate_chart_assets(summary)
    print(assets["heap_trend_svg"])
"""

import math
from typing import Any, Dict, List

__all__ = ["generate_chart_assets"]

# ---------------------------------------------------------------------------
# Chart constants
# ---------------------------------------------------------------------------
DEFAULT_CHART_WIDTH = 700
DEFAULT_MARGIN = 40

CHART_HEIGHTS = {
    "heap_trend": 240,
    "gc_cadence": 220,
    "pause_scatter": 240,
    "pause_by_type": None,  # dynamic
    "gc_causes": 220,
    "startup_timeline": 200,
}

CADENCE_HIGH_THRESHOLD = 20
CADENCE_MED_THRESHOLD = 5

# ---------------------------------------------------------------------------
# Colors (visual-html design system)
# ---------------------------------------------------------------------------
IVORY = "#FAF9F5"
SLATE = "#141413"
CLAY = "#D97757"
CLAY_D = "#B85C3E"
OAT = "#E3DACC"
OLIVE = "#788C5D"
SKY = "#6A8CAF"
RUST = "#B04A3F"
GRAY50 = "#F0EEE6"
GRAY200 = "#D1CFC5"
GRAY500 = "#87867F"
GRAY700 = "#3D3D3A"
WHITE = "#FFFFFF"


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------
def _svg_start(w: int, h: int) -> str:
    return (
        f'<svg width="100%" height="100%" viewBox="0 0 {w} {h}" '
        'xmlns="http://www.w3.org/2000/svg" style="display:block;">'
    )


def _svg_end() -> str:
    return "</svg>"


def _grid_lines(M: int, chart_w: int, chart_h: int, count: int = 5) -> List[str]:
    """Horizontal grid lines + Y-axis base."""
    out = []
    for i in range(count):
        y = M + chart_h - (i / (count - 1)) * chart_h
        out.append(
            f'<line x1="{M}" y1="{y}" x2="{M + chart_w}" y2="{y}" '
            f'stroke="{GRAY200}" stroke-width="0.5"/>'
        )
    out.append(
        f'<line x1="{M}" y1="{M + chart_h}" x2="{M + chart_w}" y2="{M + chart_h}" '
        f'stroke="{GRAY200}" stroke-width="1.5"/>'
    )
    out.append(
        f'<line x1="{M}" y1="{M}" x2="{M}" y2="{M + chart_h}" '
        f'stroke="{GRAY200}" stroke-width="1.5"/>'
    )
    return out


# ---------------------------------------------------------------------------
# Chart 1: Heap Trend (area + line)
# ---------------------------------------------------------------------------
def _heap_trend_svg(summary: Dict[str, Any]) -> str:
    heap_samples = summary.get("heap_samples", [])
    samples = [s for s in heap_samples if isinstance(s, dict) and "heap_after_mb" in s and "timestamp" in s]
    if len(samples) < 2:
        return ""

    values = [s["heap_after_mb"] for s in samples]
    labels = [s["timestamp"][11:16] for s in samples]
    h_min, h_max = min(values), max(values)
    h_range = max(h_max - h_min, 1)

    W, H = DEFAULT_CHART_WIDTH, CHART_HEIGHTS["heap_trend"]
    M = DEFAULT_MARGIN
    chart_w, chart_h = W - M * 2, H - M * 2
    n = len(values)

    points = []
    for i, v in enumerate(values):
        x = M + (i / (n - 1)) * chart_w
        y = M + chart_h - ((v - h_min) / h_range) * chart_h
        points.append(f"{x:.1f},{y:.1f}")

    area_d = f"M {points[0]} " + " ".join(f"L {p}" for p in points[1:])
    area_d += f" L {M + chart_w},{M + chart_h} L {M},{M + chart_h} Z"
    line_d = f"M {points[0]} " + " ".join(f"L {p}" for p in points[1:])

    y_labels = []
    for i in range(5):
        v = h_min + (i / 4) * h_range
        y = M + chart_h - (i / 4) * chart_h
        y_labels.append(
            f'<text x="{M - 8}" y="{y + 4}" text-anchor="end" font-size="10" '
            f'fill="{GRAY500}" font-family="ui-monospace,monospace">{v:.0f}</text>'
        )

    x_labels = []
    step = max(1, n // 6)
    for i in range(0, n, step):
        x = M + (i / (n - 1)) * chart_w
        x_labels.append(
            f'<text x="{x}" y="{H - 12}" text-anchor="middle" font-size="10" '
            f'fill="{GRAY500}" font-family="ui-monospace,monospace">{labels[i]}</text>'
        )

    point_circles = "".join(
        f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3" '
        f'fill="{WHITE}" stroke="{OLIVE}" stroke-width="1.5"/>'
        for p in points
    )

    grid = "".join(_grid_lines(M, chart_w, chart_h))

    return (
        _svg_start(W, H)
        + "".join(y_labels)
        + grid
        + f'<path d="{area_d}" fill="rgba(120,140,93,0.08)"/>'
        + f'<path d="{line_d}" fill="none" stroke="{OLIVE}" stroke-width="2" '
        + 'stroke-linecap="round" stroke-linejoin="round"/>'
        + point_circles
        + "".join(x_labels)
        + f'<text x="{M - 30}" y="{M - 10}" font-size="10" fill="{GRAY500}" '
        + 'font-family="ui-monospace,monospace">MB</text>'
        + _svg_end()
    )


# ---------------------------------------------------------------------------
# Chart 2: GC Cadence (bar + dashed line dual-axis)
# ---------------------------------------------------------------------------
def _gc_cadence_svg(summary: Dict[str, Any]) -> str:
    windows = summary.get("gc_cadence", {}).get("windows", [])
    valid = [w for w in windows if isinstance(w, dict) and all(k in w for k in ("start_time", "gc_count", "total_pause_ms"))]
    if not valid:
        return ""

    step = max(1, len(valid) // 40)
    filtered = valid[::step]
    labels = [w["start_time"][11:16] for w in filtered]
    counts = [w["gc_count"] for w in filtered]
    pauses = [w["total_pause_ms"] for w in filtered]
    c_max = max(counts) if counts else 1
    p_max = max(pauses) if pauses else 1

    W, H = DEFAULT_CHART_WIDTH, CHART_HEIGHTS["gc_cadence"]
    M = DEFAULT_MARGIN
    chart_w, chart_h = W - M * 2, H - M * 2
    n = len(filtered)
    bar_w = chart_w / n * 0.6

    bars = []
    for i, (c, p) in enumerate(zip(counts, pauses)):
        x = M + (i / n) * chart_w + bar_w * 0.3
        h = (c / c_max) * chart_h
        y = M + chart_h - h
        fill = (
            RUST if c > CADENCE_HIGH_THRESHOLD
            else CLAY if c > CADENCE_MED_THRESHOLD
            else "rgba(106,140,175,0.7)"
        )
        bars.append(
            f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" '
            f'fill="{fill}" rx="2"/>'
        )

    line_pts = []
    for i, p in enumerate(pauses):
        x = M + (i / n) * chart_w + bar_w * 0.8
        y = M + chart_h - (p / p_max) * chart_h
        line_pts.append(f"{x:.1f},{y:.1f}")
    line_d = (
        f"M {line_pts[0]} " + " ".join(f"L {p}" for p in line_pts[1:])
        if line_pts else ""
    )

    y_labels = []
    for i in range(5):
        y = M + chart_h - (i / 4) * chart_h
        y_labels.append(
            f'<text x="{M - 8}" y="{y + 4}" text-anchor="end" font-size="10" '
            f'fill="{GRAY500}" font-family="ui-monospace,monospace">'
            f'{int(c_max * i / 4)}</text>'
        )

    x_labels = []
    x_step = max(1, n // 6)
    for i in range(0, n, x_step):
        x = M + (i / n) * chart_w + bar_w * 0.5
        x_labels.append(
            f'<text x="{x}" y="{H - 12}" text-anchor="middle" font-size="10" '
            f'fill="{GRAY500}" font-family="ui-monospace,monospace">{labels[i]}</text>'
        )

    grid = "".join(_grid_lines(M, chart_w, chart_h))

    legend = (
        f'<g transform="translate({M + chart_w - 140}, {M + 10})">'
        f'<rect x="0" y="0" width="10" height="10" fill="rgba(106,140,175,0.7)" rx="2"/>'
        f'<text x="16" y="9" font-size="10" fill="{GRAY700}">Count</text>'
        f'<line x1="0" y1="20" x2="10" y2="20" stroke="{CLAY_D}" '
        f'stroke-width="1.5" stroke-dasharray="4 2"/>'
        f'<text x="16" y="24" font-size="10" fill="{GRAY700}">Pause(ms)</text>'
        f"</g>"
    )

    return (
        _svg_start(W, H)
        + "".join(y_labels)
        + grid
        + "".join(bars)
        + f'<path d="{line_d}" fill="none" stroke="{CLAY_D}" stroke-width="1.5" '
        + 'stroke-dasharray="4 2"/>'
        + "".join(x_labels)
        + legend
        + _svg_end()
    )


# ---------------------------------------------------------------------------
# Chart 3: Pause Scatter (log Y-axis, top 20)
# ---------------------------------------------------------------------------
def _pause_scatter_svg(summary: Dict[str, Any]) -> str:
    top = summary.get("top_pauses", [])
    valid = [p for p in top if isinstance(p, dict) and "pause_ms" in p]
    if not valid:
        return ""

    vals = [p["pause_ms"] for p in valid]
    s_min, s_max = min(vals), max(vals)
    log_min = math.log10(max(s_min, 1))
    log_max = math.log10(s_max)
    log_range = max(log_max - log_min, 0.001)

    anomalies = summary.get("anomalies", [])
    anomaly_lines = {a.get("line"): a for a in anomalies if isinstance(a, dict) and "line" in a}

    W, H = DEFAULT_CHART_WIDTH, CHART_HEIGHTS["pause_scatter"]
    M = DEFAULT_MARGIN
    chart_w, chart_h = W - M * 2, H - M * 2
    n = len(valid)

    dots = []
    for i, p in enumerate(valid):
        x = M + (i / max(n - 1, 1)) * chart_w
        log_y = math.log10(max(p["pause_ms"], 1))
        y = M + chart_h - ((log_y - log_min) / log_range) * chart_h

        if p.get("is_full_gc"):
            color, r = RUST, 8
        elif p.get("line_number") in anomaly_lines:
            color, r = CLAY, 5
        else:
            color, r = SKY, 3

        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" '
            f'fill="{color}" opacity="0.85"/>'
        )

    y_labels = []
    for t in [1, 10, 100, 1000, 10000]:
        if log_min <= math.log10(t) <= log_max + 0.1:
            y = M + chart_h - ((math.log10(t) - log_min) / log_range) * chart_h
            y_labels.append(
                f'<text x="{M - 8}" y="{y + 4}" text-anchor="end" font-size="10" '
                f'fill="{GRAY500}" font-family="ui-monospace,monospace">{t}ms</text>'
            )
            y_labels.append(
                f'<line x1="{M}" y1="{y}" x2="{M + chart_w}" y2="{y}" '
                f'stroke="{GRAY200}" stroke-width="0.5"/>'
            )

    grid = "".join(_grid_lines(M, chart_w, chart_h))

    legend = (
        f'<g transform="translate({M + 10}, {M + 10})">'
        f'<circle cx="5" cy="10" r="8" fill="{RUST}"/>'
        f'<text x="18" y="14" font-size="10" fill="{GRAY700}">Full GC</text>'
        f'<circle cx="5" cy="30" r="5" fill="{CLAY}"/>'
        f'<text x="18" y="34" font-size="10" fill="{GRAY700}">Anomaly</text>'
        f'<circle cx="5" cy="48" r="3" fill="{SKY}"/>'
        f'<text x="18" y="51" font-size="10" fill="{GRAY700}">Normal</text>'
        f"</g>"
    )

    return (
        _svg_start(W, H)
        + "".join(y_labels)
        + grid
        + "".join(dots)
        + f'<text x="{M + chart_w / 2}" y="{H - 4}" text-anchor="middle" '
        + f'font-size="10" fill="{GRAY500}" font-family="ui-monospace,monospace">'
        + "Rank (by pause duration)</text>"
        + legend
        + _svg_end()
    )


# ---------------------------------------------------------------------------
# Chart 4: Pause by Type (horizontal bars)
# ---------------------------------------------------------------------------
def _pause_by_type_svg(summary: Dict[str, Any]) -> str:
    items = [
        (k, v) for k, v in summary.get("pause_by_type", {}).items()
        if isinstance(v, dict) and "count" in v and "avg_ms" in v
    ]
    if not items:
        return ""

    items.sort(key=lambda x: x[1]["count"], reverse=True)
    max_count = max(it[1]["count"] for it in items)

    W = DEFAULT_CHART_WIDTH
    H = 20 + len(items) * 40
    bar_h = 24
    gap = 16

    bars = []
    for i, (name, stats) in enumerate(items):
        y = 20 + i * (bar_h + gap)
        w = (stats["count"] / max_count) * 500
        fill = RUST if "Full" in name else SKY if "Young" in name else GRAY500
        bars.append(
            f'<text x="0" y="{y + 16}" font-size="12" fill="{GRAY700}" '
            f'font-family="system-ui,sans-serif">{name}</text>'
        )
        bars.append(
            f'<rect x="180" y="{y}" width="{w}" height="{bar_h}" '
            f'fill="{fill}" rx="4" opacity="0.8"/>'
        )
        bars.append(
            f'<text x="{180 + w + 8}" y="{y + 16}" font-size="11" '
            f'fill="{GRAY500}" font-family="ui-monospace,monospace">'
            f'{stats["count"]} · avg {stats["avg_ms"]:.0f}ms</text>'
        )

    return _svg_start(W, H) + "".join(bars) + _svg_end()


# ---------------------------------------------------------------------------
# Chart 5: GC Causes (doughnut)
# ---------------------------------------------------------------------------
def _gc_causes_svg(summary: Dict[str, Any]) -> str:
    items = [
        (k, v) for k, v in summary.get("gc_causes", {}).items()
        if isinstance(v, dict) and "count" in v
    ]
    if not items:
        return ""

    items.sort(key=lambda x: x[1]["count"], reverse=True)
    total = sum(c[1]["count"] for c in items)

    W, H = DEFAULT_CHART_WIDTH, CHART_HEIGHTS["gc_causes"]
    cx, cy, r = 160, 110, 70
    inner_r = 42

    colors = [
        RUST if "Full" in c[0] else SKY if "Evacuation" in c[0] else OLIVE
        if "Metadata" in c[0] else GRAY500
        for c in items
    ]

    segments = []
    labels = []
    start_a = -math.pi / 2

    for i, (name, stats) in enumerate(items):
        angle = (stats["count"] / total) * 2 * math.pi
        end_a = start_a + angle

        x1 = cx + r * math.cos(start_a)
        y1 = cy + r * math.sin(start_a)
        x2 = cx + r * math.cos(end_a)
        y2 = cy + r * math.sin(end_a)

        ix1 = cx + inner_r * math.cos(start_a)
        iy1 = cy + inner_r * math.sin(start_a)
        ix2 = cx + inner_r * math.cos(end_a)
        iy2 = cy + inner_r * math.sin(end_a)

        large = 1 if angle > math.pi else 0

        d = (
            f"M {ix1},{iy1} L {x1},{y1} A {r},{r} 0 {large} 1 {x2},{y2} "
            f"L {ix2},{iy2} A {inner_r},{inner_r} 0 {large} 0 {ix1},{iy1} Z"
        )
        segments.append(
            f'<path d="{d}" fill="{colors[i]}" opacity="0.85" '
            f'stroke="{WHITE}" stroke-width="2"/>'
        )

        mid_a = start_a + angle / 2
        lx = cx + (r + 25) * math.cos(mid_a)
        ly = cy + (r + 25) * math.sin(mid_a)
        anchor = "start" if math.cos(mid_a) >= 0 else "end"
        pct = stats["count"] / total * 100

        labels.append(
            f'<text x="{lx}" y="{ly + 4}" text-anchor="{anchor}" font-size="11" '
            f'fill="{GRAY700}" font-family="system-ui,sans-serif">{name}</text>'
        )
        labels.append(
            f'<text x="{lx}" y="{ly + 18}" text-anchor="{anchor}" font-size="10" '
            f'fill="{GRAY500}" font-family="ui-monospace,monospace">'
            f'{stats["count"]} ({pct:.1f}%)</text>'
        )

        start_a = end_a

    center_text = (
        f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="14" '
        f'font-weight="600" fill="{SLATE}" '
        f'font-family="var(--serif),Georgia,serif">{total}</text>'
        f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" font-size="9" '
        f'fill="{GRAY500}" font-family="ui-monospace,monospace">total</text>'
    )

    return (
        _svg_start(W, H)
        + "".join(segments)
        + center_text
        + "".join(labels)
        + _svg_end()
    )


# ---------------------------------------------------------------------------
# Chart 6: Startup Anomaly Timeline (bar chart)
# ---------------------------------------------------------------------------
def _startup_timeline_svg(summary: Dict[str, Any]) -> str:
    anomalies = summary.get("anomalies", [])
    valid = [a for a in anomalies if isinstance(a, dict) and "type" in a]
    if not valid:
        return ""

    events = []
    for a in valid:
        events.append(
            {
                "time": a.get("seconds_since_startup", 0),
                "type": a["type"],
                "pause": a.get("pause_ms", 0),
                "line": a.get("line", "—"),
            }
        )
    events.sort(key=lambda x: x["time"])

    W, H = DEFAULT_CHART_WIDTH, CHART_HEIGHTS["startup_timeline"]
    M = DEFAULT_MARGIN
    chart_w = W - M * 2

    t_min = events[0]["time"]
    t_max = events[-1]["time"]
    t_range = t_max - t_min

    bars = []
    if t_range == 0:
        # All anomalies at the same time — spread them evenly
        n = len(events)
        for i, e in enumerate(events):
            x = M + (i / max(n - 1, 1)) * chart_w
            h = max((e["pause"] / 15000) * 120, 15) if e["pause"] else 15
            fill = RUST if e["type"] == "full_gc" else CLAY
            label_y = M + 140 - h - 6
            pause_label = (
                f'<text x="{x}" y="{label_y}" text-anchor="middle" font-size="9" '
                f'fill="{GRAY700}" font-family="ui-monospace,monospace">'
                f'{e["pause"]:.0f}ms</text>'
                if e["pause"] else ""
            )
            bars.append(
                f'<rect x="{x - 8}" y="{M + 140 - h}" width="16" height="{h}" '
                f'fill="{fill}" rx="3" opacity="0.85"/>'
            )
            bars.append(pause_label)
            bars.append(
                f'<text x="{x}" y="{M + 160}" text-anchor="middle" font-size="9" '
                f'fill="{GRAY500}" font-family="ui-monospace,monospace">'
                f'T+{e["time"]:.0f}s</text>'
            )
    else:
        for e in events:
            x = M + ((e["time"] - t_min) / t_range) * chart_w
            h = max((e["pause"] / 15000) * 120, 15) if e["pause"] else 15
            fill = RUST if e["type"] == "full_gc" else CLAY
            label_y = M + 140 - h - 6
            pause_label = (
                f'<text x="{x}" y="{label_y}" text-anchor="middle" font-size="9" '
                f'fill="{GRAY700}" font-family="ui-monospace,monospace">'
                f'{e["pause"]:.0f}ms</text>'
                if e["pause"] else ""
            )
            bars.append(
                f'<rect x="{x - 8}" y="{M + 140 - h}" width="16" height="{h}" '
                f'fill="{fill}" rx="3" opacity="0.85"/>'
            )
            bars.append(pause_label)
            bars.append(
                f'<text x="{x}" y="{M + 160}" text-anchor="middle" font-size="9" '
                f'fill="{GRAY500}" font-family="ui-monospace,monospace">'
                f'T+{e["time"]:.0f}s</text>'
            )

    axis_y = M + 140

    legend = (
        f'<g transform="translate({M + 10}, {M + 10})">'
        f'<rect x="0" y="0" width="12" height="12" fill="{RUST}" rx="3"/>'
        f'<text x="18" y="10" font-size="10" fill="{GRAY700}">Full GC</text>'
        f'<rect x="0" y="18" width="12" height="12" fill="{CLAY}" rx="3"/>'
        f'<text x="18" y="28" font-size="10" fill="{GRAY700}">'
        f"To-space exhausted</text></g>"
    )

    return (
        _svg_start(W, H)
        + f'<line x1="{M}" y1="{axis_y}" x2="{M + chart_w}" y2="{axis_y}" '
        + f'stroke="{GRAY200}" stroke-width="1.5"/>'
        + "".join(bars)
        + f'<text x="{M + chart_w / 2}" y="{H - 4}" text-anchor="middle" '
        + f'font-size="10" fill="{GRAY500}" font-family="ui-monospace,monospace">'
        + "Seconds since JVM startup</text>"
        + legend
        + _svg_end()
    )


# ---------------------------------------------------------------------------
# Metrics Grid HTML
# ---------------------------------------------------------------------------
def _metrics_grid_html(summary: Dict[str, Any]) -> str:
    metrics = summary.get("metrics", {})
    heap_trend = summary.get("heap_trend", {})

    cards = [
        (f"{metrics.get('throughput_percent', 0):.2f}%", "吞吐量", "status-ok"),
        (f"{metrics.get('max_pause_ms', 0):.0f}ms", "最大 STW", "status-err"),
        (f"{metrics.get('avg_pause_ms', 0):.0f}ms", "平均 STW", ""),
        (f"{metrics.get('p95_pause_ms', 0):.0f}ms", "P95 STW", ""),
        (f"{metrics.get('full_gc_count', 0)}", "Full GC", "status-warn"),
        (f"{metrics.get('gc_frequency_per_minute', 0):.2f}/min", "GC 频率", ""),
        (heap_trend.get("leak_risk", "?"), "泄漏风险", "status-ok"),
        (str(heap_trend.get("estimated_hours_to_oom", "N/A")), "预计 OOM(h)", ""),
    ]

    cells = ""
    for value, label, cls in cards:
        cls_attr = f' class="{cls}"' if cls else ""
        cells += (
            f'<div class="metric">'
            f'<div class="value{cls_attr}">{value}</div>'
            f'<div class="label">{label}</div>'
            f"</div>"
        )

    return f'<div class="metrics-grid">{cells}</div>'


# ---------------------------------------------------------------------------
# Anomaly Table HTML
# ---------------------------------------------------------------------------
def _anomaly_table_html(summary: Dict[str, Any]) -> str:
    anomalies = summary.get("anomalies", [])
    if not anomalies:
        return '<p class="t-small text-muted">No anomalies detected.</p>'

    rows = ""
    for a in anomalies:
        if not isinstance(a, dict):
            continue
        a_type = a.get("type", "unknown")
        ts = a.get("seconds_since_startup", 0)
        pause = a.get("pause_ms", 0)
        pause_str = f"{pause:.0f}ms" if pause else "—"
        line = a.get("line", "—")
        chip_cls = "chip-p0" if a_type == "full_gc" else "chip-p1"
        startup_chip = (
            '<span class="chip chip-startup">启动期</span>'
            if a.get("in_startup_period") else ""
        )
        rows += (
            f'<tr>'
            f'<td class="t-mono">T+{ts:.1f}s</td>'
            f'<td>{a_type}</td>'
            f'<td class="t-mono">{pause_str}</td>'
            f'<td class="t-mono">{line}</td>'
            f'<td><span class="chip {chip_cls}">'
            f"P{'0' if a_type == 'full_gc' else '1'}</span> {startup_chip}</td>"
            f"</tr>"
        )

    return (
        '<table class="data-table">'
        "<thead><tr><th>时间</th><th>类型</th>"
        "<th>停顿</th><th>行号</th><th>标签</th></tr></thead>"
        f'<tbody>{rows}</tbody></table>'
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_chart_assets(summary: Dict[str, Any]) -> Dict[str, str]:
    """Generate all chart SVGs and HTML snippets from a summary dict."""
    if not isinstance(summary, dict):
        return {
            "heap_trend_svg": "",
            "gc_cadence_svg": "",
            "pause_scatter_svg": "",
            "pause_by_type_svg": "",
            "gc_causes_svg": "",
            "startup_timeline_svg": "",
            "metrics_grid_html": "",
            "anomaly_table_html": "",
        }

    return {
        "heap_trend_svg": _heap_trend_svg(summary),
        "gc_cadence_svg": _gc_cadence_svg(summary),
        "pause_scatter_svg": _pause_scatter_svg(summary),
        "pause_by_type_svg": _pause_by_type_svg(summary),
        "gc_causes_svg": _gc_causes_svg(summary),
        "startup_timeline_svg": _startup_timeline_svg(summary),
        "metrics_grid_html": _metrics_grid_html(summary),
        "anomaly_table_html": _anomaly_table_html(summary),
    }


# ---------------------------------------------------------------------------
# Development / debug helper (not part of the public API)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 html_report.py <summary.json>")
        sys.exit(1)

    try:
        with open(sys.argv[1]) as f:
            summary = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading {sys.argv[1]}: {e}", file=sys.stderr)
        sys.exit(1)

    assets = generate_chart_assets(summary)
    print(json.dumps({k: v[:200] + "..." if len(v) > 200 else v for k, v in assets.items()}, indent=2))
