function ok(data) {
  console.log(JSON.stringify({ ok: true, data }, null, 2));
  process.exit(0);
}

function err(code, message) {
  console.log(JSON.stringify({ ok: false, error: { code, message } }, null, 2));
  process.exit(1);
}

module.exports = { ok, err };
