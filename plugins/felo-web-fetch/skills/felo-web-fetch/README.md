# Felo Web Fetch Skill for Claude Code

**Extract web page content as markdown, HTML, or plain text.**

Convert any web page into clean, readable content using Felo AI's web extraction API.

---

## What It Does

Felo Web Fetch integrates [Felo AI](https://felo.ai) into Claude Code, enabling:

- Extract article content from any URL
- Convert web pages to clean markdown
- Extract specific elements using CSS selectors
- Handle JavaScript-rendered dynamic content
- Get structured data with links and images summary
- Support cookies and custom user agents
- Enable readability processing for cleaner content

**When to use:**
- Reading articles without distractions
- Extracting documentation for offline use
- Processing web content for analysis
- Converting web pages to markdown
- Archiving web content

**When NOT to use:**
- General web search (use felo-search instead)
- Real-time information queries
- Downloading files or binary content

---

## Quick Setup

### Step 1: Install

```bash
npx @anthropic-ai/skills add felo-web-fetch
```

**Verify:** Restart Claude Code and run:
```bash
claude skills list
```

You should see `felo-web-fetch` in the output.

### Step 2: Get API Key

1. Visit [felo.ai](https://felo.ai) and log in (or register)
2. Click your avatar (top right) → **Settings**
3. Navigate to **API Keys** tab
4. Click **Create New Key**
5. Copy your API key

### Step 3: Configure

Set the `FELO_API_KEY` environment variable:

**Linux/macOS:**
```bash
export FELO_API_KEY="your-api-key-here"

# Make it permanent (add to shell profile)
echo 'export FELO_API_KEY="your-api-key-here"' >> ~/.zshrc  # or ~/.bashrc
```

**Windows (PowerShell):**
```powershell
$env:FELO_API_KEY="your-api-key-here"

# Make it permanent (system environment variables)
# System Properties → Advanced → Environment Variables → New
```

**Restart Claude Code** to load the environment variable.

### Step 4: Test

Try fetching a web page:
```
/felo-web-fetch --url https://example.com
```

Or use the CLI directly:
```bash
node skills/felo-web-fetch/scripts/web_fetch.mjs --url https://example.com
```

---

## Usage Examples

### Basic Fetch

```
You: /felo-web-fetch --url https://en.wikipedia.org/wiki/Anthropic
Claude: [Displays article content in markdown format]
```

### Extract Specific Format

```
You: /felo-web-fetch --url https://example.com --output-format html
Claude: [Displays raw HTML content]
```

### Extract with Readability

```
You: /felo-web-fetch --url https://example.com/blog/post --with-readability true
Claude: [Extracts main article content, removes ads/navigation]
```

### Developer Scenarios

**Extract Documentation:**
```
You: /felo-web-fetch --url https://docs.example.com/api --with-readability true
Claude: [Displays clean markdown version of the docs]
```

**Archive Content:**
```bash
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --output-format markdown > article.md
```

---

## Command Reference

### Basic Usage

```bash
# Fetch as markdown
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com"

# Fetch as HTML
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --output-format html

# Fetch as plain text
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --output-format text
```

### Advanced Options

```bash
# Fine-grained extraction (JavaScript support)
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --crawl-mode fine

# Extract specific element
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --target-selector "article.main-content"

# Wait for dynamic content
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --wait-for-selector "#content-loaded"

# Enable readability
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --with-readability true

# Add cookies
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --cookie "session=abc" --cookie "user=john"

# Custom user agent
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --user-agent "Mozilla/5.0..."

# Include links and images summary
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --with-links-summary true --with-images-summary true

# JSON output
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --json
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--url` | Target web page URL (required) | - |
| `--output-format` | Output format: html, markdown, text | - |
| `--crawl-mode` | fast or fine (JS rendering) | - |
| `--target-selector` | CSS selector for specific element | - |
| `--wait-for-selector` | Wait for element before extraction | - |
| `--cookie` | Add cookie (repeatable) | - |
| `--set-cookies-json` | JSON array of cookies | - |
| `--user-agent` | Custom user agent string | - |
| `--timeout` | Request timeout in seconds | 60 |
| `--request-timeout-ms` | API timeout in milliseconds | - |
| `--with-readability` | Enable readability processing | - |
| `--with-links-summary` | Include links summary | - |
| `--with-images-summary` | Include images summary | - |
| `--with-images-readability` | Enable images readability | - |
| `--with-images` | Include images | - |
| `--with-links` | Include links | - |
| `--ignore-empty-text-image` | Ignore empty text images | - |
| `--with-cache` | Enable cache | - |
| `--with-stypes` | Enable stypes | - |
| `--json` | Output full JSON response | false |

---

## Advanced Configuration

### Proxy Support

If you need a proxy to access Felo API:

```bash
# HTTP proxy
export FELO_PROXY=http://127.0.0.1:8080

# SOCKS5 proxy (common for Clash/V2Ray)
export FELO_PROXY=socks5://127.0.0.1:7897
```

Supported formats:
- `http://host:port`
- `https://host:port`
- `socks5://host:port`
- `socks5://user:pass@host:port`

### Custom API Base

If you need to use a different API endpoint:

```bash
export FELO_API_BASE=https://custom-api.example.com
```

---

## Troubleshooting

### "FELO_API_KEY not set" error

**Problem:** Environment variable not configured.

**Solution:**
```bash
export FELO_API_KEY="your-key"
```

Then restart Claude Code.

### "INVALID_API_KEY" error

**Problem:** API key is incorrect or revoked.

**Solution:** Generate a new key at [felo.ai](https://felo.ai) (Settings → API Keys).

### "FETCH_FAILED" error

**Problem:** Unable to fetch the URL.

**Solutions:**
- Check if the URL is accessible in a browser
- Try `--crawl-mode fine` for JavaScript-heavy sites
- Increase timeout with `--timeout 120`
- Check if the site blocks automated requests

### Empty or partial content

**Problem:** Dynamic content not loaded.

**Solution:** Use `--crawl-mode fine` or `--wait-for-selector`:
```bash
node skills/felo-web-fetch/scripts/web_fetch.mjs --url "https://example.com" --crawl-mode fine
```

### Proxy not working

**Problem:** Proxy configured but not being used.

**Solution:** Node.js native fetch requires `undici` for proxy support. Ensure you're using Node.js 18+:
```bash
node --version
```

If proxy is configured but `undici` is not available, the script will warn and proceed without proxy.

---

## Links

- **[Get API Key](https://felo.ai)** - Settings → API Keys
- **[API Documentation](https://openapi.felo.ai)** - Full API reference
- **[Report Issues](https://github.com/Felo-Inc/felo-skills/issues)** - Bug reports and feature requests

---

## License

MIT License - see [LICENSE](./LICENSE) for details.
