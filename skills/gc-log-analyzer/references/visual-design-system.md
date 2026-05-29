# Visual Design System Reference for GC Reports

CSS tokens, components, and layout patterns for self-contained HTML GC reports.
Include all CSS at the top of every generated HTML file.

## Tokens

```css
:root {
  /* Palette */
  --ivory:    #FAF9F5;   /* page background */
  --slate:    #141413;   /* primary text / headings */
  --clay:     #D97757;   /* accent / CTA / warning */
  --clay-d:   #B85C3E;   /* accent dark */
  --oat:      #E3DACC;   /* secondary bg / tags */
  --olive:    #788C5D;   /* success / positive */
  --sky:      #6A8CAF;   /* info / neutral */
  --rust:     #B04A3F;   /* error / danger */

  /* Grays */
  --gray-50:  #F0EEE6;   /* card bg / code bg */
  --gray-200: #D1CFC5;   /* borders */
  --gray-500: #87867F;   /* secondary text */
  --gray-700: #3D3D3A;   /* body text */
  --white:    #FFFFFF;   /* card surface */

  /* Typography */
  --serif: ui-serif, Georgia, 'Times New Roman', serif;
  --sans:  system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --mono:  ui-monospace, 'SF Mono', Menlo, Consolas, monospace;

  /* Geometry */
  --radius-panel: 12px;
  --radius-row:    8px;
  --radius-pill: 999px;
  --border: 1.5px solid var(--gray-300);
}
```

## Base Reset

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: var(--sans);
  background: var(--ivory);
  color: var(--slate);
  font-size: 15px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  padding: 56px 24px 96px;
}
.page { max-width: 980px; margin: 0 auto; }
```

## Typography Scale

```css
.t-display { font-family: var(--serif); font-size: clamp(36px, 5vw, 48px); line-height: 1.08; font-weight: 500; letter-spacing: -0.02em; }
.t-h1      { font-family: var(--serif); font-size: clamp(28px, 3.5vw, 40px); line-height: 1.15; font-weight: 500; letter-spacing: -0.01em; }
.t-h2      { font-family: var(--serif); font-size: clamp(22px, 2.5vw, 26px); line-height: 1.2; font-weight: 500; }
.t-h3      { font-family: var(--serif); font-size: 20px; line-height: 1.25; font-weight: 500; }
.t-body    { font-family: var(--sans);  font-size: 15px; line-height: 1.55; font-weight: 430; }
.t-small   { font-family: var(--sans);  font-size: 14px; line-height: 1.5; font-weight: 430; }
.t-caption { font-family: var(--sans);  font-size: 12px; line-height: 1.4; font-weight: 500; color: var(--gray-500); }
.t-mono    { font-family: var(--mono);  font-size: 12px; line-height: 1.5; letter-spacing: 0.01em; }
.t-eyebrow { font-family: var(--mono); font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--gray-500); }
```

## Layout Patterns

```css
/* Centered reading column */
.layout-single { max-width: 760px; margin: 0 auto; }

/* Two-column: content + sidebar */
.layout-split {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 32px; align-items: start;
}
@media (max-width: 960px) { .layout-split { grid-template-columns: 1fr; } }

/* Card grid auto-fill */
.layout-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

/* Sticky sidebar */
.sticky { position: sticky; top: 24px; }
```

## Components

### Panel / Card
```css
.panel {
  background: var(--white);
  border: var(--border);
  border-radius: var(--radius-panel);
  padding: 24px;
}
.panel-subtle {
  background: var(--gray-50);
  border: var(--border);
  border-radius: var(--radius-panel);
  padding: 16px 20px;
}
```

### Code Block
```css
.code-block {
  background: var(--slate);
  border-radius: var(--radius-panel);
  padding: 18px 20px;
  overflow-x: auto;
}
.code-block pre {
  font-family: var(--mono);
  font-size: 12.5px;
  line-height: 1.65;
  color: #E8E6DE;
  white-space: pre;
}
.code-block .kw  { color: var(--clay); }
.code-block .str { color: var(--olive); }
.code-block .cm  { color: var(--gray-500); }
.code-block .fn  { color: #C9B98A; }
```

### Inline Code
```css
code {
  font-family: var(--mono);
  font-size: 13px;
  background: var(--gray-50);
  padding: 1px 5px;
  border-radius: 4px;
}
```

### Chip / Tag
```css
.chip {
  font-family: var(--mono);
  font-size: 11.5px;
  background: var(--gray-50);
  border: var(--border);
  color: var(--gray-700);
  padding: 5px 10px;
  border-radius: var(--radius-row);
  white-space: nowrap;
  display: inline-block;
}
.chip-strong { color: var(--slate); font-weight: 600; }
```

### Table
```css
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.data-table th, .data-table td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--gray-300);
}
.data-table th {
  font-family: var(--mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--gray-500);
  background: var(--gray-50);
}
```

### Banner / Alert
```css
.banner {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 10px 14px;
  border: 1.5px solid #E8C2AE;
  background: #F8E9E0;
  color: var(--clay-d);
  border-radius: 10px;
  font-size: 13px;
}
.banner-danger {
  border-color: rgba(176,74,63,0.25);
  background: rgba(176,74,63,0.06);
  color: var(--rust);
}
.banner-ok {
  border-color: rgba(120,140,93,0.25);
  background: rgba(120,140,93,0.06);
  color: var(--olive);
}
```

### Metrics Grid
```css
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}
.metric {
  text-align: center;
  padding: 16px 8px;
  background: var(--gray-50);
  border-radius: var(--radius-row);
  border: var(--border);
}
.metric .value {
  font-size: 1.4rem;
  font-weight: 700;
  font-family: var(--serif);
}
.metric .label {
  font-size: 0.78rem;
  color: var(--gray-500);
  margin-top: 4px;
  font-family: var(--mono);
}
```

## Utility Classes

```css
/* Margins */
.mb-sm  { margin-bottom: 12px; }
.mb-md  { margin-bottom: 24px; }
.mb-lg  { margin-bottom: 48px; }
.mb-xl  { margin-bottom: 64px; }

/* Text */
.text-muted  { color: var(--gray-500); }
.text-center { text-align: center; }

/* Status colors */
.status-ok   { color: var(--olive); }
.status-warn { color: var(--clay); }
.status-err  { color: var(--rust); }

/* Status dots */
.dot-ok::before,
.dot-warn::before,
.dot-err::before {
  content: '';
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  margin-right: 8px;
  vertical-align: 2px;
}
.dot-ok::before   { background: var(--olive); }
.dot-warn::before { background: var(--clay); }
.dot-err::before  { background: var(--rust); }
```

## Responsive Breakpoints

- `960px` — `.layout-split` stacks
- `600px` — body padding reduces, `.metrics-grid` becomes 2-column
