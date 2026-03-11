# Mazhen Skills

Personal skills collection for Claude Code.

## Structure

Each skill is packaged as an independent plugin in the `plugins/` directory:

```
plugins/
├── article-illustrator-prompts/   # Article illustration prompts
├── cover-image-prompts/           # Cover image prompts
├── drawio/                        # Draw.io diagram generation
├── felo-search/                   # Felo AI web search
├── felo-web-fetch/                # Web page content extraction
├── infographic-prompts/           # Infographic prompts
├── searxng/                       # SearXNG metasearch
└── xhs-prompts/                   # Xiaohongshu prompts
```

This structure allows each skill to be installed and enabled independently.

## Installation

### Method 1: Add to Plugin Marketplace (Recommended)

```bash
/plugin marketplace add mz1999/mazhen-skills
```

Then install specific skills:

```bash
# Search skills
/plugin install searxng@mazhen-skills
/plugin install felo-search@mazhen-skills

# Content generation prompts
/plugin install xhs-prompts@mazhen-skills
/plugin install infographic-prompts@mazhen-skills
/plugin install cover-image-prompts@mazhen-skills
/plugin install article-illustrator-prompts@mazhen-skills

# Diagram generation
/plugin install drawio@mazhen-skills
```

### Method 2: Direct Install

```bash
/plugin install searxng@mz1999/mazhen-skills
```

## Available Skills

### Search Skills (Auto-triggered)

The following skills are automatically triggered when Claude detects a relevant request:

| Skill | Description |
|-------|-------------|
| **searxng** | Privacy-respecting metasearch using authenticated SearXNG instance |
| **felo** | AI-powered conversational search with real-time web results |

### Content Generation (Manual Invocation)

The following skills require manual invocation using `/skill-name`:

| Skill | Description | Command |
|-------|-------------|---------|
| **xhs-prompts** | Xiaohongshu infographic prompts generator | `/xhs-prompts` |
| **infographic-prompts** | Professional infographic drawing prompts generator | `/infographic-prompts` |
| **cover-image-prompts** | Article cover image prompts generator | `/cover-image-prompts` |
| **article-illustrator-prompts** | Article illustration prompts generator | `/article-illustrator-prompts` |

### Diagram Generation (Manual Invocation)

| Skill | Description | Command |
|-------|-------------|---------|
| **drawio** | Generate draw.io diagrams as .drawio files, export to PNG/SVG/PDF | `/drawio` |

### Web Content Extraction (Manual Invocation)

| Skill | Description | Command |
|-------|-------------|---------|
| **felo-web-fetch** | Extract web page content as markdown, HTML, or plain text | `/felo-web-fetch` |

## Attribution

以下技能是基于 [baoyu-skills](https://github.com/JimLiu/baoyu-skills) 复刻的提示词版本：

| 本仓库技能 | 来源技能 | 差异说明 |
|------------|----------|----------|
| `xhs-prompts` | `baoyu-xhs-images` | 只生成提示词，不生成图片 |
| `infographic-prompts` | `baoyu-infographic` | 只生成提示词，不生成图片 |
| `cover-image-prompts` | `baoyu-cover-image` | 只生成提示词，不生成图片 |
| `article-illustrator-prompts` | `baoyu-article-illustrator` | 只生成提示词，不生成图片 |

原 baoyu-skills 提供完整的图片生成功能，本项目仅保留提示词生成功能。

### drawio

`drawio` skill 来自 [drawio-mcp](https://github.com/jgraph/drawio-mcp) 项目，是一个纯提示词类型的 skill，用于生成 draw.io 图表文件。

## Documentation

- [Plugin Marketplace Standard](docs/plugin-marketplace-standard.md) - How to add new skills

## License

MIT
