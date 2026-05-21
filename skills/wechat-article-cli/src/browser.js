const http = require('http');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);
const DAEMON_URL = process.env.WEBBRIDGE_URL || 'http://127.0.0.1:10086';

function request(action, args, session) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ action, args, session });
    const req = http.request(
      `${DAEMON_URL}/command`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
        timeout: 30000,
      },
      (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          try {
            const json = JSON.parse(data);
            if (!json.ok) {
              reject(new Error(json.error?.message || 'Unknown error'));
              return;
            }
            resolve(json.data);
          } catch (e) {
            reject(new Error(`Invalid JSON: ${data.slice(0, 200)}`));
          }
        });
        res.on('error', (err) => reject(new Error(`Response error: ${err.message}`)));
      }
    );
    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    req.write(body);
    req.end();
  });
}

async function status() {
  try {
    const { stdout } = await execAsync(`${process.env.HOME}/.kimi-webbridge/bin/kimi-webbridge status`);
    return JSON.parse(stdout.trim());
  } catch (e) {
    return { running: false, error: e.message };
  }
}

async function navigate(url, session) {
  return request('navigate', { url, newTab: true }, session);
}

async function evaluate(code, session) {
  const result = await request('evaluate', { code }, session);
  if (result.type === 'string') {
    try { return JSON.parse(result.value); } catch (e) { return result.value; }
  }
  return result;
}

async function snapshot(session) {
  return request('snapshot', {}, session);
}

async function closeSession(session) {
  try { await request('close_session', {}, session); } catch (e) { /* ignore */ }
}

module.exports = { status, navigate, evaluate, snapshot, closeSession };
