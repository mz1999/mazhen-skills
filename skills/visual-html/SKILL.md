---
name: visual-html
description: Generate rich, single-file HTML artifacts instead of markdown, automatically classifying content type and selecting a matching layout.
disable-model-invocation: true
argument-hint: "<content or topic to turn into HTML>"
---

# Visual HTML

Generate single-file HTML artifacts for any content, automatically selecting the right visual form based on content type.

## When to Use

Invoke this skill when you want to:
- Present information in a visually rich, shareable format
- Compare multiple options or solutions side by side
- Explain a complex system, flow, or codebase
- Create a report, status update, or incident timeline
- Build a throwaway interactive editor or prototype
- Replace a markdown document with something more readable

## Workflow

1. **Classify** the content into one of the 10 content types below.
   *Done:* you have named the single best-matching content type and stated why.

2. **Select** the matching layout and components from the content-type guide below.
   *Done:* you have listed the layout class and the components you will use.

3. **Read** `references/design-system.md` for the full CSS tokens and components.
   *Done:* you have copied the relevant tokens, layout, and component CSS into the HTML.

4. **Generate** a single-file HTML with all CSS inlined in `<style>`.
   *Done:* the file has no external CSS/JS/image links and meets every constraint in the Constraints section.

5. **Add interactivity** if the content type calls for it.
   *Done:* keyboard handlers or controls are wired and tested in the generated HTML, or you have confirmed the type is static.

## Step 1: Content Classification

Analyze the user's content and classify into the closest type. The content type determines everything that follows.

| Content Type | Reader's Goal | Classification Signals |
|-------------|--------------|------------------------|
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
- Decide on a plan or spec → Exploration (plan/spec branch)
- Follow a path → CodeUnderstanding / Diagram
- Watch something happen → Prototype
- Read and absorb → Report / Research
- Interact and export → Editor

## Step 2: Layout & Component Selection

For each content type, use the prescribed layout. Read `references/design-system.md` for full component CSS.

### Exploration
Two branches:
- **Compare options** — use `.layout-tri` or `.layout-quad` with one `.panel` per option.
- **Plan / spec** — use stacked `.panel` sections after a prompt box that captures the decision.
- **Components:** `.panel`, `.code-block`, `.chip`, `.prompt-box` (for plan/spec branch)
- **Structure:**
  - Compare branch: Header → Grid of options → Recommendation box (`.panel-subtle`, left border `--clay`)
  - Plan/spec branch: Header → Prompt box → Structured sections (Overview, Approach, Risks, Open questions)
- **Example (compare):** "Show 3 ways to handle API errors, side by side with tradeoffs"
- **Example (plan/spec):** "We picked the queue-based approach. Write an implementation plan with data model, API changes, migration steps, and open questions."

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
- **Export requirement:** Always end with an export — e.g., "Copy as JSON", "Copy as prompt", or "Copy diff" — that turns UI state back into something pasteable into Claude Code or commitable to a file.

## Step 3: CSS & Design System

`references/design-system.md` contains the complete CSS tokens, typography scale, layout patterns, and component styles. Copy the relevant sections into every generated HTML file.

**For human reference:** Open `assets/design-system.html` in a browser to see a live, browsable showcase of all tokens, components, and layout patterns. This is a visual companion to the CSS code in `references/design-system.md`.

**Design system at a glance:**
- Warm editorial aesthetic: ivory background, clay accents, serif headings
- `1.5px` borders and `12px` radius are signature visual elements
- Three font families: serif (headings), sans (body), mono (code/labels)
- Syntax highlighting uses 4 span classes: `.kw` `.str` `.cm` `.fn` (no Prism.js)

## Constraints

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

## When Markdown Still Makes Sense

HTML is the default for visual, spatial, comparable, or interactive content. If the output is a few lines of plain text or the user explicitly asks for `.md`, fall back to Markdown.

## Examples

**Exploration (compare):**
User: "I'm not sure what direction to take the onboarding screen. Generate 6 distinctly different approaches—vary layout, tone, and density—and lay them out as a single HTML file in a grid so I can compare them side by side. Label each with the tradeoff it's making."
→ Classify: Exploration
→ Branch: compare options
→ Layout: `.layout-quad` or `.layout-tri`
→ Components: `.panel` per approach, `.chip` for tradeoffs

**Exploration (plan/spec):**
User: "Create a thorough implementation plan in an HTML file. Include mockups, show data flow, and add important code snippets I might want to review. Make it easy to read and digest."
→ Classify: Exploration
→ Branch: plan/spec
→ Layout: stacked `.panel` sections
→ Components: `.prompt-box`, `.code-block`, SVG data-flow diagram

**CodeReview:**
User: "Help me review this PR by creating an HTML artifact that describes it. I'm not very familiar with the streaming/backpressure logic, so focus on that. Render the actual diff with inline margin annotations, color-code findings by severity, and whatever else might be needed to convey the concept well."
→ Classify: CodeReview
→ Layout: single column with margin annotations
→ Components: `.diff`, `.chip` for severity, `.panel-subtle` for notes

**Research / CodeUnderstanding:**
User: "I don't understand how our rate limiter actually works. Read the relevant code and produce a single HTML explainer page: a diagram of the token-bucket flow, the 3–4 key code snippets annotated, and a 'gotchas' section at the bottom. Optimize it for someone reading it once."
→ Classify: CodeUnderstanding (or Research if the goal is learning)
→ Layout: `.layout-split`
→ Components: SVG flowchart, `.code-block`, `.panel` for gotchas

**Editor:**
User: "I need to reprioritize these 30 Linear tickets. Make me an HTML file with each ticket as a draggable card across Now / Next / Later / Cut columns. Pre-sort them by your best guess. Add a 'copy as Markdown' button that exports the final ordering with a one-line rationale per bucket."
→ Classify: Editor
→ Layout: full-width with `.toolbar`
→ Components: drag-and-drop cards, `.btn` for "Copy as Markdown"
