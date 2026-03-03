# Mazhen Skills

Personal skills collection for Claude Code.

## Installation

### Method 1: Add to Plugin Marketplace (Recommended)

```bash
/plugin marketplace add mz1999/mazhen-skills
```

Then install specific skill groups:

```bash
/plugin install search-skills@mazhen-skills
```

### Method 2: Direct Install

```bash
/plugin install search-skills@mz1999/mazhen-skills
```

## Available Skills

### Search Skills

- **searxng** - Privacy-respecting metasearch using authenticated SearXNG instance

### Content Generation (Prompts Only)

- **xhs-prompts** - Xiaohongshu infographic prompts generator
- **infographic-prompts** - Infographic prompts generator
- **cover-image-prompts** - Article cover image prompts generator
- **article-illustrator-prompts** - Article illustration prompts generator

## Attribution

以下技能是基于 [baoyu-skills](https://github.com/JimLiu/baoyu-skills) 复刻的提示词版本：

| 本仓库技能 | 来源技能 | 差异说明 |
|------------|----------|----------|
| `xhs-prompts` | `baoyu-xhs-images` | 只生成提示词，不生成图片 |
| `infographic-prompts` | `baoyu-infographic` | 只生成提示词，不生成图片 |
| `cover-image-prompts` | `baoyu-cover-image` | 只生成提示词，不生成图片 |
| `article-illustrator-prompts` | `baoyu-article-illustrator` | 只生成提示词，不生成图片 |

原 baoyu-skills 提供完整的图片生成功能，本项目仅保留提示词生成功能。

## Documentation

- [Plugin Marketplace Standard](docs/plugin-marketplace-standard.md) - How to add new skills

## License

MIT
