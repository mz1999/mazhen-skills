# Claude Code 插件市场标准文档

本文档说明如何将 skills 发布到 Claude Code 插件市场，让用户可以通过 `/plugin marketplace add username/repo-name` 命令安装。

## 概述

Claude Code 支持从 GitHub 仓库加载 skills 集合，称为"插件市场"。通过标准化的配置，用户可以方便地发现和安装多个相关的 skills。

## 仓库结构要求

```
your-skills-repo/
├── .claude-plugin/
│   └── marketplace.json          # 插件市场清单（必需）
├── plugins/                       # 插件目录
│   ├── plugin-a/                  # 每个插件独立目录
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json        # 插件配置（必需）
│   │   └── skills/
│   │       └── skill-name/
│   │           ├── SKILL.md       # Skill 定义文件（必需）
│   │           ├── scripts/       # 实现脚本（可选）
│   │           └── ...            # 其他资源文件
│   └── plugin-b/
│       └── ...
├── README.md                      # 项目说明
└── docs/                          # 文档（可选）
```

**关键区别**：实际结构使用 `plugins/` 目录而非 `skills/` 目录，每个插件是一个独立的包，可以单独安装和启用。

## 核心配置文件

### .claude-plugin/marketplace.json

这是插件市场的核心配置文件，必须位于 `.claude-plugin/marketplace.json`。

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "插件包名称",
  "description": "插件包描述",
  "owner": {
    "name": "作者名称",
    "email": "作者邮箱"
  },
  "metadata": {
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "description": "Plugin 描述",
      "source": "./plugins/plugin-name",
      "strict": false
    }
  ]
}
```

#### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `$schema` | string | 否 | Schema URL，用于验证 |
| `name` | string | 是 | 插件包名称，通常是仓库名 |
| `description` | string | 是 | 插件包描述 |
| `owner.name` | string | 否 | 作者名称 |
| `owner.email` | string | 否 | 作者邮箱 |
| `metadata.version` | string | 是 | 版本号 |
| `plugins` | array | 是 | 插件列表 |
| `plugins[].name` | string | 是 | 插件名称，用于安装命令 |
| `plugins[].description` | string | 是 | 插件描述 |
| `plugins[].source` | string | 是 | 源代码路径，相对于仓库根目录 |
| `plugins[].strict` | boolean | 是 | 是否严格模式 |

### plugins/{name}/.claude-plugin/plugin.json

每个插件必须包含独立的 `plugin.json` 配置文件：

```json
{
  "name": "plugin-name",
  "description": "Plugin 描述",
  "version": "1.0.0",
  "author": {
    "name": "作者名",
    "email": "作者邮箱"
  }
}
```

#### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 插件名称，与 marketplace.json 中的 name 一致 |
| `description` | string | 是 | 插件描述 |
| `version` | string | 是 | 版本号，语义化版本 |
| `author.name` | string | 否 | 作者名称 |
| `author.email` | string | 否 | 作者邮箱 |

## Skill 定义文件

每个插件必须包含 `SKILL.md` 文件，位于 `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`。

### 文件格式

```markdown
---
name: skill-name
description: "Skill 的简短描述，会显示在命令列表中"
---

# Skill 标题

## 简介

详细描述这个 skill 的功能和使用场景。

## 使用方式

```bash
# 使用示例
uv run {baseDir}/scripts/script.py command
```

## 配置说明

说明需要配置的环境变量或其他配置项。
```

### Frontmatter 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | 是 | Skill 名称，唯一标识符 |
| `description` | string | 是 | 简短描述，显示在命令列表 |

**注意**：实际使用的 SKILL.md 格式较为简洁，主要包含 `name` 和 `description` 两个字段。

## 添加新 Skill 的步骤

### 步骤 1: 创建插件目录

```bash
mkdir -p plugins/new-plugin/.claude-plugin
mkdir -p plugins/new-plugin/skills/new-skill/scripts
```

### 步骤 2: 编写 plugin.json

创建 `plugins/new-plugin/.claude-plugin/plugin.json`：

```json
{
  "name": "new-plugin",
  "description": "New plugin description",
  "version": "1.0.0",
  "author": {
    "name": "your-name",
    "email": "your-email@example.com"
  }
}
```

### 步骤 3: 编写 SKILL.md

创建 `plugins/new-plugin/skills/new-skill/SKILL.md`：

```markdown
---
name: new-skill
description: "Description of the new skill"
---

# New Skill

## 简介

描述 skill 的功能。

## 使用方式

```bash
uv run {baseDir}/scripts/script.py
```
```

### 步骤 4: 添加实现脚本（可选）

如果需要脚本实现，放在 `plugins/new-plugin/skills/new-skill/scripts/` 目录下。

支持的语言和运行方式：
- **Python**: `uv run {baseDir}/scripts/script.py`
- **TypeScript**: `npx -y bun {baseDir}/scripts/main.ts`
- **Bash**: 直接执行

### 步骤 5: 更新 marketplace.json

在根目录的 `.claude-plugin/marketplace.json` 中添加新的插件配置：

```json
{
  "plugins": [
    {
      "name": "new-plugin",
      "description": "New plugin description",
      "source": "./plugins/new-plugin",
      "strict": false
    }
  ]
}
```

### 步骤 6: 更新版本号

修改 `metadata.version`，遵循语义化版本规范。

### 步骤 7: 提交并推送

```bash
git add .
git commit -m "Add new-plugin"
git push
```

## 用户使用方式

### 添加插件市场

```bash
/plugin marketplace add username/repo-name
```

### 安装特定插件

```bash
/plugin install plugin-name@repo-name
```

或直接安装（不添加市场）：

```bash
/plugin install plugin-name@username/repo-name
```

### 使用插件

安装后，skills 会以 slash 命令的形式可用：

```
/skill-name
```

## 最佳实践

### 1. 插件命名

- 使用小写字母和连字符
- 格式：`功能描述`，如 `felo-search`, `cover-image-prompts`
- 避免使用通用名称，防止冲突

### 2. 目录组织

- 每个插件独立成一个目录，方便用户按需安装
- 插件可以按功能分类命名：`search-*`, `content-*`, `utility-*`
- 每个插件目录下包含 `.claude-plugin/plugin.json` 和 `skills/` 子目录

### 3. 版本管理

- 使用语义化版本（Semantic Versioning）
- 格式：`主版本.次版本.修订号`，如 `1.0.0`
- 重大变更升级主版本，新增功能升级次版本，Bug 修复升级修订号
- marketplace.json 和 plugin.json 都需要维护版本号

### 4. 文档规范

- SKILL.md 必须包含清晰的使用说明
- 列出所有可用的命令和选项
- 提供配置示例
- 说明环境变量需求
- 可以使用 `{baseDir}` 变量引用 skill 目录路径

### 5. 脚本规范

- 使用相对路径 `{baseDir}` 引用 skill 目录
- 优先使用 `uv run` 或 `npx -y bun` 运行脚本，避免依赖安装步骤
- 提供友好的错误信息和帮助文本

## 示例

### 完整的 marketplace.json

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "mazhen-skills",
  "description": "Personal skills collection for Claude Code",
  "owner": {
    "name": "mazhen",
    "email": "mz1999@gmail.com"
  },
  "metadata": {
    "version": "2.0.0"
  },
  "plugins": [
    {
      "name": "searxng",
      "description": "Privacy-respecting metasearch using authenticated SearXNG instance",
      "source": "./plugins/searxng",
      "strict": false
    },
    {
      "name": "felo-search",
      "description": "Felo AI real-time web search for questions requiring current/live information",
      "source": "./plugins/felo-search",
      "strict": false
    }
  ]
}
```

### 完整的 plugin.json

```json
{
  "name": "felo-search",
  "description": "Felo AI real-time web search for questions requiring current/live information",
  "version": "1.0.0",
  "author": {
    "name": "mazhen",
    "email": "mz1999@gmail.com"
  }
}
```

### 完整的 SKILL.md

```markdown
---
name: felo-search
description: "Felo AI real-time web search for questions requiring current/live information"
---

# Felo Search Skill

Felo AI provides AI-driven conversational search that generates intelligent answers based on real-time web search results.

## When to Use

Trigger this skill for questions requiring current or real-time information:

- **Current events & news:** Recent developments, trending topics
- **Real-time data:** Weather, stock prices, exchange rates
- **Information queries:** "What is...", "Tell me about..."

## Script Directory

**Important**: All scripts are located in the `scripts/` subdirectory of this skill.

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/felo.py`
3. Replace all `${SKILL_DIR}` in this document with the actual path

## Commands

### Basic Search
```bash
uv run ${SKILL_DIR}/scripts/felo.py chat "Your search query"
```

## Configuration

### API Key (Required)

```bash
export FELO_API_KEY=your_api_key_here
```

Get your API key from: https://felo.ai
```

## 参考

- [mazhen-skills 示例](https://github.com/mz1999/mazhen-skills)
- [Semantic Versioning](https://semver.org/)
