#!/usr/bin/env node
const { fetchArticle } = require('./src/fetch');

const articles = [
  { title: '都是 AI Coding，为什么 Java 体验差了一个量级？', url: 'https://mp.weixin.qq.com/s?__biz=MzIzOTU0NTQ0MA==&mid=2247560145&idx=1&sn=ae14d8af22600c85a92201ef28517016' },
  { title: '来自 Codex 官方团队的分享：如何把 Codex 用到极致', url: 'https://mp.weixin.qq.com/s?__biz=Mzk1NzgxMjQ0OA==&mid=2247494887&idx=1&sn=93bb0d1594df9d8311681c69d5f25861' },
  { title: 'QQ音乐Harness Engineering实践', url: 'https://mp.weixin.qq.com/s?__biz=MzI2NDU4OTExOQ==&mid=2247695581&idx=1&sn=08aacd344637c9eba04e75e9fae2354c' },
  { title: '首个 Java Harness Framework 来了丨AgentScope', url: 'https://mp.weixin.qq.com/s?__biz=MzUzNzYxNjAzMg==&mid=2247583906&idx=1&sn=54dfcf23fa15e732c4ad1fa70bf6b0e4' },
  { title: '从0开发大模型的17种Agent架构演进详细拆解', url: 'https://mp.weixin.qq.com/s?__biz=MjM5ODYwMjI2MA==&mid=2649801545&idx=1&sn=b2d15c583715f519cbec484e8b10abdf' },
  { title: '腾讯开源Agent Memory，让Token消耗降低61%', url: 'https://mp.weixin.qq.com/s?__biz=MjM5MDgwMzc4MA==&mid=2654907713&idx=1&sn=85adc5b5cd76b73bb3460e74ce867513' },
  { title: '从上下文污染到多 Agent 分工：AI Coding Agent 如何工程化', url: 'https://mp.weixin.qq.com/s?__biz=Mzk0MjI4Nzc3Mw==&mid=2247488753&idx=1&sn=d5a9d848f61d8cba7d05aa7059bab6d9' },
  { title: '从零设计生产级 Multi-Agent Harness', url: 'https://mp.weixin.qq.com/s?__biz=MzI2NDU4OTExOQ==&mid=2247695544&idx=1&sn=865fb183130b2851900b9f4eda62da9c' },
  { title: '深度解析LLM Wiki / Obsidian-Wiki / GBrain', url: 'https://mp.weixin.qq.com/s?__biz=MzIzOTU0NTQ0MA==&mid=2247559971&idx=1&sn=e93c802829515223ad1dbb15de073b59' },
  { title: '拆完Hermes源码，我发现Agent的自我进化', url: 'https://mp.weixin.qq.com/s?__biz=MzI2NDU4OTExOQ==&mid=2247695500&idx=1&sn=57de8c7c4889ace8c6c1e15ab460447a' },
  { title: '深度拆解：AI 智能体 Harness 的构造【译】', url: 'https://mp.weixin.qq.com/s?__biz=Mzk1NzgxMjQ0OA==&mid=2247494817&idx=1&sn=f22c6d9af7323504d323a0453d6d4bc6' },
  { title: '第一个 Agent 从 Pi 开始', url: 'https://mp.weixin.qq.com/s?__biz=MzIzNjE2NTI3NQ==&mid=2247491875&idx=1&sn=032b282f98aa1daad1d8d8d82c0adb3f' },
  { title: '开发流程 skill 化', url: 'https://mp.weixin.qq.com/s?__biz=Mzk0MDIwNzM2MA==&mid=2247485155&idx=1&sn=d32701dcaceb93f621b470a3fc0acdf2' },
  { title: 'Karpathy 最新访谈：Vibe Coding 只是开始', url: 'https://mp.weixin.qq.com/s?__biz=Mzk1NzgxMjQ0OA==&mid=2247494701&idx=1&sn=eed8f9766a80a8130460e10c3b79637f' },
  { title: '万字干货｜AI 时代的 Git 版本管理，你用对了吗？', url: 'https://mp.weixin.qq.com/s?__biz=MzkxMTY4NTAyNQ==&mid=2247510348&idx=1&sn=0eaed4bb608369011819fade6a28a188' },
  { title: '你不知道的 Agent：原理、架构与工程实践', url: 'https://mp.weixin.qq.com/s?__biz=MzIzOTU0NTQ0MA==&mid=2247559745&idx=1&sn=31903f96e842d95a2fa2f6b5a5a012cc' },
  { title: 'SOLO 必装的 14个 Skills，看这一篇就够了', url: 'https://mp.weixin.qq.com/s?__biz=MzkxMTY4NTAyNQ==&mid=2247509974&idx=1&sn=cd5a7a08e13c2dd00b4d6961ee1c230d' },
  { title: '深度解析 Claude Code 在 Prompt / Context / Harness 的设计与实践', url: 'https://mp.weixin.qq.com/s?__biz=MzIzOTU0NTQ0MA==&mid=2247559627&idx=1&sn=7847089f5135e5060953f013fa56fd4f' },
  { title: '我做了个 Skill：让 AI 帮你生成 Logo 和图标', url: 'https://mp.weixin.qq.com/s?__biz=MzU0MDk3NTUxMA==&mid=2247496504&idx=1&sn=a24aa3dcf5efbbdb78522f0e290ebc1d' },
  { title: '可算有解决Claude降智和偷Token的神配置了', url: 'https://mp.weixin.qq.com/s?__biz=Mzg3MTk3NzYzNw==&mid=2247506380&idx=1&sn=61a5e32ac2ce7477db9d8a1c3dce0f0d' },
];

async function test() {
  console.log(`Batch testing ${articles.length} articles...\n`);
  const results = [];

  for (let i = 0; i < articles.length; i++) {
    const { title, url } = articles[i];
    process.stdout.write(`[${String(i + 1).padStart(2, '0')}/${articles.length}] ${title.slice(0, 40)}... `);

    try {
      const data = await fetchArticle(url);
      if (data.ok) {
        const mdLen = data.data.markdown?.length || 0;
        const extractedTitle = data.data.title || '';
        const author = data.data.author || '';
        console.log(`OK | title=${extractedTitle.slice(0, 30)} | author=${author.slice(0, 15)} | ${mdLen} chars`);
        results.push({ idx: i + 1, expected: title, status: 'OK', title: extractedTitle, author, mdLen });
      } else {
        console.log(`FAIL | code=${data.error?.code} | ${data.error?.message?.slice(0, 60)}`);
        results.push({ idx: i + 1, expected: title, status: 'FAIL', error: data.error });
      }
    } catch (e) {
      const msg = e.message?.slice(0, 100) || 'unknown';
      console.log(`ERROR | ${msg}`);
      results.push({ idx: i + 1, expected: title, status: 'ERROR', error: msg });
    }

    if (i < articles.length - 1) {
      await new Promise(r => setTimeout(r, 500));
    }
  }

  console.log('\n=== Summary ===');
  const ok = results.filter(r => r.status === 'OK').length;
  const fail = results.filter(r => r.status === 'FAIL').length;
  const err = results.filter(r => r.status === 'ERROR').length;
  console.log(`Total: ${articles.length} | OK: ${ok} | FAIL: ${fail} | ERROR: ${err}`);

  if (fail + err > 0) {
    console.log('\n=== Failed / Error ===');
    results.filter(r => r.status !== 'OK').forEach(r => {
      console.log(`  [${r.idx}] ${r.expected.slice(0, 40)}... -> ${r.status}: ${r.error?.code || r.error || ''}`);
    });
  }
}

test();
