---
name: felo
description: AI-powered conversational search with real-time web results. Use when user asks to "search with Felo", "Felo search", "AI search", or wants intelligent answers with cited web sources.
---

# Felo AI Chat - Conversational Search

Felo AI provides AI-driven conversational search that generates intelligent answers based on real-time web search results, with cited sources and query analysis.

## Script Directory

**Important**: All scripts are located in the `scripts/` subdirectory of this skill.

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/felo.py`
3. Replace all `${SKILL_DIR}` in this document with the actual path

**Script Reference**:
| Script | Purpose |
|--------|---------|
| `scripts/felo.py` | Felo Chat CLI |

## Commands

### Basic Chat Search
```bash
uv run ${SKILL_DIR}/scripts/felo.py chat "What is the latest news about AI?"
uv run ${SKILL_DIR}/scripts/felo.py chat "Explain quantum computing"
uv run ${SKILL_DIR}/scripts/felo.py chat "Best restaurants in Tokyo" --format json
```

### Output Formats
```bash
uv run ${SKILL_DIR}/scripts/felo.py chat "query" --format table  # Rich formatted output (default)
uv run ${SKILL_DIR}/scripts/felo.py chat "query" --format json   # JSON output
```

## Configuration

### API Key (Required)

Set your Felo API Key:

```bash
export FELO_API_KEY=your_api_key_here
```

Or configure in your Claude Code config:
```json
{
  "env": {
    "FELO_API_KEY": "your_api_key_here"
  }
}
```

Get your API key from: https://felo.ai

### Proxy Configuration (Optional)

By default, the skill does not use a proxy. If you need to use a proxy to access the Felo API, set the `FELO_PROXY` environment variable.

**Supported proxy formats:**

| Protocol | Format | Example |
|----------|--------|---------|
| HTTP | `http://host:port` | `http://127.0.0.1:8080` |
| HTTPS | `https://host:port` | `https://proxy.example.com:443` |
| SOCKS5 | `socks5://host:port` | `socks5://127.0.0.1:7897` |
| SOCKS5 (authenticated) | `socks5://user:pass@host:port` | `socks5://user:pass@127.0.0.1:1080` |

**Enable proxy:**

```bash
# HTTP/HTTPS proxy
export FELO_PROXY=http://127.0.0.1:8080

# SOCKS5 proxy (common for Clash/V2Ray)
export FELO_PROXY=socks5://127.0.0.1:7897
```

When not set or set to empty string, no proxy is used.

## Features

- 🤖 AI-powered conversational answers
- 🌐 Real-time web search results
- 📚 Cited sources with links and summaries
- 🔍 Query analysis and optimization
- 🎨 Rich formatted output with sources table
- 🚀 JSON mode for programmatic use

## Rate Limits

- 100 requests per minute per API key
- Query length: 1-2000 characters

## Security Notes

- API Key is read from environment variables - never hardcoded
- API Key is never logged or displayed in output

## API

Uses Felo AI OpenAPI v2: `POST https://openapi.felo.ai/v2/chat`
