# Mazhen Skills

Personal skills collection for Claude Code.

## Installation

### Method 1: Add to Plugin Marketplace (Recommended)

```bash
/plugin marketplace add mz1999/mazhen-skills
```

Then install specific skills:

```bash
# Search skills
/plugin install searxng@mazhen-skills
/plugin install felo@mazhen-skills

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

### Search Skills

| Skill | Description |
|-------|-------------|
| **searxng** | Privacy-respecting metasearch using authenticated SearXNG instance |
| **felo** | AI-powered conversational search with real-time web results |

### Content Generation (Prompts Only)

| Skill | Description |
|-------|-------------|
| **xhs-prompts** | Xiaohongshu infographic prompts generator |
| **infographic-prompts** | Professional infographic drawing prompts generator |
| **cover-image-prompts** | Article cover image prompts generator |
| **article-illustrator-prompts** | Article illustration prompts generator |

### Diagram Generation

| Skill | Description |
|-------|-------------|
| **drawio** | Generate draw.io diagrams as .drawio files, export to PNG/SVG/PDF |

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
