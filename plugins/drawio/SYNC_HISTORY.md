# drawio 插件同步历史

## v2.2.0 — 2026-03-20（同步自上游 skill-cli）

**上游仓库**: `/Users/mazhen/Documents/works/mazhen/skills/drawio-mcp/skill-cli/`

### 新增内容

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| CLAUDE.md | 新增章节 | WSL2 CLI 路径与检测方式 |
| CLAUDE.md | 新增章节 | Dark Mode Colors（`adaptiveColors="auto"`, `light-dark()` 函数） |
| CLAUDE.md | 新增章节 | Coding Conventions（Allman brace style, `function()` 表达式优先） |
| SKILL.md | frontmatter 更新 | `description` 扩展为包含触发短语的长版本 |
| SKILL.md | 新增内容 | WSL2 CLI 检测与路径（"Locating the CLI" 章节） |
| SKILL.md | 新增内容 | "Opening the result" 表格新增 WSL2 行（`wslpath -w`） |
| SKILL.md | 新增内容 | Step 3 CLI 未找到时的降级行为（保留 .drawio 文件） |
| SKILL.md | 新增内容 | Step 4 打开命令失败时打印路径 |
| SKILL.md | 属性变更 | `<mxGraphModel>` → `<mxGraphModel adaptiveColors="auto">` |
| SKILL.md | 新增章节 | Dark mode colors |
| SKILL.md | 新增内容 | Edge routing：边标签不要用 HTML 包裹缩小字体 |
| SKILL.md | 新增章节 | Troubleshooting 表格（5 行常见问题） |
| references/xml-reference.md | 新建文件 | 上游将 XML 样式/路由/容器参考内容提取为独立文件 |
| README.md | 新增章节 | Other Variants（MCP App/Tool Server、Project Instructions 链接） |

### 本地保留（未同步）

| 字段/内容 | 原因 |
|----------|------|
| SKILL.md `allowed-tools: Bash, Write` | 本地插件系统特有字段 |
| SKILL.md `disable-model-invocation: true` | 本地插件系统特有字段 |
| SKILL.md `version` 字段 | 本地版本管理 |
| README.md 安装方式（marketplace install） | 本地插件市场安装方式不同于上游 |
| SKILL.md 现有内联 XML 参考内容 | 保留，不删减，仅增加对 xml-reference.md 的引用提示 |

### 版本号更新

- `plugin.json`: `2.1.0` → `2.2.0`
- `SKILL.md` frontmatter: `2.1.0` → `2.2.0`
- `marketplace.json` `plugins[drawio].version`: `2.1.0` → `2.2.0`

---

## v2.1.0 — 初始版本（复刻自上游）

初始从上游 skill-cli 复刻，适配本地插件市场结构。
