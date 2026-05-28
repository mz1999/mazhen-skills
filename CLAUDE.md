# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal skills collection for Claude Code, distributed via the `skills` CLI. Skills are registered in `.claude-plugin/plugin.json` and each lives in `skills/<name>/`. Most skills are pure documentation (a single `SKILL.md` with YAML frontmatter). The exception is `wechat-article-cli`, which is a full Node.js CLI package.

## Project Structure

```
.claude-plugin/plugin.json     # Registry of all skills
skills/<name>/SKILL.md          # Skill definition with YAML frontmatter
skills/<name>/...               # Optional supporting files (scripts, references, assets)
skills-lock.json                # Tracks externally sourced skill dependencies
```

### Skill Types

- **Documentation-only**: `tech-article-outline`, `twitter-cli` — single `SKILL.md`.
- **With reference docs**: `gc-log-analyzer` (Python parser + reference docs), `visual-html` (design system HTML/CSS reference).
- **With executable code**: `wechat-article-cli` (Node.js CLI).

## Development Commands

### wechat-article-cli

```bash
cd skills/wechat-article-cli
npm test                        # Runs --help smoke test
node bin/wechat-article-cli.js --help
node bin/wechat-article-cli.js fetch <url>
node batch-test.js              # Integration test against 20 real WeChat articles
```

The CLI depends on the **kimi-webbridge daemon** running locally (`~/.kimi-webbridge/bin/kimi-webbridge`). The daemon must show `running: true` and `extension_connected: true`.

### gc-log-analyzer

```bash
cd skills/gc-log-analyzer
python3 scripts/gc_log_parser.py /path/to/gc.log --summary > gc_summary.json
python3 scripts/gc_log_parser.py /path/to/gc.log --window-start "2024-01-15T10:23:45" --window-end "2024-01-15T10:24:00" > window.log
python3 scripts/gc_log_parser.py /path/to/gc.log --window-start-line 1240 --window-end-line 1260 > window.log
```

The `test/` directory contains sample GC log files (not unit tests).

## Architecture

### Skill Registration

To add or remove a skill, update both:
1. `skills/<name>/SKILL.md` — create the skill file with frontmatter
2. `.claude-plugin/plugin.json` — add the path to the `skills` array

### SKILL.md Frontmatter

Required fields: `name`, `description`. Optional: `compatibility`.

```yaml
---
name: skill-name
description: |
  Multi-line description of when to trigger this skill.
compatibility:
  - Node.js >= 18
---
```

### wechat-article-cli Architecture

The CLI is a thin client over the kimi-webbridge browser automation daemon:

- `bin/wechat-article-cli.js` — Entry point. Commands: `fetch <url>`, `--help`, `--version`.
- `src/fetch.js` — Orchestrates the fetch: validates URL, checks daemon status, opens a browser session, polls for content extraction.
- `src/browser.js` — HTTP client talking to `http://127.0.0.1:10086/command`. Actions: `navigate`, `evaluate`, `snapshot`, `close_session`.
- `src/extractor.js` — Builds a JavaScript string injected into the browser via `evaluate()`. Parses the WeChat article DOM into Markdown.
- `src/output.js` — Structured JSON output helpers.

The extraction script runs inside the browser context (not Node.js). It detects WeChat CAPTCHA/verification pages and returns `CAPTCHA_REQUIRED` when triggered.

## Packaging & Distribution

The repo is installed by end users via:

```bash
npx skills add mz1999/mazhen-skills
npx skills add mz1999/mazhen-skills --skill <name>
```

For `wechat-article-cli` specifically, it is also published as a standalone global npm package:

```bash
npm install -g wechat-article-cli
```

Version bumps should update both `package.json` and `package-lock.json` (if present). The `files` array in `package.json` controls what gets published: `bin/`, `src/`, `README.md`, `LICENSE`.
