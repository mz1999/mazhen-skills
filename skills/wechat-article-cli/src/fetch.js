const browser = require('./browser');
const { buildExtractionScript } = require('./extractor');

async function fetchArticle(url) {
  url = (url || '').trim();
  if (!url) {
    return { ok: false, error: { code: 'MISSING_ARG', message: 'URL is required. Usage: wechat-article-cli fetch <url>' } };
  }
  if (!url.startsWith('https://mp.weixin.qq.com/') && !url.startsWith('http://mp.weixin.qq.com/')) {
    return { ok: false, error: { code: 'INVALID_URL', message: 'URL must be a WeChat article link (mp.weixin.qq.com)' } };
  }

  let session;
  try {
    const st = await browser.status();
    if (!st.running || !st.extension_connected) {
      return { ok: false, error: { code: 'DAEMON_DOWN', message: 'kimi-webbridge daemon is not running or extension not connected. Run: ~/.kimi-webbridge/bin/kimi-webbridge start' } };
    }

    session = 'weixin-' + Date.now();

    await browser.navigate(url, session);

    const MAX_WAIT = 15000;
    const POLL_INTERVAL = 500;
    let waited = 0;
    let result = { ok: false, error: 'Timeout: Article content did not load within ' + MAX_WAIT + 'ms' };
    while (waited < MAX_WAIT) {
      await new Promise(r => setTimeout(r, POLL_INTERVAL));
      waited += POLL_INTERVAL;
      result = await browser.evaluate(buildExtractionScript(), session);
      if (result && result.ok) break;
      if (result && result.error && typeof result.error === 'string' && result.error.includes('CAPTCHA_REQUIRED')) break;
    }

    if (!result || !result.ok) {
      const msg = (result && result.error) || 'Failed to extract article content';
      return { ok: false, error: { code: 'EXTRACTION_FAILED', message: msg } };
    }

    return { ok: true, data: result.data };
  } catch (e) {
    return { ok: false, error: { code: 'FETCH_ERROR', message: e.message || String(e) } };
  } finally {
    if (session) {
      try { await browser.closeSession(session); } catch (_) {}
    }
  }
}

module.exports = { fetchArticle };
