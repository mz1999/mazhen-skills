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
├── defuddle/                      # Web page content extraction with proxy
├── felo-web-fetch/                # Web page content extraction
├── handoff/                       # Work continuity & context management
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

# Context management
/plugin install handoff@mazhen-skills

# Web content extraction with proxy support
/plugin install defuddle@mazhen-skills
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
| **defuddle** | Extract clean markdown from web pages with proxy support | `defuddle` (auto-triggered on URL) |
| **felo-web-fetch** | Extract web page content as markdown, HTML, or plain text | `/felo-web-fetch` |

### Context Management (Auto-triggered)

| Skill | Description | Trigger |
|-------|-------------|---------|
| **handoff** | Create and manage handoff documents for seamless work continuity | "create handoff", "save handoff", "继续工作", "load handoff" |

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

## Maintenance

### Defuddle Skill Updates

The `defuddle` skill includes a pre-built version of [mz1999/defuddle](https://github.com/mz1999/defuddle) (a fork with proxy support). The built files are located in `plugins/defuddle/skills/defuddle/scripts/dist/`.

#### Version History

| Skill Version | Defuddle Version | Date | Changes |
|---------------|------------------|------|---------|
| 1.0.0 | 0.14.0 | 2025-03-17 | Initial release with proxy support via `DEFUDDLE_PROXY` |

#### Quick Update (Using Script)

```bash
cd scripts
./update-defuddle.sh
```

This script will:
1. Clone the latest defuddle from GitHub
2. Install dependencies and build
3. Copy `dist/` files to the skill
4. Display the version number

After running the script:
1. Test: `export DEFUDDLE_PROXY=http://proxy:port && node defuddle.mjs parse https://example.com --md`
2. Update the version table above
3. Commit: `git add dist/ && git commit -m "Update defuddle to X.X.X"`

#### Manual Update

If the script doesn't work:

```bash
# 1. Clone and build
cd /tmp
git clone --depth 1 https://github.com/mz1999/defuddle.git
cd defuddle
npm install
npm run build

# 2. Copy dist files
rm -rf /path/to/mazhen-skills/plugins/defuddle/skills/defuddle/scripts/dist
cp -r dist /path/to/mazhen-skills/plugins/defuddle/skills/defuffle/scripts/

# 3. Update version table in README and commit
```

## Documentation

- [Plugin Marketplace Standard](docs/plugin-marketplace-standard.md) - How to add new skills

## License

MIT
