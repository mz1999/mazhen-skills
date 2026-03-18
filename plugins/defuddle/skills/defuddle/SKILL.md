---
name: defuddle
description: Extract clean markdown content from web pages using Defuddle CLI with proxy support. Prefer over WebFetch for standard web pages — it removes navigation, ads, and clutter, reducing token usage.
---

# Defuddle

Extract clean readable content from web pages using Defuddle CLI with HTTP proxy support. Prefer over WebFetch for standard web pages — it removes navigation, ads, and clutter, reducing token usage.

## Installation

```bash
npm install -g @mz1999/defuddle
```

## Usage

### Basic Fetch (Markdown)

```bash
defuddle parse <url> --md
```

### Output as JSON with metadata

```bash
defuddle parse <url> --json
```

### Extract specific property

```bash
defuddle parse <url> -p title
defuddle parse <url> -p description
defuddle parse <url> -p domain
```

### Save to file

```bash
defuddle parse <url> --md -o content.md
```

## Proxy Support

Defuddle supports HTTP/HTTPS proxies via the `DEFUDDLE_PROXY` environment variable.

```bash
export DEFUDDLE_PROXY=http://proxy.example.com:8080
defuddle parse https://example.com/article --md
```

## Output Formats

| Flag | Format |
|------|--------|
| `--md` | Markdown (default choice) |
| `--json` | JSON with both HTML and markdown |
| (none) | HTML |
| `-p <name>` | Specific metadata property |

## CLI Options

| Option | Alias | Description |
|--------|-------|-------------|
| `--output <file>` | `-o` | Write output to a file instead of stdout |
| `--markdown` | `-m` | Convert content to markdown format |
| `--md` | | Alias for `--markdown` |
| `--json` | `-j` | Output as JSON with metadata and content |
| `--property <name>` | `-p` | Extract a specific property |
| `--debug` | | Enable debug mode |
| `--lang <code>` | `-l` | Preferred language (BCP 47, e.g. `en`, `fr`, `ja`) |

## Response Fields

When using `--json`, the response includes:

| Property | Type | Description |
|----------|------|-------------|
| `title` | string | Article title |
| `content` | string | Cleaned content (HTML or markdown) |
| `author` | string | Author of the article |
| `description` | string | Description or summary |
| `domain` | string | Domain name of the website |
| `favicon` | string | URL of the website's favicon |
| `image` | string | URL of the article's main image |
| `language` | string | Language of the page |
| `published` | string | Publication date |
| `site` | string | Name of the website |
| `wordCount` | number | Total word count |
| `parseTime` | number | Time taken to parse in milliseconds |
