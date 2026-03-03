# Claude Code 插件市场标准文档

本文档说明如何将 skills 发布到 Claude Code 插件市场，让用户可以通过 `/plugin marketplace add username/repo-name` 命令安装。

## 概述

Claude Code 支持从 GitHub 仓库加载 skills 集合，称为"插件市场"。通过标准化的配置，用户可以方便地发现和安装多个相关的 skills。

## 仓库结构要求

```
your-skills-repo/
├── .claude-plugin/
│   └── marketplace.json      # 插件市场清单（必需）
├── skills/                   # Skills 目录
│   ├── skill-a/
│   │   ├── SKILL.md          # Skill 定义文件（必需）
│   │   ├── scripts/          # 实现脚本（可选）
│   │   └── ...               # 其他资源文件
│   └── skill-b/
│       └── SKILL.md
├── README.md                 # 项目说明
└── docs/                     # 文档（可选）
```

## 核心配置文件

### .claude-plugin/marketplace.json

这是插件市场的核心配置文件，必须位于 `.claude-plugin/marketplace.json`。

```json
{
  "name": "插件包名称",
  "owner": {
    "name": "作者名称",
    "email": "作者邮箱"
  },
  "metadata": {
    "description": "插件包描述",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "技能组名称",
      "description": "技能组描述",
      "source": "./",
      "strict": false,
      "skills": [
        "./skills/skill-a",
        "./skills/skill-b"
      ]
    }
  ]
}
```

#### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 插件包名称，通常是仓库名 |
| `owner.name` | string | 否 | 作者名称 |
| `owner.email` | string | 否 | 作者邮箱 |
| `metadata.description` | string | 是 | 插件包描述 |
| `metadata.version` | string | 是 | 版本号，使用语义化版本 |
| `plugins` | array | 是 | 技能组列表 |
| `plugins[].name` | string | 是 | 技能组名称，用于安装命令 |
| `plugins[].description` | string | 是 | 技能组描述 |
| `plugins[].source` | string | 是 | 源代码路径，通常为 `"./"` |
| `plugins[].strict` | boolean | 是 | 是否严格模式 |
| `plugins[].skills` | array | 是 | skill 路径列表，相对于仓库根目录 |

## Skill 定义文件

每个 skill 必须包含 `SKILL.md` 文件，位于 `skills/<skill-name>/SKILL.md`。

### 文件格式

```markdown
---
name: skill-name
description: Skill 的简短描述，会显示在命令列表中。使用第三人称，最多1024字符。
author: 作者名
version: 1.0.0
homepage: https://github.com/username/repo
triggers:
  - "触发词1"
  - "触发词2"
metadata:
  clawdbot:
    emoji: "🔍"
    requires:
      bins: ["python3", "node"]
    config:
      env:
        ENV_VAR_NAME:
          description: "环境变量说明"
          required: true
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
| `author` | string | 否 | 作者名 |
| `version` | string | 否 | 版本号 |
| `homepage` | string | 否 | 项目主页 |
| `triggers` | array | 否 | 自然语言触发词 |
| `metadata.clawdbot` | object | 否 | Claude Code 特定配置 |

## 添加新 Skill 的步骤

### 步骤 1: 创建 Skill 目录

```bash
mkdir -p skills/new-skill/scripts
```

### 步骤 2: 编写 SKILL.md

创建 `skills/new-skill/SKILL.md`，包含完整的 frontmatter 和使用文档。

### 步骤 3: 添加实现脚本（可选）

如果需要脚本实现，放在 `skills/new-skill/scripts/` 目录下。

支持的语言和运行方式：
- **Python**: `uv run {baseDir}/scripts/script.py`
- **TypeScript**: `npx -y bun {baseDir}/scripts/main.ts`
- **Bash**: 直接执行

### 步骤 4: 更新 marketplace.json

在 `plugins` 数组中找到合适的技能组，添加新 skill 的路径：

```json
{
  "name": "技能组名称",
  "skills": [
    "./skills/existing-skill",
    "./skills/new-skill"  // 添加这一行
  ]
}
```

### 步骤 5: 更新版本号

修改 `metadata.version`，遵循语义化版本规范。

### 步骤 6: 提交并推送

```bash
git add .
git commit -m "Add new-skill"
git push
```

## 用户使用方式

### 安装插件市场

```bash
/plugin marketplace add username/repo-name
```

### 安装特定技能组

```bash
/plugin install 技能组名称@repo-name
```

### 使用 Skill

安装后，skills 会以 slash 命令的形式可用：

```
/skill-name
```

## 最佳实践

### 1. Skill 命名

- 使用小写字母和连字符
- 格式: `作者名-skill-功能`，如 `baoyu-xhs-images`
- 避免使用通用名称，防止冲突

### 2. 目录组织

- 将相关的 skills 放在同一个技能组中
- 可以按功能分类：search-skills、content-skills、utility-skills

### 3. 版本管理

- 使用语义化版本（Semantic Versioning）
- 格式: `主版本.次版本.修订号`，如 `1.0.0`
- 重大变更升级主版本，新增功能升级次版本，Bug 修复升级修订号

### 4. 文档规范

- SKILL.md 必须包含清晰的使用说明
- 列出所有可用的命令和选项
- 提供配置示例
- 说明环境变量需求

### 5. 脚本规范

- 使用相对路径 `{baseDir}` 引用 skill 目录
- 优先使用 `uv run` 或 `npx -y bun` 运行脚本，避免依赖安装步骤
- 提供友好的错误信息和帮助文本

## 示例

### 完整的 marketplace.json

```json
{
  "name": "mazhen-skills",
  "owner": {
    "name": "mazhen",
    "email": "mazhen@example.com"
  },
  "metadata": {
    "description": "Personal skills for daily work",
    "version": "1.2.0"
  },
  "plugins": [
    {
      "name": "search-skills",
      "description": "Web search related skills",
      "source": "./",
      "strict": false,
      "skills": [
        "./skills/searxng"
      ]
    },
    {
      "name": "dev-tools",
      "description": "Development utility tools",
      "source": "./",
      "strict": false,
      "skills": [
        "./skills/git-helper",
        "./skills/docker-utils"
      ]
    }
  ]
}
```

### 完整的 SKILL.md

```markdown
---
name: searxng-auth
description: Privacy-respecting metasearch using your authenticated SearXNG instance.
author: mazhen
version: 1.0.0
homepage: https://github.com/mazhen/mazhen-skills
triggers:
  - "search for"
  - "search web"
metadata:
  clawdbot:
    emoji: "🔐"
    requires:
      bins: ["python3"]
    config:
      env:
        SEARXNG_URL:
          description: "Your SearXNG instance URL"
          required: true
---

# SearXNG Search

## 使用方式

```bash
uv run {baseDir}/scripts/searxng.py search "query"
```

## 配置

设置环境变量：
```bash
export SEARXNG_URL=https://your-instance.com
export SEARXNG_USERNAME=your-username
export SEARXNG_PASSWORD=your-password
```
```

## 参考

- [baoyu-skills 示例](https://github.com/JimLiu/baoyu-skills)
- [Semantic Versioning](https://semver.org/)
