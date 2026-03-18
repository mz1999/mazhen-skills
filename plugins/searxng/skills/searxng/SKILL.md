---
name: searxng
description: Privacy-respecting metasearch using your authenticated SearXNG instance. Search the web with HTTP Basic Auth protection. Use when user asks to "search for", "search web", "find information", or "look up" anything online.
version: 2.1.0
---

# SearXNG Search with Authentication

Search the web using your authenticated SearXNG instance - a privacy-respecting metasearch engine protected with HTTP Basic Auth.

## Script Directory

**Important**: All scripts are located in the `scripts/` subdirectory of this skill.

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/searxng.py`
3. Replace all `${SKILL_DIR}` in this document with the actual path

**Script Reference**:
| Script | Purpose |
|--------|---------|
| `scripts/searxng.py` | Main search CLI |

## Commands

### Web Search
```bash
uv run ${SKILL_DIR}/scripts/searxng.py search "query"              # Top 10 results
uv run ${SKILL_DIR}/scripts/searxng.py search "query" -n 20        # Top 20 results
uv run ${SKILL_DIR}/scripts/searxng.py search "query" --format json # JSON output
```

### Category Search
```bash
uv run ${SKILL_DIR}/scripts/searxng.py search "query" --category images
uv run ${SKILL_DIR}/scripts/searxng.py search "query" --category news
uv run ${SKILL_DIR}/scripts/searxng.py search "query" --category videos
```

### Advanced Options
```bash
uv run ${SKILL_DIR}/scripts/searxng.py search "query" --language en
uv run ${SKILL_DIR}/scripts/searxng.py search "query" --time-range day
```

## Configuration

**Required:** Set all three environment variables:

```bash
export SEARXNG_URL=https://your-searxng-instance.com
export SEARXNG_USERNAME=your-username
export SEARXNG_PASSWORD=your-password
```

Or configure in your Clawdbot config:
```json
{
  "env": {
    "SEARXNG_URL": "https://your-searxng-instance.com",
    "SEARXNG_USERNAME": "your-username",
    "SEARXNG_PASSWORD": "your-password"
  }
}
```

### Proxy Configuration (Optional)

By default, the skill does not use a proxy. If you need to use a proxy to access your SearXNG instance, set the `SEARXNG_PROXY` environment variable.

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
export SEARXNG_PROXY=http://127.0.0.1:8080

# SOCKS5 proxy (common for Clash/V2Ray)
export SEARXNG_PROXY=socks5://127.0.0.1:7897
```

When not set or set to empty string, no proxy is used.

## Features

- 🔐 HTTP Basic Auth protection
- 🔒 Privacy-focused (uses your self-hosted instance)
- 🌐 Multi-engine aggregation
- 📰 Multiple search categories
- 🎨 Rich formatted output
- 🚀 Fast JSON mode for programmatic use

## Security Notes

- All credentials are read from environment variables - never hardcoded
- SSL certificate verification is enabled by default for secure public deployments
- Passwords are never logged or displayed in output

## API

Uses your SearXNG instance's JSON API endpoint with HTTP Basic Authentication.
