/* Spam-check regression tests for worker.js. Run with `npm test` in this
   directory (no install, no network — the Brevo call is stubbed, and an
   unexpected outbound fetch is a hard failure).

   These exist because every check in worker.js fails SILENTLY: a blocked
   request and a real signup return an identical {"success":true}. That is
   deliberate, but it means a bug that blocks real people looks exactly
   like everything working. The assertions below are on whether Brevo was
   actually reached, which is the only thing that distinguishes them. */

import worker from './worker.js';

// Stub Brevo so no real request leaves this machine.
let brevoCalls = 0;
globalThis.fetch = async (url) => {
  if (String(url).includes('api.brevo.com')) {
    brevoCalls++;
    return new Response(null, { status: 201 });
  }
  throw new Error('unexpected outbound fetch: ' + url);
};

const ORIGIN = 'https://midvaalmadmac.co.za';
const env = { BREVO_API_KEY: 'test-key' }; // no Turnstile, no rate limiter

function post(body, contentType = 'application/json') {
  return new Request('https://w.dev/', {
    method: 'POST',
    headers: { 'Content-Type': contentType, Origin: ORIGIN, 'CF-Connecting-IP': '1.2.3.4' },
    body: contentType === 'application/json' ? JSON.stringify(body) : new URLSearchParams(body),
  });
}

async function run(name, req, expect) {
  const before = brevoCalls;
  const res = await worker.fetch(req, env);
  const data = await res.json();
  const reached = brevoCalls > before;
  const ok = data.success === expect.success && reached === expect.reachedBrevo;
  console.log(
    `${ok ? 'PASS' : 'FAIL'}  ${name.padEnd(46)} status=${res.status} success=${data.success} brevo=${reached ? 'called' : 'blocked'}`
  );
  return ok;
}

const results = [];
results.push(await run('real signup (JS path, 8s elapsed)',
  post({ email: 'runner@example.com', company: '', _elapsed: '8000' }),
  { success: true, reachedBrevo: true }));

results.push(await run('no-JS fallback (form POST, no _elapsed)',
  post({ email: 'runner2@example.com' }, 'application/x-www-form-urlencoded'),
  { success: true, reachedBrevo: true }));

results.push(await run('honeypot filled -> silently discarded',
  post({ email: 'bot@example.com', company: 'Acme Corp', _elapsed: '9000' }),
  { success: true, reachedBrevo: false }));

results.push(await run('submitted in 40ms -> silently discarded',
  post({ email: 'bot2@example.com', company: '', _elapsed: '40' }),
  { success: true, reachedBrevo: false }));

results.push(await run('elapsed just under threshold (2499ms)',
  post({ email: 'bot3@example.com', _elapsed: '2499' }),
  { success: true, reachedBrevo: false }));

results.push(await run('elapsed just over threshold (2501ms)',
  post({ email: 'human@example.com', _elapsed: '2501' }),
  { success: true, reachedBrevo: true }));

results.push(await run('garbage _elapsed -> treated as absent, allowed',
  post({ email: 'human2@example.com', _elapsed: 'abc' }),
  { success: true, reachedBrevo: true }));

// invalid email still gets a truthful error, not a silent lie
{
  const res = await worker.fetch(post({ email: 'nope', _elapsed: '9000' }), env);
  const d = await res.json();
  const ok = res.status === 400 && d.success === false && d.error === 'invalid_email';
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${'invalid email -> honest 400'.padEnd(46)} status=${res.status} error=${d.error}`);
  results.push(ok);
}

// Turnstile configured but no token
{
  const res = await worker.fetch(
    post({ email: 'x@example.com', _elapsed: '9000' }),
    { ...env, TURNSTILE_SECRET: 'sec' }
  );
  const d = await res.json();
  const ok = d.success === true; // silent discard
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${'Turnstile on, no token -> discarded'.padEnd(46)} success=${d.success}`);
  results.push(ok);
}

// rate limiter says no
{
  const before = brevoCalls;
  const res = await worker.fetch(post({ email: 'y@example.com', _elapsed: '9000' }),
    { ...env, RATE_LIMITER: { limit: async () => ({ success: false }) } });
  const d = await res.json();
  const ok = d.success === true && brevoCalls === before;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${'rate limit exceeded -> discarded'.padEnd(46)} success=${d.success}`);
  results.push(ok);
}

console.log(`\n${results.filter(Boolean).length}/${results.length} passed · Brevo reached ${brevoCalls} times (only for genuine signups)`);
process.exit(results.every(Boolean) ? 0 : 1);
