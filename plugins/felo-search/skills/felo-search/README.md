# Felo Search Skill for Claude Code

**Real-time web search with AI-generated answers.**

Get current information on anything - weather, news, tech docs, reviews, prices. Works in Chinese, English, Japanese, and Korean.

---

## What It Does

Felo Search integrates [Felo AI](https://felo.ai) into Claude Code, enabling:
- Real-time web search for current information
- AI-generated comprehensive answers
- Multi-language support (auto-detects query language)
- Automatic triggering for questions needing current data

**When to use:**
- Current events, news, weather
- Product reviews, prices, comparisons
- Latest documentation, tech trends
- Location info (restaurants, attractions)
- Any question with "latest", "recent", "best", "how to"

**When NOT to use:**
- Code questions about your local project
- Pure math or logic problems
- Questions about files in your workspace

---

## Quick Setup

### Step 1: Install

```bash
npx @anthropic-ai/skills add felo-search
```

**Verify:** Restart Claude Code and run:
```bash
claude skills list
```

You should see `felo-search` in the output.

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

**Windows (CMD):**
```cmd
set FELO_API_KEY=your-api-key-here
```

**Verify:** Check the variable is set:
```bash
# Linux/macOS
echo $FELO_API_KEY

# Windows PowerShell
echo $env:FELO_API_KEY
```

You should see your API key.

**Restart Claude Code** to load the environment variable.

### Step 4: Test

Ask Claude a question requiring current information:
```
What's the weather in Tokyo today?
```

If you see an AI-generated answer, **you're all set!**

---

## Usage Examples

### Daily Life

**Weather**
```
You: What's the weather in Tokyo today?
Claude: Currently 15°C in Tokyo with partly cloudy skies. High of 18°C,
        low of 12°C. 20% chance of rain.

You: What's the weather in Hangzhou tomorrow?
Claude: Hangzhou tomorrow: partly cloudy to clear, 8-16°C, NE wind 3-4.
```

**Restaurants & Food**
```
You: Best ramen in Osaka
Claude: Top 3 ramen shops in Osaka:
        1. Ichiran Dotonbori - Famous tonkotsu ramen, open 24/7
        2. Kamukura - Rich chicken broth, Michelin Bib Gourmand
        3. Menya Joroku - Tsukemen specialist

You: Where to find the best xiaolongbao in Shanghai?
Claude: Shanghai xiaolongbao recommendations:
        1. Nanxiang Steamed Bun - Old brand near Yuyuan, thin skin, juicy
        2. Jiajia Soup Dumplings - Popular on Huanghe Road, good value
        3. Din Tai Fung - Taiwan brand, consistent quality
```

**Shopping & Prices**
```
You: iPhone 16 Pro price comparison
Claude: iPhone 16 Pro (128GB) prices:
        - Apple Store: $999
        - Amazon: $979 (save $20)
        - Best Buy: $999 (with trade-in deals)
```

**Travel**
```
You: Things to do in Kyoto this weekend
Claude: Kyoto weekend highlights:
        - Fushimi Inari Shrine (open 24/7, less crowded early morning)
        - Nishiki Market food tour (closes 6pm)
        - Gion district evening walk (geisha spotting)

You: What to do in Taipei?
Claude: Taipei must-sees:
        - Taipei 101 - Observatory for night views
        - National Palace Museum - Chinese art and artifacts
        - Shilin Night Market - Food and snacks
        - Jiufen Old Street - Nostalgic mountain town
```

### Developer Scenarios

**Latest Documentation**
```
You: React 19 new features
Claude: React 19 key features:
        - React Compiler (auto-optimization)
        - Server Components stable
        - Actions for form handling
        - use() hook for async data

You: Next.js 15 new features
Claude: Next.js 15 main updates:
        - Turbopack stable (5x faster builds)
        - Partial Prerendering (PPR)
        - Improved cache control
        - React 19 support
```

**Library Comparison**
```
You: Vite vs Webpack 2025 comparison
Claude: Vite vs Webpack (2025):

        Build Speed: Vite 10x faster (dev), 3x faster (prod)
        Config: Vite simpler, Webpack more flexible
        Ecosystem: Webpack mature, Vite growing fast

        Use Vite for: New projects, fast iteration
        Use Webpack for: Complex builds, legacy support
```

**Tech Trends**
```
You: Latest AI developments 2026
Claude: AI developments (2026):
        - OpenAI GPT-5 preview released
        - Google Gemini 2.0 with multimodal reasoning
        - Anthropic Claude 4 with extended context
        - Meta's open-source LLaMA 4
```

### Multi-language Queries

Felo supports Chinese, Japanese, Korean, and English. Ask in any language and get answers in that language.

**简体中文:**
```
You: 杭州最近有什么新鲜事？
You: 北京最好的烤鸭店在哪里？
```

**日本語:**
```
You: 東京で今人気のレストランは？
You: 京都のおすすめ観光スポット
```

**한국어:**
```
You: 서울에서 가장 인기 있는 맛집은?
You: 최근 AI 기술 동향
```

---

## How It Works

### Auto-trigger

The skill automatically triggers for questions containing:
- **Time-sensitive**: "latest", "recent", "today", "now"
- **Information**: "what is", "tell me about", "how to"
- **Comparison**: "best", "top", "vs", "compare"
- **Location**: "where", "in [city]", "near me"
- **Chinese**: "最近", "什么", "哪里", "怎么样"
- **Japanese**: "最近", "何", "どこ", "どう"
- **Korean**: "최근", "무엇", "어디", "어떻게"

### Manual Trigger

Force the skill to run:
```
/felo-search your query here
```

Or use trigger phrases:
```
Search with Felo for [query]
Felo search: [query]
Use Felo to find [query]
```

### Response Format

Each response includes:

1. **Answer** - AI-generated comprehensive answer
2. **Sources** - Web sources with links and summaries
3. **Query Analysis** - Optimized search queries used by Felo

Example:
```
## Answer
[Comprehensive AI-generated answer]

## Sources
1. [Source Title] - https://example.com
   Summary of the source...

## Query Analysis
Optimized queries: ["query 1", "query 2"]
```

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

### JSON Output

For programmatic use, output in JSON format:

```bash
uv run skills/felo-search/scripts/felo.py chat "your query" --format json
```

---

## Troubleshooting

### "FELO_API_KEY not set" error

**Problem:** Environment variable not configured.

**Solution:**
```bash
# Linux/macOS
export FELO_API_KEY="your-key"

# Windows PowerShell
$env:FELO_API_KEY="your-key"
```

Then restart Claude Code.

### "INVALID_API_KEY" error

**Problem:** API key is incorrect or revoked.

**Solution:** Generate a new key at [felo.ai](https://felo.ai) (Settings → API Keys).

### Skill not triggering automatically

**Problem:** Query doesn't match trigger keywords.

**Solution:** Use manual trigger:
```
/felo-search your query
```

### Character encoding issues (Chinese/Japanese/Korean)

**Problem:** Special characters not displaying correctly.

**Solution:** Ensure your terminal supports UTF-8 encoding.

---

## Links

- **[Get API Key](https://felo.ai)** - Settings → API Keys
- **[API Documentation](https://openapi.felo.ai)** - Full API reference
- **[Report Issues](https://github.com/Felo-Inc/felo-skills/issues)** - Bug reports and feature requests

---

## License

MIT License - see [LICENSE](./LICENSE) for details.
