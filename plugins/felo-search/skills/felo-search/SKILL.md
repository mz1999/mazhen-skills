---
name: felo-search
description: "Felo AI real-time web search for questions requiring current/live information. Triggers on current events, news, trends, real-time data, information queries, location queries, how-to guides, shopping, or when Claude's knowledge may be outdated."
---

# Felo Search Skill

Felo AI provides AI-driven conversational search that generates intelligent answers based on real-time web search results, with cited sources and query analysis.

## When to Use

Trigger this skill for questions requiring current or real-time information:

- **Current events & news:** Recent developments, trending topics, breaking news
- **Real-time data:** Weather, stock prices, exchange rates, sports scores
- **Information queries:** "What is...", "Tell me about...", product reviews, comparisons, recommendations
- **Location-based:** Restaurants, travel destinations, local attractions, things to do
- **How-to guides:** Tutorials, step-by-step instructions, best practices
- **Shopping & prices:** Product prices, deals, "where to buy"
- **Trends & statistics:** Market trends, rankings, data analysis
- **Any question where Claude's knowledge may be outdated**

**Trigger words:**
- 简体中文: 最近、什么、哪里、怎么样、如何、查、搜、找、推荐、比较、新闻、天气
- 繁體中文: 最近、什麼、哪裡、怎麼樣、如何、查、搜、找、推薦、比較、新聞、天氣
- 日本語: 最近、何、どこ、どう、検索、探す、おすすめ、比較、ニュース、天気
- 한국어: 최근, 무엇, 어디, 어떻게
- English: latest, recent, what, where, how, best, search, find, compare, news, weather

**Explicit commands:** `/felo-search`, "search with felo", "felo search"

**Do NOT use for:**
- Code questions about the user's codebase (unless asking about external libraries/docs)
- Pure mathematical calculations or logical reasoning
- Questions about files in the current project

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

- AI-powered conversational answers
- Real-time web search results
- Cited sources with links and summaries
- Query analysis and optimization
- Rich formatted output with sources table
- JSON mode for programmatic use
- Multi-language support (Chinese, English, Japanese, Korean)
- Retry with exponential backoff for transient errors

## Rate Limits

- 100 requests per minute per API key
- Query length: 1-2000 characters

## Error Handling

### Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `INVALID_API_KEY` | API Key is invalid or revoked | Check if your API key is correct and hasn't been revoked |
| `MISSING_AUTHORIZATION` | Authorization header is missing | Ensure FELO_API_KEY is set correctly |
| `MALFORMED_AUTHORIZATION` | Authorization header format is incorrect | Use: Bearer YOUR_API_KEY |
| `MISSING_PARAMETER` | Required parameter is missing | Ensure the query parameter is provided |
| `INVALID_PARAMETER` | Parameter value is invalid | Check the query format |
| `QUERY_TOO_LONG` | Query exceeds 2000 characters limit | Shorten your query |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Slow down your requests (max 100/min) |
| `CHAT_FAILED` | Internal service error | Retry the request or contact Felo support |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | Wait and retry |

### HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API Key |
| 429 | Too Many Requests - Rate limit exceeded |
| 5xx | Server Error - Retry with backoff |

## Complete Examples

### Example 1: Weather query

**User asks:** "What's the weather in Tokyo today?"

**Expected response format:**
```
## Answer
Tokyo weather today: Sunny, 22°C (72°F). High of 25°C, low of 18°C.
Light winds from the east at 10 km/h. UV index: 6 (high).
Good day for outdoor activities!

## Query Analysis
Optimized queries: Tokyo weather today, 東京 天気 今日
```

**Bash command:**
```bash
uv run ${SKILL_DIR}/scripts/felo.py chat "What's the weather in Tokyo today?"
```

### Example 2: Local news / events

**User asks:** "What's new in Hangzhou recently?"

**Expected response format:**
```
## Answer
Recent news in Hangzhou: Asian Games venue upgrades completed, West Lake night tours launched, new metro lines opened. Details...

## Query Analysis
Optimized queries: Hangzhou recent news, Hangzhou events, 杭州 最近 新闻
```

**Bash command:**
```bash
uv run ${SKILL_DIR}/scripts/felo.py chat "What's new in Hangzhou recently?"
```

### Example 3: Travel / things to do

**User asks:** "What are the best things to do in Taipei?"

**Bash command:**
```bash
uv run ${SKILL_DIR}/scripts/felo.py chat "What are the best things to do in Taipei?"
```

### Example 4: Restaurants / recommendations

**User asks:** "Popular restaurants in Tokyo?"

**Bash command:**
```bash
uv run ${SKILL_DIR}/scripts/felo.py chat "Popular restaurants in Tokyo?"
```

### Example 5: JSON Output for Programmatic Use

**Agent executes:**
```bash
uv run ${SKILL_DIR}/scripts/felo.py chat "Latest AI news" --format json
```

**Expected output:**
```json
{
  "answer": "AI-generated answer text...",
  "resources": [...],
  "query_analysis": {...}
}
```

## Security Notes

- API Key is read from environment variables - never hardcoded
- API Key is never logged or displayed in output
- API Key is masked in configuration displays (shows first 4 and last 4 characters only)

## API

**Endpoint:** `POST https://openapi.felo.ai/v2/chat`

**Authentication:** Bearer token in Authorization header (from `FELO_API_KEY` environment variable)

**Request format:**
```json
{
  "query": "user's search query"
}
```

**Response format:**
```json
{
  "answer": "AI-generated comprehensive answer",
  "resources": [...],
  "query_analysis": {"queries": [...]}
}
```

## Additional Resources

- [Felo Open Platform Documentation](https://openapi.felo.ai)
- [Get API Key](https://felo.ai) (Settings → API Keys)
- [API Reference](https://openapi.felo.ai/docs)
