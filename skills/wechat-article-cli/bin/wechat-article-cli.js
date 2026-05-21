#!/usr/bin/env node
const { fetchArticle } = require('../src/fetch');
const output = require('../src/output');

const HELP = `Usage: wechat-article-cli <command> [args]

Commands:
  fetch <url>     Fetch a WeChat article and output as Markdown JSON
  --help, -h      Show this help message

Environment:
  WEBBRIDGE_URL   kimi-webbridge daemon URL (default: http://127.0.0.1:10086)

Examples:
  wechat-article-cli fetch https://mp.weixin.qq.com/s/xxxxx
`;

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log(HELP);
    process.exit(0);
  }

  const command = args[0];

  if (command === 'fetch') {
    const url = args[1];
    const result = await fetchArticle(url);
    if (result.ok) {
      output.ok(result.data);
    } else {
      output.err(result.error.code, result.error.message);
    }
    return;
  }

  output.err('UNKNOWN_COMMAND', `Unknown command: ${command}. Use --help for usage.`);
}

main().catch((e) => {
  output.err('UNEXPECTED_ERROR', e.message || String(e));
});
