"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.BOT_UA_DOMAINS = exports.BOT_UA = exports.DEFAULT_UA = void 0;
exports.getInitialUA = getInitialUA;
exports.fetchPage = fetchPage;
exports.extractRawMarkdown = extractRawMarkdown;
exports.cleanMarkdownContent = cleanMarkdownContent;
const MAX_SIZE = 5 * 1024 * 1024; // 5MB
const FETCH_TIMEOUT = 10000; // 10s
function getProxyUrl() {
    // Only use proxy in Node.js environment
    if (typeof process === 'undefined' || !process.env)
        return undefined;
    return process.env.DEFUDDLE_PROXY;
}
function validateProxyUrl(url) {
    try {
        const parsed = new URL(url);
        return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    }
    catch {
        return false;
    }
}
exports.DEFAULT_UA = 'Mozilla/5.0 (compatible; Defuddle/1.0; +https://defuddle.md)';
exports.BOT_UA = exports.DEFAULT_UA + ' bot';
// Domains that serve better content to bot user agents (e.g. SSR vs client-rendered)
exports.BOT_UA_DOMAINS = ['github.com'];
function getInitialUA(targetUrl) {
    try {
        const hostname = new URL(targetUrl).hostname;
        if (exports.BOT_UA_DOMAINS.some(d => hostname === d || hostname.endsWith('.' + d))) {
            return exports.BOT_UA;
        }
    }
    catch { }
    return exports.DEFAULT_UA;
}
async function fetchWithNative(targetUrl, headers, signal) {
    return fetch(targetUrl, {
        headers,
        redirect: 'follow',
        signal,
    });
}
async function fetchWithProxy(targetUrl, headers, signal, proxyUrl) {
    const undici = await Promise.resolve().then(() => __importStar(require('undici')));
    const proxyAgent = new undici.ProxyAgent(proxyUrl);
    const fetchOptions = {
        headers,
        redirect: 'follow',
        signal,
        dispatcher: proxyAgent,
    };
    return undici.fetch(targetUrl, fetchOptions);
}
async function fetchPage(targetUrl, userAgent, options = {}) {
    const { language, debug = false, useProxy = false } = options;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
    try {
        const headers = {
            'User-Agent': userAgent,
            'Accept': 'text/html,application/xhtml+xml',
        };
        if (language) {
            headers['Accept-Language'] = language;
        }
        const proxyUrl = useProxy ? getProxyUrl() : undefined;
        let response;
        if (proxyUrl && validateProxyUrl(proxyUrl)) {
            try {
                response = await fetchWithProxy(targetUrl, headers, controller.signal, proxyUrl);
            }
            catch (err) {
                if (debug) {
                    console.warn(`[defuddle] Failed to use proxy: ${err instanceof Error ? err.message : 'Unknown error'}`);
                    console.warn(`[defuddle] Falling back to direct connection`);
                }
                response = await fetchWithNative(targetUrl, headers, controller.signal);
            }
        }
        else {
            if (proxyUrl && debug) {
                console.warn(`[defuddle] Invalid proxy URL: ${proxyUrl}`);
                console.warn(`[defuddle] Proxy URL must be a valid http:// or https:// URL`);
                console.warn(`[defuddle] Falling back to direct connection`);
            }
            response = await fetchWithNative(targetUrl, headers, controller.signal);
        }
        if (!response.ok) {
            throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
        }
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('text/html') && !contentType.includes('application/xhtml+xml')) {
            throw new Error(`Not an HTML page (content-type: ${contentType})`);
        }
        const contentLength = response.headers.get('content-length');
        if (contentLength && parseInt(contentLength) > MAX_SIZE) {
            throw new Error(`Page too large (${Math.round(parseInt(contentLength) / 1024 / 1024)}MB, max 5MB)`);
        }
        const buffer = await response.arrayBuffer();
        if (buffer.byteLength > MAX_SIZE) {
            throw new Error(`Page too large (${Math.round(buffer.byteLength / 1024 / 1024)}MB, max 5MB)`);
        }
        return decodeHtml(buffer, contentType);
    }
    catch (err) {
        if (err.name === 'AbortError') {
            throw new Error(`Timed out fetching page after ${FETCH_TIMEOUT / 1000}s`);
        }
        throw err;
    }
    finally {
        clearTimeout(timer);
    }
}
// Windows-1252 bytes 0x80-0x9F that differ from ISO-8859-1/Unicode
const WIN1252 = {
    0x80: 0x20AC, 0x82: 0x201A, 0x83: 0x0192, 0x84: 0x201E, 0x85: 0x2026, 0x86: 0x2020,
    0x87: 0x2021, 0x88: 0x02C6, 0x89: 0x2030, 0x8A: 0x0160, 0x8B: 0x2039, 0x8C: 0x0152,
    0x8E: 0x017D, 0x91: 0x2018, 0x92: 0x2019, 0x93: 0x201C, 0x94: 0x201D, 0x95: 0x2022,
    0x96: 0x2013, 0x97: 0x2014, 0x98: 0x02DC, 0x99: 0x2122, 0x9A: 0x0161, 0x9B: 0x203A,
    0x9C: 0x0153, 0x9E: 0x017E, 0x9F: 0x0178,
};
function decodeWindows1252(buffer) {
    const bytes = new Uint8Array(buffer);
    const CHUNK = 8192;
    const parts = [];
    for (let i = 0; i < bytes.length; i += CHUNK) {
        const slice = bytes.subarray(i, Math.min(i + CHUNK, bytes.length));
        const mapped = new Uint16Array(slice.length);
        for (let j = 0; j < slice.length; j++) {
            mapped[j] = WIN1252[slice[j]] ?? slice[j];
        }
        parts.push(String.fromCharCode(...mapped));
    }
    return parts.join('');
}
function detectCharset(contentType, buffer) {
    const headerMatch = contentType.match(/charset=([^\s;]+)/i);
    if (headerMatch)
        return headerMatch[1].toLowerCase();
    const head = new TextDecoder('latin1').decode(buffer.slice(0, 1024));
    const metaCharset = head.match(/<meta[^>]+charset=["']?([^\s"';>]+)/i);
    if (metaCharset)
        return metaCharset[1].toLowerCase();
    const metaHttpEquiv = head.match(/<meta[^>]+content=["'][^"']*charset=([^\s"';]+)/i);
    if (metaHttpEquiv)
        return metaHttpEquiv[1].toLowerCase();
    const bytes = new Uint8Array(buffer, 0, Math.min(buffer.byteLength, 8192));
    for (let i = 0; i < bytes.length; i++) {
        const b = bytes[i];
        if (b >= 0x80 && b <= 0x9F)
            return 'windows-1252';
        if (b >= 0xC0 && b <= 0xF7) {
            const seqLen = b < 0xE0 ? 2 : b < 0xF0 ? 3 : 4;
            let valid = true;
            for (let j = 1; j < seqLen && i + j < bytes.length; j++) {
                if ((bytes[i + j] & 0xC0) !== 0x80) {
                    valid = false;
                    break;
                }
            }
            if (valid) {
                i += seqLen - 1;
                continue;
            }
            return 'windows-1252';
        }
    }
    return 'utf-8';
}
function decodeHtml(buffer, contentType) {
    const charset = detectCharset(contentType, buffer);
    if (charset === 'windows-1252' || charset === 'iso-8859-1' || charset === 'latin1') {
        return decodeWindows1252(buffer);
    }
    return new TextDecoder(charset).decode(buffer);
}
/**
 * Extract raw markdown from HTML before DOM parsing.
 * Some sites (e.g. Obsidian Publish) embed raw markdown in a text node
 * for bot user agents. DOM parsing destroys whitespace like tab indentation,
 * so we extract it from the raw HTML string.
 */
function extractRawMarkdown(html) {
    const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    if (!bodyMatch)
        return null;
    const textContent = bodyMatch[1]
        .replace(/<(script|style|noscript)[^>]*>[\s\S]*?<\/\1>/gi, '')
        .replace(/<[^>]+>/g, '')
        .trim();
    if (!textContent || !isMarkdownContent(textContent))
        return null;
    return textContent;
}
function isMarkdownContent(content) {
    let signals = 0;
    if (/^#{1,6}\s+\S/m.test(content))
        signals++;
    if (/\*\*[^*\n]+\*\*/m.test(content))
        signals++;
    if (/\[[^\]]+\]\([^)]+\)/m.test(content))
        signals++;
    if (/^\s*[-*+]\s+\S/m.test(content))
        signals++;
    if (/^\s*\d+\.\s+\S/m.test(content))
        signals++;
    if (/^>\s+\S/m.test(content))
        signals++;
    if (/```/m.test(content))
        signals++;
    return signals >= 2;
}
function cleanMarkdownContent(content) {
    let markdown = content
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .trim();
    const titleMatch = markdown.match(/^# .+\n+/);
    if (titleMatch) {
        markdown = markdown.slice(titleMatch[0].length);
    }
    markdown = markdown.replace(/\n{3,}/g, '\n\n');
    return markdown.trim();
}
//# sourceMappingURL=fetch.js.map