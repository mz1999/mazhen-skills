---
name: felo-web-fetch
description: "Extract web page content as markdown, HTML, or plain text using Felo AI. Triggers on /felo-web-fetch command only."
---

# Felo Web Fetch Skill

Extract web page content as markdown, HTML, or plain text using Felo AI's web extraction API.

## When to Use

Trigger this skill when the user explicitly requests to extract web content using the `/felo-web-fetch` command:

- **Fetch article content:** Extract article text from a URL for reading or processing
- **Convert web to markdown:** Get clean markdown from web pages
- **Extract specific elements:** Use CSS selectors to extract specific parts of a page
- **Archive web content:** Save web page content in a readable format
- **Content processing:** Extract text for summarization, translation, or analysis
- **Documentation extraction:** Get clean docs from messy HTML pages

**Explicit commands:** `/felo-web-fetch`, "felo web fetch"

**Do NOT use for:**
- General web search (use felo-search instead)
- Questions about current events (use felo-search instead)
- Downloading files or media (this extracts text content only)

## Script Directory

**Important**: All scripts are located in the `scripts/` subdirectory of this skill.

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/web_fetch.mjs`
3. Replace all `${SKILL_DIR}` in this document with the actual path

**Script Reference**:
| Script | Purpose |
|--------|---------|
| `scripts/web_fetch.mjs` | Web content extraction CLI |

## Commands

### Basic Fetch (Markdown)
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com/article"
```

### Different Formats
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --output-format html
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --output-format text
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --output-format markdown
```

### Fine-grained Extraction
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --crawl-mode fine
```

### Extract Specific Element
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --target-selector "article.main-content"
```

### Wait for Dynamic Content
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --wait-for-selector "#content-loaded"
```

### Enable Readability
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --with-readability true
```

### Add Cookies
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --cookie "session=abc123" --cookie "user=john"
```

### JSON Output (Full Response)
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --json
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

## Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--url` | string | Target web page URL (required) | - |
| `--output-format` | enum | Output format: html, markdown, text | - |
| `--crawl-mode` | enum | Crawl mode: fast, fine | - |
| `--target-selector` | string | CSS selector for target extraction | - |
| `--wait-for-selector` | string | Wait until selector appears | - |
| `--cookie` | string | Add cookie entry (repeatable) | - |
| `--set-cookies-json` | string | JSON array for set_cookies | - |
| `--user-agent` | string | Custom user-agent | - |
| `--timeout` | number | Request timeout in seconds | 60 |
| `--request-timeout-ms` | number | API timeout in milliseconds | - |
| `--with-readability` | bool | Enable readability processing | - |
| `--with-links-summary` | bool | Include links summary | - |
| `--with-images-summary` | bool | Include images summary | - |
| `--with-images-readability` | bool | Enable images readability | - |
| `--with-images` | bool | Include images | - |
| `--with-links` | bool | Include links | - |
| `--ignore-empty-text-image` | bool | Ignore empty text images | - |
| `--with-cache` | bool | Enable cache | - |
| `--with-stypes` | bool | Enable stypes | - |
| `--json` | flag | Print full JSON response | false |
| `--help` | flag | Show help | false |

## Crawl Modes

- **fast**: Quick extraction, suitable for static content
- **fine**: Thorough extraction with JavaScript execution, better for dynamic pages

## Error Handling

### Common Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `INVALID_API_KEY` | API Key is invalid or revoked | Check your FELO_API_KEY |
| `MISSING_AUTHORIZATION` | Authorization header missing | Set FELO_API_KEY environment variable |
| `INVALID_URL` | URL format is invalid | Check the URL format |
| `FETCH_FAILED` | Failed to fetch the page | Check if URL is accessible |
| `TIMEOUT` | Request timed out | Increase timeout or check URL |

### HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API Key |
| 429 | Too Many Requests - Rate limit exceeded |
| 5xx | Server Error - Retry with backoff |

## Complete Examples

### Example 1: Fetch article content

**User asks:** `/felo-web-fetch --url https://example.com/article`

**Bash command:**
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com/article"
```

**Expected output:**
```markdown
# Article Title

Article content in markdown format...
```

### Example 2: Extract with readability

**User asks:** `/felo-web-fetch --url https://example.com --with-readability true`

**Bash command:**
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --with-readability true
```

### Example 3: JSON output for processing

**Bash command:**
```bash
node ${SKILL_DIR}/scripts/web_fetch.mjs --url "https://example.com" --json
```

**Expected output:**
```json
{
  "data": {
    "url": "https://example.com",
    "title": "Page Title",
    "content": "Extracted content...",
    "links": [...],
    "images": [...]
  }
}
```

## Security Notes

- API Key is read from environment variables - never hardcoded
- API Key is never logged or displayed in output
- URLs are validated before fetching
- Content is extracted, not executed

## API

**Endpoint:** `POST https://openapi.felo.ai/v2/web/extract`

**Authentication:** Bearer token in Authorization header (from `FELO_API_KEY` environment variable)

**Request format:**
```json
{
  "url": "https://example.com",
  "output_format": "markdown",
  "crawl_mode": "fast",
  "target_selector": "",
  "wait_for_selector": ""
}
```

**Response format:**
```json
{
  "data": {
    "url": "https://example.com",
    "title": "Page Title",
    "content": "Extracted content in requested format",
    "links": [...],
    "images": [...]
  }
}
```

## Additional Resources

- [Felo Open Platform Documentation](https://openapi.felo.ai)
- [Get API Key](https://felo.ai) (Settings → API Keys)
- [API Reference](https://openapi.felo.ai/docs)
