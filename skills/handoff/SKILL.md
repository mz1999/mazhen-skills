---
name: handoff
description: Create and manage handoff documents for seamless work continuity. Triggered when user says 'create handoff', 'save handoff', '记录上下文', 'load handoff', '继续工作', or 'resume work'. Helps preserve context across AI sessions.

---

# Handoff - 工作状态记录与恢复

创建或加载 handoff 文档，实现工作状态的保存和恢复。

## 模式识别

判断当前请求属于哪种模式：

**创建/更新 handoff？** 用户说：
- "create handoff" / "保存 handoff" / "记录上下文"
- "update handoff" / "更新 handoff"
→ 执行 **CREATE 流程**

**加载/继续工作？** 用户说：
- "load handoff" / "继续工作" / "resume work"
- "读取 handoff" / "恢复上下文"
→ 执行 **RESUME 流程**

---

## CREATE 流程

### Step 1: 收集当前状态

获取以下信息：
- 当前时间戳
- 项目路径（当前工作目录）
- Git 分支（如果是 git 仓库）

### Step 2: 检查现有 handoff

检查文件是否存在：`.claude/handoffs/handoff.md`

如果存在，先读取现有内容，在原有基础上更新。

### Step 3: 创建/更新 handoff 文档

创建目录（如不存在）：
```bash
mkdir -p .claude/handoffs
```

使用模板创建或更新文档，替换以下占位符：
- `[TODO: ...]` - 根据当前会话内容填写
- `[TIMESTAMP]` - 当前时间（格式：YYYY-MM-DD HH:MM:SS）
- `[PROJECT_PATH]` - 项目绝对路径
- `[GIT_BRANCH]` - 当前 git 分支（或 "N/A"）

**文档结构**：
1. **Goal / 目标** - 当前任务的总体目标
2. **Current Progress / 当前进展** - 已完成的工作
3. **What Worked / 成功经验** - 有效的方法
4. **What Didn't Work / 失败经验** - 需要避免的方法
5. **Next Steps / 下一步** - 接下来的行动计划

### Step 4: 确认保存

向用户确认：
- Handoff 文件路径
- 已记录的章节
- 提醒用户下次可以用 "load handoff" 或 "继续工作" 恢复

---

## RESUME 流程

### Step 1: 查找 handoff 文件

检查文件：`.claude/handoffs/handoff.md`

如果不存在，告知用户未找到 handoff 文件。

### Step 2: 读取 handoff

完整读取 handoff 文件内容，理解：
- 任务目标（Goal）
- 当前进展（Current Progress）
- 经验教训（What Worked / What Didn't Work）
- 下一步行动（Next Steps）

### Step 3: 向用户确认

总结 handoff 中的关键信息，询问用户：
- 是否从 "Next Steps" 的第一项开始继续？
- 还是需要调整优先级？

### Step 4: 开始工作

根据确认的下一步行动开始工作。

---

## 存储位置

- **文件路径**: `.claude/handoffs/handoff.md`
- **更新方式**: 覆盖式更新（始终只有一个最新版本）

## 模板参考

完整模板见：[references/template.md](references/template.md)

## 使用示例

### 创建 handoff
用户："保存当前进度"
→ 创建/更新 `.claude/handoffs/handoff.md`

### 恢复工作
用户："继续之前的工作"
→ 读取 handoff → 确认下一步 → 开始执行
