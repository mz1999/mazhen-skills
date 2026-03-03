---
name: cover-image-prompts
description: Generates article cover image prompts with 5 dimensions (type, palette, rendering, text, mood) combining 9 color palettes and 6 rendering styles. Outputs only the generation prompt to a file, not the actual image. Use when user asks to "generate cover prompt", "create cover image prompt", or "make cover prompt".
---

# Cover Image Prompt Generator

Generate elegant cover image prompts for articles with 5-dimensional customization. Outputs the prompt to a file for later use with any image generation tool.

## Usage

```bash
# Auto-select dimensions based on content
/cover-image-prompts path/to/article.md

# Quick mode: skip confirmation
/cover-image-prompts article.md --quick

# Specify dimensions
/cover-image-prompts article.md --type conceptual --palette warm --rendering flat-vector

# Style presets (shorthand for palette + rendering)
/cover-image-prompts article.md --style blueprint

# With reference images
/cover-image-prompts article.md --ref style-ref.png

# Direct content input
/cover-image-prompts --palette mono --aspect 1:1 --quick
[paste content]
```

## Options

| Option | Description |
|--------|-------------|
| `--type <name>` | hero, conceptual, typography, metaphor, scene, minimal |
| `--palette <name>` | warm, elegant, cool, dark, earth, vivid, pastel, mono, retro |
| `--rendering <name>` | flat-vector, hand-drawn, painterly, digital, pixel, chalk |
| `--style <name>` | Preset shorthand (see [Style Presets](references/style-presets.md)) |
| `--text <level>` | none, title-only, title-subtitle, text-rich |
| `--mood <level>` | subtle, balanced, bold |
| `--font <name>` | clean, handwritten, serif, display |
| `--aspect <ratio>` | 16:9 (default), 2.35:1, 4:3, 3:2, 1:1, 3:4 |
| `--lang <code>` | Title language (en, zh, ja, etc.) |
| `--no-title` | Alias for `--text none` |
| `--quick` | Skip confirmation, use auto-selection |
| `--ref <files...>` | Reference images for style/composition guidance |

## Five Dimensions

| Dimension | Values | Default |
|-----------|--------|---------|
| **Type** | hero, conceptual, typography, metaphor, scene, minimal | auto |
| **Palette** | warm, elegant, cool, dark, earth, vivid, pastel, mono, retro | auto |
| **Rendering** | flat-vector, hand-drawn, painterly, digital, pixel, chalk | auto |
| **Text** | none, title-only, title-subtitle, text-rich | title-only |
| **Mood** | subtle, balanced, bold | balanced |
| **Font** | clean, handwritten, serif, display | clean |

Auto-selection rules: [references/auto-selection.md](references/auto-selection.md)

## Galleries

**Types**: hero, conceptual, typography, metaphor, scene, minimal
→ Details: [references/types.md](references/types.md)

**Palettes**: warm, elegant, cool, dark, earth, vivid, pastel, mono, retro
→ Details: [references/palettes/](references/palettes/)

**Renderings**: flat-vector, hand-drawn, painterly, digital, pixel, chalk
→ Details: [references/renderings/](references/renderings/)

**Text Levels**: none (pure visual) | title-only (default) | title-subtitle | text-rich (with tags)
→ Details: [references/dimensions/text.md](references/dimensions/text.md)

**Mood Levels**: subtle (low contrast) | balanced (default) | bold (high contrast)
→ Details: [references/dimensions/mood.md](references/dimensions/mood.md)

**Fonts**: clean (sans-serif) | handwritten | serif | display (bold decorative)
→ Details: [references/dimensions/font.md](references/dimensions/font.md)

## File Structure

Output directory per `default_output_dir` preference:
- `same-dir`: `{article-dir}/`
- `imgs-subdir`: `{article-dir}/imgs/`
- `independent` (default): `cover-image-prompts/{topic-slug}/`

```
<output-dir>/
├── source-{slug}.{ext}    # Source files
├── refs/                  # Reference images (if provided)
│   ├── ref-01-{slug}.{ext}
│   └── ref-01-{slug}.md   # Description file
└── prompts/
    └── cover.md           # Generation prompt (only output)
```

**Slug**: 2-4 words, kebab-case. Conflict: append `-YYYYMMDD-HHMMSS`

## Workflow

### Progress Checklist

```
Cover Prompt Progress:
- [ ] Step 0: Check preferences (EXTEND.md) ⛔ BLOCKING
- [ ] Step 1: Analyze content + save refs + determine output dir
- [ ] Step 2: Confirm options (6 dimensions) ⚠️ unless --quick
- [ ] Step 3: Create prompt
- [ ] Step 4: Save prompt to file
- [ ] Step 5: Completion report
```

### Flow

```
Input → [Step 0: Preferences] ─┬─ Found → Continue
                               └─ Not found → First-Time Setup ⛔ BLOCKING → Save EXTEND.md → Continue
        ↓
Analyze + Save Refs → [Output Dir] → [Confirm: 6 Dimensions] → Prompt → Save → Complete
                                              ↓
                                     (skip if --quick or all specified)
```

### Step 0: Load Preferences ⛔ BLOCKING

Check EXTEND.md existence (priority: project → user):
```bash
test -f .baoyu-skills/cover-image-prompts/EXTEND.md && echo "project"
test -f "$HOME/.baoyu-skills/cover-image-prompts/EXTEND.md" && echo "user"
```

| Result | Action |
|--------|--------|
| Found | Load, display summary → Continue |
| Not found | ⛔ Run first-time setup ([references/config/first-time-setup.md](references/config/first-time-setup.md)) → Save → Continue |

**CRITICAL**: If not found, complete setup BEFORE any other steps or questions.

### Step 1: Analyze Content

1. **Save reference images** (if provided) → [references/workflow/reference-images.md](references/workflow/reference-images.md)
2. **Save source content** (if pasted, save to `source.md`)
3. **Analyze content**: topic, tone, keywords, visual metaphors
4. **Deep analyze references** ⚠️: Extract specific, concrete elements (see reference-images.md)
5. **Detect language**: Compare source, user input, EXTEND.md preference
6. **Determine output directory**: Per File Structure rules

### Step 2: Confirm Options ⚠️

Full confirmation flow: [references/workflow/confirm-options.md](references/workflow/confirm-options.md)

| Condition | Skipped | Still Asked |
|-----------|---------|-------------|
| `--quick` or `quick_mode: true` | 6 dimensions | Aspect ratio (unless `--aspect`) |
| All 6 + `--aspect` specified | All | None |

### Step 3: Create Prompt

Assemble the generation prompt. Template: [references/workflow/prompt-template.md](references/workflow/prompt-template.md)

**CRITICAL - References in Frontmatter**:
- Files saved to `refs/` → Add to frontmatter `references` list
- Style extracted verbally (no file) → Omit `references`, describe in body
- Before writing → Verify: `test -f refs/ref-NN-{slug}.{ext}`

**Reference elements in body** MUST be detailed, prefixed with "MUST"/"REQUIRED", with integration approach.

### Step 4: Save Prompt to File

1. **Create output directory** if not exists
2. **Save prompt** to `prompts/cover.md` with frontmatter and body
3. Include all selected dimensions in frontmatter for reference

### Step 5: Completion Report

```
Cover Prompt Generated!

Topic: [topic]
Type: [type] | Palette: [palette] | Rendering: [rendering]
Text: [text] | Mood: [mood] | Font: [font] | Aspect: [ratio]
Title: [title or "visual only"]
Language: [lang]
References: [N images or "extracted style" or "none"]
Location: [directory path]

Files:
✓ source-{slug}.{ext}
✓ prompts/cover.md

Usage:
Use the generated prompt with any image generation tool (e.g., Midjourney, DALL-E, Stable Diffusion).
The prompt file contains the full generation instructions in the body section.
```

## Using the Generated Prompt

The `prompts/cover.md` file contains:
- **Frontmatter**: Metadata about dimensions, title, aspect ratio, references
- **Body**: The complete generation prompt to use with image generation tools

To generate the actual image:
1. Open `prompts/cover.md`
2. Copy the body content (below the frontmatter)
3. Paste into your preferred image generation tool
4. Add any reference images if specified in frontmatter

## Prompt Modification

| Action | Steps |
|--------|-------|
| **Regenerate prompt** | Update dimensions → Overwrite `prompts/cover.md` |
| **Change dimension** | Confirm new value → Update prompt → Save |

## Composition Principles

- **Whitespace**: 40-60% breathing room
- **Visual anchor**: Main element centered or offset left
- **Characters**: Simplified silhouettes; NO realistic humans
- **Title**: Use exact title from user/source; never invent

## Extension Support

Custom configurations via EXTEND.md. See **Step 0** for paths.

Supports: Preferred dimensions | Default aspect/output | Quick mode | Custom palettes | Language

Schema: [references/config/preferences-schema.md](references/config/preferences-schema.md)

## References

**Dimensions**: [text.md](references/dimensions/text.md) | [mood.md](references/dimensions/mood.md) | [font.md](references/dimensions/font.md)
**Palettes**: [references/palettes/](references/palettes/)
**Renderings**: [references/renderings/](references/renderings/)
**Types**: [references/types.md](references/types.md)
**Auto-Selection**: [references/auto-selection.md](references/auto-selection.md)
**Style Presets**: [references/style-presets.md](references/style-presets.md)
**Compatibility**: [references/compatibility.md](references/compatibility.md)
**Visual Elements**: [references/visual-elements.md](references/visual-elements.md)
**Workflow**: [confirm-options.md](references/workflow/confirm-options.md) | [prompt-template.md](references/workflow/prompt-template.md) | [reference-images.md](references/workflow/reference-images.md)
**Config**: [preferences-schema.md](references/config/preferences-schema.md) | [first-time-setup.md](references/config/first-time-setup.md)
