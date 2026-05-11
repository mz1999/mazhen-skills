---
name: html-artifact
description: >
  Generate rich, single-file HTML artifacts instead of markdown. Use this skill
  whenever the user wants to present information visually — whether they ask for
  "an HTML file", "a visualization", "a report", "a comparison", "a diagram",
  or even just "summarize this in a nice format". Also trigger when they mention
  code reviews, PR writeups, weekly status, incident timelines, design systems,
  prototypes, slide decks, explainer pages, or interactive editors. If the user
  wants to compare options, explain a system, teach a concept, or present data
  to a team, this skill is the right choice over plain markdown.
  Automatically classifies content type, selects matching layout & components,
  and generates a self-contained .html file with no external dependencies.
---

# HTML Artifact Skill

Generate single-file HTML artifacts for any content, automatically selecting the right visual form based on content type.

## When to Use

Use this skill when the user wants to:
- Present information in a visually rich, shareable format
- Compare multiple options/solutions side by side
- Explain a complex system, flow, or codebase
- Create a report, status update, or incident timeline
- Build a throwaway interactive editor or prototype
- Replace a markdown document with something more readable

**Trigger even when the user doesn't explicitly say "HTML"** — phrases like "lay them out", "visualize", "draw a diagram", "make a slide deck", "explain how this works", or "summarize for my team" all indicate this skill should be used.

## Workflow

1. **Classify** the content into one of the 10 content types below
2. **Select** the matching layout and components
3. **Read** `references/design-system.md` for the full CSS tokens and components
4. **Generate** a single-file HTML with all CSS inlined in `<style>`
5. If interactive, add JS in `<script>` at the bottom

## Step 1: Content Classification

Analyze the user's content and classify into the closest type. The content type determines everything that follows.

| Content Type | Reader's Goal | Trigger Keywords |
|-------------|--------------|------------------|
| **Exploration** | Choose between alternatives | compare, approaches, options, tradeoffs |
| **CodeReview** | Understand code changes | diff, PR, review, annotated |
| **CodeUnderstanding** | Follow a system's logic | how it works, flow, architecture |
| **DesignSystem** | Document visual decisions | tokens, colors, typography, components |
| **Prototype** | Experience motion/interaction | animation, click-through, feel |
| **Diagram** | See spatial relationships | flowchart, pipeline, architecture |
| **Deck** | Present page by page | slides, presentation, weekly, pitch |
| **Research** | Learn a concept deeply | explainer, concept, deep-dive |
| **Report** | Consume summarized data | status, incident, metrics, timeline |
| **Editor** | Manipulate data and export | triage, config, flags, draft |

**Decision rule:** Ask "What does the reader need to DO with this information?"
- Pick between options → Exploration
- Follow a path → CodeUnderstanding / Diagram
- Watch something happen → Prototype
- Read and absorb → Report / Research
- Interact and export → Editor

## Step 2: Layout & Component Selection

For each content type, use the prescribed layout. Read `references/design-system.md` for full component CSS.

### Exploration
- **Layout:** `.layout-tri` (3-col) or `.layout-quad` (4-col)
- **Components:** `.panel` per option, `.code-block`, `.chip` for metrics
- **Structure:** Header → Grid of options → Recommendation box (`.panel-subtle`, left border `--clay`)
- **Example:** "Show 3 ways to handle API errors, side by side with tradeoffs"

### CodeReview
- **Layout:** Single column with margin annotations
- **Components:** `.diff` (`.del` / `.ins` / `.ctx`), `.chip` for severity, `.panel-subtle` for notes
- **Structure:** Header → Stats bar → Annotated diff → Action items

### CodeUnderstanding
- **Layout:** `.layout-split` (diagram left, code right)
- **Components:** SVG flowchart, `.code-block`, `.data-table`
- **Structure:** Title → Split view → Callstack walkthrough → Gotchas

### DesignSystem
- **Layout:** `.layout-cards` or stacked sections
- **Components:** Swatch grids, type-scale rows, spacing rulers
- **Structure:** Colors → Typography → Spacing → Components → Elevation

### Prototype
- **Layout:** Single centered stage + control panel
- **Components:** CSS animations, `<input type="range">`, `.btn` triggers
- **Structure:** Header → Stage → Controls → Parameters

### Diagram
- **Layout:** `.layout-split` (SVG left, detail panel right)
- **Components:** Inline SVG (`.node` / `.edge`), clickable nodes
- **Structure:** Title → SVG canvas → Legend → Detail panel

### Deck
- **Layout:** Full-viewport slides, `scroll-snap-type: y mandatory`
- **Components:** `.slide` per page, SVG sparklines, metric cards
- **Structure:** Title slide → Content slides → Metrics → Closing
- **Keyboard:** Arrow keys / space to navigate

### Research
- **Layout:** `.layout-split` (content left, glossary/aside right)
- **Components:** SVG illustrations, `.demo` panels, `.data-table`, `.term` tooltips
- **Structure:** TL;DR → Concept → Interactive demo → Comparison table → Deep dive

### Report
- **Layout:** Stacked sections with `.panel` grouping
- **Components:** `.timeline`, `.data-table`, SVG bar charts, `.chip`
- **Structure:** Summary → Timeline/Events → Data → Action Items

### Editor
- **Layout:** `.layout-split` or full-width with `.toolbar`
- **Components:** `.toolbar` (sticky), drag-and-drop, `.toggle`, `.btn`
- **Structure:** Header → Toolbar → Work area → Export panel

## Step 3: CSS & Design System

Read `references/design-system.md` for the complete CSS tokens, typography scale, layout patterns, and component styles. Copy the relevant sections into every generated HTML file.

**For human reference:** Open `assets/design-system.html` in a browser to see a live, browsable showcase of all tokens, components, and layout patterns. This is a visual companion to the CSS code in `references/design-system.md` — use it to preview what the design system looks like before generating artifacts.

**Key principles from the design system:**
- Warm editorial aesthetic: ivory background, clay accents, serif headings
- `1.5px` borders and `12px` radius are signature visual elements
- Three font families: serif (headings), sans (body), mono (code/labels)
- Syntax highlighting uses 4 span classes: `.kw` `.str` `.cm` `.fn` (no Prism.js)


## Constraints (never violate)

1. **Single file**: Everything in one `.html`. No external CSS/JS/images.
2. **Zero dependencies**: No frameworks, no libraries, no CDN links.
3. **Responsive**: Always include mobile breakpoints (1100px, 960px, 920px, 880px).
4. **Self-contained**: Demo data hardcoded in JS. No fetch calls.
5. **Semantic HTML**: Use `<article>`, `<section>`, `<aside>`, `<header>`, `<footer>`.
6. **Font smoothing**: Always include `-webkit-font-smoothing: antialiased`.

## Response Format

After generating the HTML, respond with:
1. A one-sentence summary of what was built and why this form was chosen
2. The classification decision (which content type and why)
3. Instructions on how to use it ("Open the file in your browser...")
4. Any interactive features and how they work

## Examples

**Exploration:**
User: "Compare 3 ways to handle errors in our API"
→ Classify: Exploration
→ Layout: `.layout-tri`, each option in `.panel`
→ Components: `.code-block` per option, `.chip` for metrics

**Report:**
User: "Summarize yesterday's outage"
→ Classify: Report
→ Layout: stacked `.panel` sections
→ Components: `.timeline`, `.data-table`, `.banner` for severity

**Editor:**
User: "I need to sort these tasks into priorities"
→ Classify: Editor
→ Layout: full-width with `.toolbar`
→ Components: drag-and-drop, `.btn` for export
