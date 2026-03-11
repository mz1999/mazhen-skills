# Usage

## Command Syntax

```bash
# Auto-select type and style based on content
/article-illustrator-prompts path/to/article.md

# Specify type
/article-illustrator-prompts path/to/article.md --type infographic

# Specify style
/article-illustrator-prompts path/to/article.md --style blueprint

# Combine type and style
/article-illustrator-prompts path/to/article.md --type flowchart --style notion

# Specify density
/article-illustrator-prompts path/to/article.md --density rich

# Direct content input (paste mode)
/article-illustrator-prompts
[paste content]
```

## Options

| Option | Description |
|--------|-------------|
| `--type <name>` | Illustration type (see Type Gallery in SKILL.md) |
| `--style <name>` | Visual style (see references/styles.md) |
| `--density <level>` | Image count: minimal / balanced / rich |

## Input Modes

| Mode | Trigger | Output Directory |
|------|---------|------------------|
| File path | `path/to/article.md` | Use `default_output_dir` preference, or ask if not set |
| Paste content | No path argument | `article-illustrator-prompts/{topic-slug}/` |

## Output Directory Options

| Value | Path |
|-------|------|
| `same-dir` | `{article-dir}/` |
| `prompts-subdir` | `{article-dir}/prompts/` |
| `independent` | `article-illustrator-prompts/{topic-slug}/` |

Configure in EXTEND.md: `default_output_dir: prompts-subdir`

## Examples

**Technical article with data**:
```bash
/article-illustrator-prompts api-design.md --type infographic --style blueprint
```

**Personal story**:
```bash
/article-illustrator-prompts journey.md --type scene --style warm
```

**Tutorial with steps**:
```bash
/article-illustrator-prompts how-to-deploy.md --type flowchart --density rich
```
