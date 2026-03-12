---
name: xhs-prompts
description: Generates drawing prompts for Xiaohongshu (Little Red Book) infographic series with 11 visual styles and 8 layouts. Breaks content into 1-10 cartoon-style image prompts optimized for XHS engagement. Use when user mentions "小红书提示词", "XHS prompts", "RedNote drawing prompts", "小红书绘图提示词", or wants AI image generation prompts for Chinese social media infographics.
disable-model-invocation: true
version: 1.56.1
metadata:
  source: baoyu-skills
---

# Xiaohongshu Infographic Prompt Generator

Break down complex content into drawing prompts for eye-catching infographic series for Xiaohongshu with multiple style options.

## Usage

```bash
# Auto-select style and layout based on content
/xhs-prompts posts/ai-future/article.md

# Specify style
/xhs-prompts posts/ai-future/article.md --style notion

# Specify layout
/xhs-prompts posts/ai-future/article.md --layout dense

# Combine style and layout
/xhs-prompts posts/ai-future/article.md --style notion --layout list

# Use preset (style + layout shorthand)
/xhs-prompts posts/ai-future/article.md --preset knowledge-card

# Preset with override
/xhs-prompts posts/ai-future/article.md --preset poster --layout quadrant

# Direct content input
/xhs-prompts
[paste content]

# Direct input with options
/xhs-prompts --style bold --layout comparison
[paste content]
```

## Options

| Option | Description |
|--------|-------------|
| `--style <name>` | Visual style (see Style Gallery) |
| `--layout <name>` | Information layout (see Layout Gallery) |
| `--preset <name>` | Style + layout shorthand (see [Style Presets](references/style-presets.md)) |

## Two Dimensions

| Dimension | Controls | Options |
|-----------|----------|---------|
| **Style** | Visual aesthetics: colors, lines, decorations | cute, fresh, warm, bold, minimal, retro, pop, notion, chalkboard, study-notes, screen-print |
| **Layout** | Information structure: density, arrangement | sparse, balanced, dense, list, comparison, flow, mindmap, quadrant |

Style × Layout can be freely combined. Example: `--style notion --layout dense` creates an intellectual-looking knowledge card with high information density.

Or use presets: `--preset knowledge-card` → style + layout in one flag. See [Style Presets](references/style-presets.md).

Style × Layout can be freely combined. Example: `--style notion --layout dense` creates an intellectual-looking knowledge card with high information density.

## Style Gallery

| Style | Description |
|-------|-------------|
| `cute` (Default) | Sweet, adorable, girly - classic Xiaohongshu aesthetic |
| `fresh` | Clean, refreshing, natural |
| `warm` | Cozy, friendly, approachable |
| `bold` | High impact, attention-grabbing |
| `minimal` | Ultra-clean, sophisticated |
| `retro` | Vintage, nostalgic, trendy |
| `pop` | Vibrant, energetic, eye-catching |
| `notion` | Minimalist hand-drawn line art, intellectual |
| `chalkboard` | Colorful chalk on black board, educational |
| `study-notes` | Realistic handwritten photo style, blue pen + red annotations + yellow highlighter |
| `screen-print` | Bold poster art, halftone textures, limited colors, symbolic storytelling |

Detailed style definitions: `references/presets/<style>.md`

## Preset Gallery

Quick-start presets by content scenario. Use `--preset <name>` or recommend during Step 2.

**Knowledge & Learning**:

| Preset | Style | Layout | Best For |
|--------|-------|--------|----------|
| `knowledge-card` | notion | dense | 干货知识卡、概念科普 |
| `checklist` | notion | list | 清单、排行榜、必备清单 |
| `concept-map` | notion | mindmap | 概念图、知识脉络 |
| `swot` | notion | quadrant | SWOT分析、四象限分类 |
| `tutorial` | chalkboard | flow | 教程步骤、操作流程 |
| `classroom` | chalkboard | balanced | 课堂笔记、知识讲解 |
| `study-guide` | study-notes | dense | 学习笔记、考试重点 |

**Lifestyle & Sharing**:

| Preset | Style | Layout | Best For |
|--------|-------|--------|----------|
| `cute-share` | cute | balanced | 少女风分享、日常种草 |
| `girly` | cute | sparse | 甜美封面、氛围感 |
| `cozy-story` | warm | balanced | 生活故事、情感分享 |
| `product-review` | fresh | comparison | 产品对比、测评 |
| `nature-flow` | fresh | flow | 健康流程、自然主题 |

**Impact & Opinion**:

| Preset | Style | Layout | Best For |
|--------|-------|--------|----------|
| `warning` | bold | list | 避坑指南、重要提醒 |
| `versus` | bold | comparison | 正反对比、强烈对照 |
| `clean-quote` | minimal | sparse | 金句、极简封面 |
| `pro-summary` | minimal | balanced | 专业总结、商务内容 |

**Trend & Entertainment**:

| Preset | Style | Layout | Best For |
|--------|-------|--------|----------|
| `retro-ranking` | retro | list | 复古排行、经典盘点 |
| `throwback` | retro | balanced | 怀旧分享、老物件 |
| `pop-facts` | pop | list | 趣味冷知识、好玩的事 |
| `hype` | pop | sparse | 炸裂封面、惊叹分享 |

**Poster & Editorial**:

| Preset | Style | Layout | Best For |
|--------|-------|--------|----------|
| `poster` | screen-print | sparse | 海报风封面、影评书评 |
| `editorial` | screen-print | balanced | 观点文章、文化评论 |
| `cinematic` | screen-print | comparison | 电影对比、戏剧张力 |

Full preset definitions: [references/style-presets.md](references/style-presets.md)

## Layout Gallery

| Layout | Description |
|--------|-------------|
| `sparse` (Default) | Minimal information, maximum impact (1-2 points) |
| `balanced` | Standard content layout (3-4 points) |
| `dense` | High information density, knowledge card style (5-8 points) |
| `list` | Enumeration and ranking format (4-7 items) |
| `comparison` | Side-by-side contrast layout |
| `flow` | Process and timeline layout (3-6 steps) |
| `mindmap` | Center radial mind map layout (4-8 branches) |
| `quadrant` | Four-quadrant / circular section layout |

Detailed layout definitions: `references/elements/canvas.md`

## Auto Selection

| Content Signals | Style | Layout |
|-----------------|-------|--------|
| Beauty, fashion, cute, girl, pink | `cute` | sparse/balanced |
| Health, nature, clean, fresh, organic | `fresh` | balanced/flow |
| Life, story, emotion, feeling, warm | `warm` | balanced |
| Warning, important, must, critical | `bold` | list/comparison |
| Professional, business, elegant, simple | `minimal` | sparse/balanced |
| Classic, vintage, old, traditional | `retro` | balanced |
| Fun, exciting, wow, amazing | `pop` | sparse/list |
| Knowledge, concept, productivity, SaaS | `notion` | dense/list |
| Education, tutorial, learning, teaching, classroom | `chalkboard` | balanced/dense |
| Notes, handwritten, study guide, knowledge, realistic, photo | `study-notes` | dense/list/mindmap |
| Movie, album, concert, poster, opinion, editorial, dramatic, cinematic | `screen-print` | sparse/comparison | `poster`, `editorial`, `cinematic` |

## Outline Strategies

Three differentiated outline strategies for different content goals:

### Strategy A: Story-Driven (故事驱动型)

| Aspect | Description |
|--------|-------------|
| **Concept** | Personal experience as main thread, emotional resonance first |
| **Features** | Start from pain point, show before/after change, strong authenticity |
| **Best for** | Reviews, personal shares, transformation stories |
| **Structure** | Hook → Problem → Discovery → Experience → Conclusion |

### Strategy B: Information-Dense (信息密集型)

| Aspect | Description |
|--------|-------------|
| **Concept** | Value-first, efficient information delivery |
| **Features** | Clear structure, explicit points, professional credibility |
| **Best for** | Tutorials, comparisons, product reviews, checklists |
| **Structure** | Core conclusion → Info card → Pros/Cons → Recommendation |

### Strategy C: Visual-First (视觉优先型)

| Aspect | Description |
|--------|-------------|
| **Concept** | Visual impact as core, minimal text |
| **Features** | Large images, atmospheric, instant appeal |
| **Best for** | High-aesthetic products, lifestyle, mood-based content |
| **Structure** | Hero image → Detail shots → Lifestyle scene → CTA |

## File Structure

Each session creates an independent directory named by content slug:

```
xhs-prompts/{topic-slug}/
├── source-{slug}.{ext}             # Source files (text, images, etc.)
├── analysis.md                     # Deep analysis + questions asked
├── outline-strategy-a.md           # Strategy A: Story-driven
├── outline-strategy-b.md           # Strategy B: Information-dense
├── outline-strategy-c.md           # Strategy C: Visual-first
├── outline.md                      # Final selected/merged outline
└── prompts/
    ├── 01-cover-[slug].md
    ├── 02-content-[slug].md
    └── ...
```

**Slug Generation**:
1. Extract main topic from content (2-4 words, kebab-case)
2. Example: "AI工具推荐" → `ai-tools-recommend`

**Conflict Resolution**:
If `xhs-prompts/{topic-slug}/` already exists:
- Append timestamp: `{topic-slug}-YYYYMMDD-HHMMSS`
- Example: `ai-tools` exists → `ai-tools-20260118-143052`

**Source Files**:
Copy all sources with naming `source-{slug}.{ext}`:
- `source-article.md`, `source-photo.jpg`, etc.
- Multiple sources supported: text, images, files from conversation

## Workflow

### Progress Checklist

```
XHS Prompt Generation Progress:
- [ ] Step 0: Check preferences (EXTEND.md) ⛔ BLOCKING
  - [ ] Found → load preferences → continue
  - [ ] Not found → run first-time setup → MUST complete before Step 1
- [ ] Step 1: Analyze content → analysis.md
- [ ] Step 2: Smart Confirm ⚠️ REQUIRED
  - [ ] Path A: Quick confirm → generate recommended outline
  - [ ] Path B: Customize → adjust then generate outline
  - [ ] Path C: Detailed → 3 outlines → second confirm → generate outline
- [ ] Step 3: Generate prompts
- [ ] Step 4: Completion report
```

### Flow

```
Input → [Step 0: Preferences] ─┬─ Found → Continue
                               │
                               └─ Not found → First-Time Setup ⛔ BLOCKING
                                              │
                                              └─ Complete setup → Save EXTEND.md → Continue
                                                                                      │
        ┌───────────────────────────────────────────────────────────────────────────┘
        ↓
Analyze → [Smart Confirm] ─┬─ Quick: confirm recommended → outline.md → Generate → Complete
                           │
                           ├─ Customize: adjust options → outline.md → Generate → Complete
                           │
                           └─ Detailed: 3 outlines → [Confirm 2] → outline.md → Generate → Complete
```

### Step 0: Load Preferences (EXTEND.md) ⛔ BLOCKING

**Purpose**: Load user preferences or run first-time setup.

**CRITICAL**: If EXTEND.md not found, MUST complete first-time setup before ANY other questions or steps. Do NOT proceed to content analysis, do NOT ask about style, do NOT ask about layout — ONLY complete the preferences setup first.

Check EXTEND.md existence (priority order):

```bash
# macOS, Linux, WSL, Git Bash
test -f .baoyu-skills/xhs-prompts/EXTEND.md && echo "project"
test -f "${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/xhs-prompts/EXTEND.md" && echo "xdg"
test -f "$HOME/.baoyu-skills/xhs-prompts/EXTEND.md" && echo "user"
```

```powershell
# PowerShell (Windows)
if (Test-Path .baoyu-skills/xhs-prompts/EXTEND.md) { "project" }
$xdg = if ($env:XDG_CONFIG_HOME) { $env:XDG_CONFIG_HOME } else { "$HOME/.config" }
if (Test-Path "$xdg/baoyu-skills/xhs-prompts/EXTEND.md") { "xdg" }
if (Test-Path "$HOME/.baoyu-skills/xhs-prompts/EXTEND.md") { "user" }
```

┌────────────────────────────────────────────────────┬───────────────────┐
│                        Path                        │     Location      │
├────────────────────────────────────────────────────┼───────────────────┤
│ .baoyu-skills/xhs-prompts/EXTEND.md                │ Project directory │
├────────────────────────────────────────────────────┼───────────────────┤
│ $XDG_CONFIG_HOME/baoyu-skills/xhs-prompts/...      │ XDG config        │
├────────────────────────────────────────────────────┼───────────────────┤
│ $HOME/.baoyu-skills/xhs-prompts/EXTEND.md          │ User home         │
└────────────────────────────────────────────────────┴───────────────────┘

┌───────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  Result   │                                              Action                                              │
├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Found     │ Read, parse, display summary → Continue to Step 1                                                 │
├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Not found │ ⛔ BLOCKING: Run first-time setup ONLY (see below) → Complete and save EXTEND.md → Then Step 1    │
└───────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────┘

**First-Time Setup** (when EXTEND.md not found):

**Language**: Use user's input language or saved language preference.

Use AskUserQuestion with ALL questions in ONE call. See `references/config/first-time-setup.md` for question details.

**EXTEND.md Supports**: Watermark | Preferred style/layout | Custom style definitions | Language preference

Schema: `references/config/preferences-schema.md`

### Step 1: Analyze Content → `analysis.md`

Read source content, save it if needed, and perform deep analysis.

**Actions**:
1. **Save source content** (if not already a file):
   - If user provides a file path: use as-is
   - If user pastes content: save to `source.md` in target directory
   - **Backup rule**: If `source.md` exists, rename to `source-backup-YYYYMMDD-HHMMSS.md`
2. Read source content
3. **Deep analysis** following `references/workflows/analysis-framework.md`:
   - Content type classification (种草/干货/测评/教程/避坑...)
   - Hook analysis (爆款标题潜力)
   - Target audience identification
   - Engagement potential (收藏/分享/评论)
   - Visual opportunity mapping
   - Swipe flow design
4. Detect source language
5. Determine recommended image count (2-10)
6. **Generate clarifying questions** (see Step 2)
7. **Save to `analysis.md`**

### Step 2: Smart Confirm ⚠️

**Purpose**: Present auto-recommended plan, let user confirm or adjust. **Do NOT skip.**

**Auto-Recommendation Logic**:
1. Use Auto Selection table to match content signals → best strategy + style + layout
2. Infer optimal image count from content density
3. Load style's default elements from preset

**Display** (analysis summary + recommended plan):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 内容分析
  主题：[topic] | 类型：[content_type]
  要点：[key points summary]
  受众：[target audience]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 推荐方案（自动匹配）
  策略：[A/B/C] [strategy name]（[reason]）
  风格：[style] · 布局：[layout] · 预设：[preset]
  图片：[N]张（封面+[N-2]内容+结尾）
  元素：[background] / [decorations] / [emphasis]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Use AskUserQuestion** with single question:

| Option | Description |
|--------|-------------|
| 1. ✅ 确认，直接生成（推荐） | Trust auto-recommendation, proceed immediately |
| 2. 🎛️ 自定义调整 | Modify strategy/style/layout/count in one step |
| 3. 📋 详细模式 | Generate 3 outlines, then choose (two confirmations) |

#### Path A: Quick Confirm (Option 1)

Generate single outline using recommended strategy + style → save to `outline.md` → Step 3.

#### Path B: Customize (Option 2)

**Use AskUserQuestion** with adjustable options (leave blank = keep recommended):

1. **策略风格**: Current: [strategy + style]. Options: A Story-Driven(warm) | B Information-Dense(notion) | C Visual-First(screen-print). Or specify style directly: cute/fresh/warm/bold/minimal/retro/pop/notion/chalkboard/study-notes/screen-print. Or use preset: knowledge-card / checklist / tutorial / poster / cinematic / etc.
2. **布局**: Current: [layout]. Options: sparse | balanced | dense | list | comparison | flow | mindmap | quadrant
3. **图片数量**: Current: [N]. Range: 2-10
4. **补充说明**（可选）: Selling point emphasis, audience adjustment, color preference, etc.

**After response**: Generate single outline with user's choices → save to `outline.md` → Step 3.

#### Path C: Detailed Mode (Option 3)

Full two-confirmation flow for maximum control:

**Step 2a: Content Understanding**

**Use AskUserQuestion** for:
1. Core selling point (multiSelect: true)
2. Target audience
3. Style preference: Authentic sharing / Professional review / Aesthetic mood / Auto
4. Additional context (optional)

**After response**: Update `analysis.md`.

**Step 2b: Generate 3 Outline Variants**

| Strategy | Filename | Outline | Recommended Style |
|----------|----------|---------|-------------------|
| A | `outline-strategy-a.md` | Story-driven: emotional, before/after | warm, cute, fresh |
| B | `outline-strategy-b.md` | Information-dense: structured, factual | notion, minimal, chalkboard |
| C | `outline-strategy-c.md` | Visual-first: atmospheric, minimal text | bold, pop, retro, screen-print |

**Outline format** (YAML front matter + content):
```yaml
---
strategy: a  # a, b, or c
name: Story-Driven
style: warm  # recommended style for this strategy
style_reason: "Warm tones enhance emotional storytelling and personal connection"
elements:  # from style preset, can be customized
  background: solid-pastel
  decorations: [clouds, stars-sparkles]
  emphasis: star-burst
  typography: highlight
layout: balanced  # primary layout
image_count: 5
---

## P1 Cover
**Type**: cover
**Hook**: "入冬后脸不干了🥹终于找到对的面霜"
**Visual**: Product hero shot with cozy winter atmosphere
**Layout**: sparse

## P2 Problem
**Type**: pain-point
**Message**: Previous struggles with dry skin
**Visual**: Before state, relatable scenario
**Layout**: balanced

...
```

**Differentiation requirements**:
- Each strategy MUST have different outline structure AND different recommended style
- Adapt page count: A typically 4-6, B typically 3-5, C typically 3-4
- Include `style_reason` explaining why this style fits the strategy

Reference: `references/workflows/outline-template.md`

**Step 2c: Outline & Style Selection**

**Use AskUserQuestion** with three questions:

**Q1: Outline Strategy**: A / B / C / Combine (specify pages from each)

**Q2: Visual Style**: Use recommended | Select preset | Select style | Custom description

**Q3: Visual Elements**: Use defaults (Recommended) | Adjust background | Adjust decorations | Custom

**After response**: Save selected/merged outline to `outline.md` with confirmed style and elements → Step 3.

### Step 3: Generate Prompts

With confirmed outline + style + layout:

**For each image (cover + content + ending)**:
1. Assemble complete drawing prompt following `references/workflows/prompt-assembly.md`
2. Save prompt to `prompts/NN-{type}-[slug].md` (in user's preferred language)
   - **Backup rule**: If prompt file exists, rename to `prompts/NN-{type}-[slug]-backup-YYYYMMDD-HHMMSS.md`
3. Report progress after each prompt is saved

**Prompt Structure**:
Each saved prompt file contains:
```markdown
---
image_number: 01
type: cover
slug: [topic-slug]
style: [selected-style]
layout: [layout-name]
generated_at: YYYY-MM-DD HH:MM:SS
---

# Drawing Prompt for Image 01 - Cover

[Complete assembled prompt following prompt-assembly.md structure]
```

**Watermark Guidance** (if enabled in preferences):
Include in each prompt:
```
## Watermark
Include a subtle watermark "[content]" positioned at [position].
The watermark should be legible but not distracting from the main content.
```
Reference: `references/config/watermark-guide.md`

**Visual Consistency Tips**:
Since prompts are for a series of related images, include at the end of each prompt file:
```markdown
## Visual Consistency Notes

- Use the same [style] visual style throughout the series
- Maintain consistent color palette: [colors from preset]
- Apply similar hand-drawn quality and illustration approach
- Keep typography style consistent with [typography style]
```

### Step 6: Completion Report

```
Xiaohongshu Infographic Prompts Complete!

Topic: [topic]
Strategy: [A/B/C/Combined]
Style: [style name]
Layout: [layout name or "varies"]
Location: [directory path]
Prompts: N total

✓ analysis.md
✓ outline-strategy-a.md
✓ outline-strategy-b.md
✓ outline-strategy-c.md
✓ outline.md (selected: [strategy])

Prompt Files:
- prompts/01-cover-[slug].md ✓ Cover (sparse)
- prompts/02-content-[slug].md ✓ Content (balanced)
- prompts/03-content-[slug].md ✓ Content (dense)
- prompts/04-ending-[slug].md ✓ Ending (sparse)

Preview (first 3 prompts):
[Show first 200 characters of each prompt]
```

## Prompt Modification

| Action | Steps |
|--------|-------|
| **Edit** | **Update prompt file directly** → Save changes |
| **Add** | Specify position → Create prompt → Save → Renumber subsequent files (NN+1) → Update outline |
| **Delete** | Remove files → Renumber subsequent (NN-1) → Update outline |

**IMPORTANT**: Prompt files are the final output. Edit them directly to refine the drawing instructions before using with your preferred image generation tool.

## Using the Prompts

These prompts are designed to work with various AI image generation tools:

| Tool | Usage |
|------|-------|
| Midjourney | Copy prompt text, add `--ar 3:4` for aspect ratio |
| DALL-E 3 | Use prompt as-is, specify 3:4 aspect ratio if supported |
| Stable Diffusion | Use prompt with appropriate model checkpoint |
| Gemini/Imagen | Use prompt with image generation skill |

**Recommended workflow**:
1. Review generated prompts in `prompts/` directory
2. Copy prompts to your preferred AI image tool
3. Generate images one by one for visual consistency
4. Use Image 1 (cover) as a style reference for subsequent images

## Content Breakdown Principles

1. **Cover (Image 1)**: Hook + visual impact → `sparse` layout
2. **Content (Middle)**: Core value per image → `balanced`/`dense`/`list`/`comparison`/`flow`
3. **Ending (Last)**: CTA / summary → `sparse` or `balanced`

**Style × Layout Matrix** (✓✓ = highly recommended, ✓ = works well):

| | sparse | balanced | dense | list | comparison | flow | mindmap | quadrant |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| cute | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ |
| fresh | ✓✓ | ✓✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ |
| warm | ✓✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ |
| bold | ✓✓ | ✓ | ✓ | ✓✓ | ✓✓ | ✓ | ✓ | ✓✓ |
| minimal | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| retro | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ |
| pop | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓ | ✓ | ✓ |
| notion | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ |
| chalkboard | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓ |
| study-notes | ✗ | ✓ | ✓✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓ |
| screen-print | ✓✓ | ✓✓ | ✗ | ✓ | ✓✓ | ✓ | ✗ | ✓✓ |

## References

Detailed templates in `references/` directory:

**Elements** (Visual building blocks):
- `elements/canvas.md` - Aspect ratios, safe zones, grid layouts
- `elements/image-effects.md` - Cutout, stroke, filters
- `elements/typography.md` - Decorated text (花字), tags, text direction
- `elements/decorations.md` - Emphasis marks, backgrounds, doodles, frames

**Presets** (Style presets):
- `presets/<name>.md` - Element combination definitions (cute, notion, warm...)

**Workflows** (Process guides):
- `workflows/analysis-framework.md` - Content analysis framework
- `workflows/outline-template.md` - Outline template with layout guide
- `workflows/prompt-assembly.md` - Prompt assembly guide

**Config** (Settings):
- `config/preferences-schema.md` - EXTEND.md schema
- `config/first-time-setup.md` - First-time setup flow
- `config/watermark-guide.md` - Watermark configuration

## Notes

- Use confirmed language preference | Maintain style consistency
- **Two confirmation points required** (Steps 2 & 4) - do not skip
- Prompts are optimized for hand-drawn, cartoon-style infographics
- All prompts include guidance for visual consistency across the series

## Extension Support

Custom configurations via EXTEND.md. See **Step 0** for paths and supported options.
