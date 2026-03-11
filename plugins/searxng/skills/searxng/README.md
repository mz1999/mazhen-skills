# SearXNG Auth Skill

A Claude Skill for searching the web using your authenticated, self-hosted SearXNG instance.

## Overview

This skill allows you to search the web using a [SearXNG](https://github.com/searxng/searxng) instance that is protected with HTTP Basic Authentication. It's designed for users who:

- Self-host SearXNG on a public server
- Want to protect their search instance with authentication
- Need a secure, privacy-respecting search solution

## Prerequisites

1. A self-hosted SearXNG instance with HTTP Basic Auth enabled
2. Python 3.11 or higher
3. `uv` for running Python scripts

## Installation

```bash
claudespace skill add searxng-auth
```

## Configuration

Set the following environment variables:

```bash
export SEARXNG_URL="https://your-searxng-instance.com"
export SEARXNG_USERNAME="your-username"
export SEARXNG_PASSWORD="your-password"
```

### Configuring in Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "skills": {
    "searxng-auth": {
      "env": {
        "SEARXNG_URL": "https://your-searxng-instance.com",
        "SEARXNG_USERNAME": "your-username",
        "SEARXNG_PASSWORD": "your-password"
      }
    }
  }
}
```

## Usage

Once configured, you can use natural language to search:

```
search for Python async tutorials
look up climate change news
search web for docker compose examples
```

Or use the CLI directly:

```bash
uv run scripts/searxng.py search "Python async"
uv run scripts/searxng.py search "news" --category news --time-range day
uv run scripts/searxng.py search "cats" --category images -n 20
```

## Search Categories

- `general` - General web search (default)
- `images` - Image search
- `videos` - Video search
- `news` - News search
- `map` - Maps
- `music` - Music
- `files` - Files
- `it` - IT/Technology
- `science` - Science

## Output Formats

### Table Format (default)
Rich formatted table with columns for rank, title, URL, and source engines.

### JSON Format
```bash
uv run scripts/searxng.py search "query" --format json
```

Returns raw JSON for programmatic use.

## Security Best Practices

1. **Use HTTPS**: Always use HTTPS URLs for your SearXNG instance
2. **Strong Passwords**: Use a strong, unique password for HTTP Basic Auth
3. **Keep Credentials Secret**: Never commit credentials to version control
4. **SSL Verification**: This skill enables SSL verification by default

## Troubleshooting

### Authentication Failed (401)
- Check that `SEARXNG_USERNAME` and `SEARXNG_PASSWORD` are correct
- Verify your SearXNG instance requires HTTP Basic Auth

### Connection Error
- Verify `SEARXNG_URL` is correct and accessible
- Ensure your SearXNG instance is running

### Timeout Error
- Check network connectivity to your SearXNG instance
- Consider increasing timeout if your instance is slow

## License

MIT License - See [LICENSE](LICENSE) for details.
