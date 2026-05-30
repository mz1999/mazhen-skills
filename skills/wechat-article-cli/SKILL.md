---
name: wechat-article-cli
description: >
  Fetch WeChat public account (mp.weixin.qq.com) articles as Markdown via a real browser.
  Trigger when the user provides a WeChat article URL, asks to extract or download
  content from a WeChat article, convert a WeChat article to Markdown, or mentions
  mp.weixin.qq.com.
compatibility:
  - Node.js >= 18
  - kimi-webbridge daemon running with extension connected
---

# wechat-article-cli

Fetch WeChat public account articles as structured Markdown via kimi-webbridge.

## When to Use

- User provides a WeChat article URL (`mp.weixin.qq.com`)
- User asks to extract, download, or convert WeChat article content
- User mentions archiving or saving WeChat articles
- User needs article title, author, publish time, or body text from WeChat

## Prerequisites

- **kimi-webbridge daemon running** — check with:
  ```bash
  ~/.kimi-webbridge/bin/kimi-webbridge status
  ```
  Must show `running: true` and `extension_connected: true`. If not:
  ```bash
  ~/.kimi-webbridge/bin/kimi-webbridge start
  ```

- **`wechat-article-cli` installed** — verify with:
  ```bash
  wechat-article-cli --help
  ```
  If command not found, install first:
  ```bash
  npm install -g wechat-article-cli
  ```

## Installation

```bash
npm install -g wechat-article-cli
```

## Usage

### Fetch a single article

```bash
wechat-article-cli fetch <url>
```

**Input:**
- `url`: string, must be a WeChat article link (`mp.weixin.qq.com`)

**Output (stdout, JSON):**

Success:
```json
{
  "ok": true,
  "data": {
    "title": "文章标题",
    "author": "作者名",
    "time": "2026年5月21日",
    "markdown": "# 文章标题\n\n正文内容..."
  }
}
```

Error (non-zero exit):
```json
{
  "ok": false,
  "error": {
    "code": "...",
    "message": "..."
  }
}
```

## Error Codes and Recovery

| Code | Meaning | Recovery Action |
|------|---------|-----------------|
| `MISSING_ARG` | URL not provided | Ask user for the WeChat article URL |
| `INVALID_URL` | Not a mp.weixin.qq.com URL | Verify the URL format |
| `DAEMON_DOWN` | kimi-webbridge not running or extension not connected | Instruct user to run `~/.kimi-webbridge/bin/kimi-webbridge start` |
| `CAPTCHA_REQUIRED` | WeChat security verification triggered | Tell user to complete the slide verification in the browser, then retry with a short link (`mp.weixin.qq.com/s/xxxxx`) |
| `EXTRACTION_FAILED` | Article content not found | Retry once; if still failing, the article may be deleted or paywalled |
| `FETCH_ERROR` | Network or unexpected error | Report the specific error message to user |

## Environment

- `WEBBRIDGE_URL` — Override daemon URL (default: `http://127.0.0.1:10086`)

## Notes

- No login required for public articles.
- The tool opens a new browser tab, navigates to the article, polls until content loads (up to 15s), then extracts DOM and converts to Markdown.
- Images are converted to Markdown image syntax.
- Tables are converted to GFM table syntax.
- Code blocks preserve language identifiers when available.
- Session is auto-closed after extraction.
