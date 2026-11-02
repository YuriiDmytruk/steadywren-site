// Tests the contact handler with plain Node (no Cloudflare runtime): node worker/test.mjs
import assert from 'node:assert/strict';
import { handle, validate } from './src/handler.js';

const env = { FROM: 'contact@steadywren.com', TO: 'owner@example.com', ALLOWED_ORIGINS: 'https://steadywren.com' };
const post = (body, origin = 'https://steadywren.com') => new Request('https://api.steadywren.com/contact', {
    method: 'POST', headers: { 'Content-Type': 'application/json', Origin: origin }, body: JSON.stringify(body),
});
const good = { email: 'buyer@company.com', message: 'Need a scraper for X with weekly runs.', topics: ['Apify'] };

let sent = [];
const send = async (from, to, raw) => { sent.push({ from, to, raw }); };

// valid message is sent, Reply-To is the visitor, CORS allows the site
let res = await handle(post(good), env, send);
assert.equal(res.status, 200);
assert.equal(res.headers.get('Access-Control-Allow-Origin'), 'https://steadywren.com');
assert.equal(sent.length, 1);
assert.equal(sent[0].to, 'owner@example.com');
assert.match(sent[0].raw, /Reply-To: buyer@company\.com/);
const bodyText = Buffer.from(sent[0].raw.split('\r\n\r\n')[1].replace(/\r\n/g, ''), 'base64').toString('utf8');
assert.match(bodyText, /Need a scraper for X/);
assert.match(bodyText, /About: Apify/);
assert.match(sent[0].raw, /Subject: =\?UTF-8\?B\?/);

// honeypot: 200 but nothing sent
sent = [];
res = await handle(post({ ...good, website: 'http://spam' }), env, send);
assert.equal(res.status, 200);
assert.equal(sent.length, 0);

// invalid input
assert.equal((await handle(post({ ...good, email: 'nope' }), env, send)).status, 400);
assert.equal((await handle(post({ ...good, message: 'short' }), env, send)).status, 400);
assert.equal(validate({ ...good, email: 'a@b.c<script>' }).error, 'invalid email');

// other origin gets the site's origin back (browser blocks it), preflight works, wrong path 404
res = await handle(post(good, 'https://evil.example'), env, send);
assert.equal(res.headers.get('Access-Control-Allow-Origin'), 'https://steadywren.com');
assert.equal((await handle(new Request('https://api.steadywren.com/contact', { method: 'OPTIONS' }), env, send)).status, 204);
assert.equal((await handle(new Request('https://api.steadywren.com/other', { method: 'POST', body: '{}' }), env, send)).status, 404);

// delivery failure -> 502 with a fallback hint
res = await handle(post(good), env, async () => { throw new Error('boom'); });
assert.equal(res.status, 502);

console.log('worker tests passed');
