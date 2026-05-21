# wechat-article-cli

Fetch WeChat public account (mp.weixin.qq.com) articles as Markdown via the real browser.

## Prerequisites

- [kimi-webbridge](https://github.com/your-org/kimi-webbridge) daemon running
- Node.js >= 18

Check daemon status:
```bash
~/.kimi-webbridge/bin/kimi-webbridge status
```

## Installation

```bash
npm install -g wechat-article-cli
```

## Usage

### Fetch a single article

```bash
wechat-article-cli fetch https://mp.weixin.qq.com/s/xxxxx
```

Output (JSON):
```json
{
  "ok": true,
  "data": {
    "title": "...",
    "author": "...",
    "time": "...",
    "markdown": "# ...\n\n..."
  }
}
```

### Environment Variables

- `WEBBRIDGE_URL` — Override daemon URL (default: `http://127.0.0.1:10086`)

## Features

- Extracts title, author, publish time, and full article content
- Converts HTML to Markdown: headings, bold, italic, lists, tables, code blocks, images, links
- Detects WeChat CAPTCHA/verification pages and returns clear error messages
- Polls until content loads (up to 15s), handles dynamic loading

## Error Codes

| Code | Meaning |
|------|---------|
| `MISSING_ARG` | URL not provided |
| `INVALID_URL` | Not a mp.weixin.qq.com URL |
| `DAEMON_DOWN` | kimi-webbridge daemon not running |
| `CAPTCHA_REQUIRED` | WeChat security verification triggered |
| `EXTRACTION_FAILED` | Article content not found on page |

## License

MIT
