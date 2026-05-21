function escapeMarkdown(text) {
  return text.replace(/([\\`*_{}[$#+\-.!|])/g, '\\$1');
}

function extractionScript() {
  const article = document.querySelector('#js_content');
  const titleEl = document.querySelector('.rich_media_title');

  const authorSelectors = [
    '#js_name',
    '.profile_nickname',
    '#js_profile_qrcode .profile_nickname',
    '.wx_follow_nickname',
    '#js_wx_follow_nickname',
    '.nickNameSpan',
  ];
  let authorEl = null;
  for (const sel of authorSelectors) {
    authorEl = document.querySelector(sel);
    if (authorEl && authorEl.innerText.trim()) break;
  }

  const metaTime = document.querySelector('#publish_time');

  // Detect WeChat CAPTCHA / verification page
  const verifyBtn = document.querySelector('#js_verify');
  const captchaTitle = document.querySelector('.weui-msg__title');
  if (verifyBtn || (captchaTitle && captchaTitle.innerText.includes('环境异常'))) {
    return JSON.stringify({ ok: false, error: 'CAPTCHA_REQUIRED: WeChat security verification triggered. Long links (__biz=) often require verification. Use short links (mp.weixin.qq.com/s/xxxxx) or complete verification manually in the browser first.' });
  }

  if (!article) return JSON.stringify({ ok: false, error: 'Article content not found' });

  function convertChildren(node, indent) {
    indent = indent || '';
    let result = '';
    for (const c of node.childNodes) {
      result += convertNode(c, indent);
    }
    return result;
  }

  function convertNode(node, indent) {
    indent = indent || '';
    if (node.nodeType === 3) {
      let t = node.textContent || '';
      t = t.replace(/\s+/g, ' ').trim();
      return escapeMarkdown(t);
    }
    if (node.nodeType !== 1) return '';
    const tag = node.tagName.toLowerCase();
    if (tag === 'script' || tag === 'style' || tag === 'iframe') return '';

    // <code> inside <pre> is handled by <pre>
    if (tag === 'code' && node.parentElement && node.parentElement.tagName.toLowerCase() === 'pre') {
      return '';
    }

    switch (tag) {
      case 'br': return '\n';
      case 'hr': return '\n---\n';
      case 'img': {
        const src = node.getAttribute('data-src') || node.src || '';
        const alt = node.alt || '';
        return src ? '![' + alt + '](' + src.split('?')[0] + ')\n\n' : '';
      }
      case 'a': {
        const href = node.href || '';
        const text = convertChildren(node, indent).trim();
        return href ? '[' + text + '](' + href + ')' : text;
      }
      case 'strong':
      case 'b': {
        const text = convertChildren(node, indent).trim();
        return text ? '**' + text + '**' : '';
      }
      case 'em':
      case 'i': {
        const text = convertChildren(node, indent).trim();
        return text ? '*' + text + '*' : '';
      }
      case 's':
      case 'del':
      case 'strike': {
        const text = convertChildren(node, indent).trim();
        return text ? '~~' + text + '~~' : '';
      }
      case 'pre': {
        const codeEl = node.querySelector('code');
        let lang = '';
        if (codeEl) {
          const cls = codeEl.className || '';
          const m = cls.match(/(?:language|lang)-([\w+]+)/);
          if (m) lang = m[1];
        }
        const text = node.innerText.trim();
        return text ? '\n\n```' + lang + '\n' + text + '\n```\n\n' : '';
      }
      case 'code': {
        const text = convertChildren(node, indent).trim();
        return text ? '`' + text + '`' : '';
      }
      case 'blockquote': {
        const text = convertChildren(node, indent).trim();
        return text ? '> ' + text.replace(/\n/g, '\n> ') + '\n\n' : '';
      }
      case 'h1': {
        const text = convertChildren(node, indent).trim();
        return text ? '# ' + text + '\n\n' : '';
      }
      case 'h2': {
        const text = convertChildren(node, indent).trim();
        return text ? '## ' + text + '\n\n' : '';
      }
      case 'h3': {
        const text = convertChildren(node, indent).trim();
        return text ? '### ' + text + '\n\n' : '';
      }
      case 'h4':
      case 'h5':
      case 'h6': {
        const text = convertChildren(node, indent).trim();
        return text ? '#### ' + text + '\n\n' : '';
      }
      case 'ul': {
        let result = '';
        for (const c of node.childNodes) {
          if (c.nodeType === 1 && c.tagName.toLowerCase() === 'li') {
            const liText = convertChildren(c, indent + '  ').trim();
            if (liText) result += indent + '- ' + liText + '\n';
          } else if (c.nodeType === 1) {
            result += convertNode(c, indent);
          }
        }
        return result ? result + '\n' : '';
      }
      case 'ol': {
        let result = '';
        let idx = 1;
        for (const c of node.childNodes) {
          if (c.nodeType === 1 && c.tagName.toLowerCase() === 'li') {
            const liText = convertChildren(c, indent + '  ').trim();
            if (liText) result += indent + idx + '. ' + liText + '\n';
            idx++;
          } else if (c.nodeType === 1) {
            result += convertNode(c, indent);
          }
        }
        return result ? result + '\n' : '';
      }
      case 'li': {
        const text = convertChildren(node, indent).trim();
        return text ? indent + '- ' + text + '\n' : '';
      }
      case 'p': {
        const text = convertChildren(node, indent).trim();
        return text ? text + '\n\n' : '';
      }
      case 'section':
      case 'div': {
        const text = convertChildren(node, indent).trim();
        return text ? text + '\n\n' : '';
      }
      case 'table': {
        let rows = [];
        const trs = node.querySelectorAll('tr');
        let separatorAdded = false;
        for (let i = 0; i < trs.length; i++) {
          const tr = trs[i];
          let cells = [];
          let hasTh = false;
          for (const cell of tr.children) {
            const tag = cell.tagName.toLowerCase();
            if (tag === 'th') hasTh = true;
            if (tag === 'td' || tag === 'th') {
              const text = convertChildren(cell, indent).trim();
              cells.push(text || ' ');
            }
          }
          if (cells.length > 0) {
            rows.push('| ' + cells.join(' | ') + ' |');
            if (!separatorAdded && (i === 0 || hasTh)) {
              rows.push('| ' + cells.map(() => '---').join(' | ') + ' |');
              separatorAdded = true;
            }
          }
        }
        return rows.length > 0 ? '\n' + rows.join('\n') + '\n\n' : '';
      }
      case 'span': {
        return convertChildren(node, indent).trim();
      }
      default: {
        return convertChildren(node, indent).trim();
      }
    }
  }

  const md = convertNode(article).replace(/\n{3,}/g, '\n\n').trim();

  return JSON.stringify({
    ok: true,
    data: {
      title: (titleEl ? titleEl.innerText.trim() : ''),
      author: (authorEl ? authorEl.innerText.trim() : ''),
      time: (metaTime ? metaTime.innerText.trim() : ''),
      markdown: md,
    },
  });
}

function buildExtractionScript() {
  return `(${extractionScript.toString()})()`;
}

module.exports = { buildExtractionScript };
