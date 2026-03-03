---
name: article-illustrator-prompts
description: Analyzes article structure, identifies positions requiring visual aids, and generates illustration prompts using Type × Style two-dimension approach. Outputs ready-to-use drawing prompts without generating actual images. Use when user asks to "create illustration prompts", "generate prompts for article images", "article illustration prompts", or "文章配图提示词".
---

# Article Illustrator Prompts

Analyze articles, identify illustration positions, generate ready-to-use drawing prompts with Type × Style consistency.

## Two Dimensions

| Dimension | Controls | Examples |
|-----------|----------|----------|
| **Type** | Information structure | infographic, scene, flowchart, comparison, framework, timeline |
| **Style** | Visual aesthetics | notion, warm, minimal, blueprint, watercolor, elegant |

Combine freely: `--type infographic --style blueprint`

## Types

| Type | Best For |
|------|----------|
| `infographic` | Data, metrics, technical |
| `scene` | Narratives, emotional |
| `flowchart` | Processes, workflows |
| `comparison` | Side-by-side, options |
| `framework` | Models, architecture |
| `timeline` | History, evolution |

## Styles

See [references/styles.md](references/styles.md) for Core Styles, full gallery, and Type × Style compatibility.

## Workflow

```
- [ ] Step 1: Pre-check (EXTEND.md, references, config)
- [ ] Step 2: Analyze content
- [ ] Step 3: Confirm settings (AskUserQuestion)
- [ ] Step 4: Generate outline
- [ ] Step 5: Generate prompts
- [ ] Step 6: Finalize
```

### Step 1: Pre-check

**1.5 Load Preferences (EXTEND.md) ⛔ BLOCKING**

```bash
test -f .baoyu-skills/article-illustrator-prompts/EXTEND.md && echo "project"
test -f "$HOME/.baoyu-skills/article-illustrator-prompts/EXTEND.md" && echo "user"
```

| Result | Action |
|--------|--------|
| Found | Read, parse, display summary |
| Not found | ⛔ Run [first-time-setup](references/config/first-time-setup.md) |

Full procedures: [references/workflow.md](references/workflow.md#step-1-pre-check)

### Step 2: Analyze

| Analysis | Output |
|----------|--------|
| Content type | Technical / Tutorial / Methodology / Narrative |
| Purpose | information / visualization / imagination |
| Core arguments | 2-5 main points |
| Positions | Where illustrations add value |

**CRITICAL**: Metaphors → visualize underlying concept, NOT literal image.

Full procedures: [references/workflow.md](references/workflow.md#step-2-setup--analyze)

### Step 3: Confirm Settings ⚠️

**ONE AskUserQuestion, max 4 Qs. Q1-Q3 REQUIRED.**

| Q | Options |
|---|---------|
| **Q1: Type** | [Recommended], infographic, scene, flowchart, comparison, framework, timeline, mixed |
| **Q2: Density** | minimal (1-2), balanced (3-5), per-section (Recommended), rich (6+) |
| **Q3: Style** | [Recommended], minimal-flat, sci-fi, hand-drawn, editorial, scene, Other |
| Q4: Language | When article language ≠ EXTEND.md setting |

Full procedures: [references/workflow.md](references/workflow.md#step-3-confirm-settings-)

### Step 4: Generate Outline

Save `outline.md` with frontmatter (type, density, style, image_count) and entries:

```yaml
## Illustration 1
**Position**: [section/paragraph]
**Purpose**: [why]
**Visual Content**: [what]
**Filename**: 01-infographic-concept-name.md
```

Full template: [references/workflow.md](references/workflow.md#step-4-generate-outline)

### Step 5: Generate Prompts

⛔ **BLOCKING: Prompt files MUST be saved before completing.**

1. For each illustration, create a prompt file per [references/prompt-construction.md](references/prompt-construction.md)
2. Save to `prompts/NN-{type}-{slug}.md` with YAML frontmatter
3. Prompts **MUST** use type-specific templates with structured sections (ZONES / LABELS / COLORS / STYLE / ASPECT)
4. LABELS **MUST** include article-specific data: actual numbers, terms, metrics, quotes
5. Include reference processing if applicable (`direct`/`style`/`palette`)

Full procedures: [references/workflow.md](references/workflow.md#step-5-generate-prompts)

### Step 6: Finalize

Output prompt files list and usage instructions:

```
Article Illustration Prompts Complete!
Article: [path] | Type: [type] | Density: [level] | Style: [style]
Location: [directory]
Prompts: X generated

Prompt Files:
- prompts/01-{type}-{slug}.md → After "[Section]"
- prompts/02-{type}-{slug}.md → After "[Section]"

Usage:
Copy these prompts to your preferred image generation tool (Midjourney, DALL-E, Stable Diffusion, etc.)
```

## Output Directory

```
article-illustrator-prompts/{topic-slug}/
├── source-{slug}.{ext}
├── references/           # if provided
├── outline.md
└── prompts/
    ├── 01-{type}-{slug}.md
    ├── 02-{type}-{slug}.md
    └── ...
```

**Slug**: 2-4 words, kebab-case. **Conflict**: append `-YYYYMMDD-HHMMSS`.

## Modification

| Action | Steps |
|--------|-------|
| Edit | Update prompt → Update outline |
| Add | Position → Prompt → Update outline |
| Delete | Delete prompt file → Update outline |

## References

| File | Content |
|------|---------|
| [references/workflow.md](references/workflow.md) | Detailed procedures |
| [references/usage.md](references/usage.md) | Command syntax |
| [references/styles.md](references/styles.md) | Style gallery |
| [references/prompt-construction.md](references/prompt-construction.md) | Prompt templates |
| [references/config/first-time-setup.md](references/config/first-time-setup.md) | First-time setup |
