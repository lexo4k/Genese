#!/usr/bin/env node
'use strict';

/**
 * NiceHash Stratum diagnostics for GÊNESE.
 *
 * This script checks TCP/TLS reachability and the Stratum subscribe/authorize
 * handshake. It DOES NOT mine, invent hashrate, submit shares, or claim payout.
 *
 * Required:
 *   STRATUM_HOST=... STRATUM_PORT=443 STRATUM_USER=wallet.worker
 * Optional:
 *   STRATUM_PASSWORD=x WORKER_NAME=genese-check TIMEOUT_MS=10000
 *
 * Run: node tools/nicehash-stratum-check.js
 */

const tls = require('node:tls');

const host = process.env.STRATUM_HOST || 'nhmp-ssl.eu.nicehash.com';
const port = Number(process.env.STRATUM_PORT || 443);
const user = process.env.STRATUM_USER || '';
const password = process.env.STRATUM_PASSWORD || 'x';
const worker = process.env.WORKER_NAME || 'genese-check';
const timeoutMs = Number(process.env.TIMEOUT_MS || 10000);

function fail(message, code = 1) {
  console.error(`FAIL: ${message}`);
  process.exitCode = code;
}

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  fail('STRATUM_PORT must be an integer between 1 and 65535.');
  process.exit();
}
if (!user.trim()) {
  fail('STRATUM_USER is missing. Set it to the NiceHash mining username/wallet.worker required by your account.');
  process.exit();
}

let socket;
let nextId = 1;
let buffer = '';
let finished = false;
const pending = new Map();

function finish(ok, message) {
  if (finished) return;
  finished = true;
  clearTimeout(timer);
  if (socket) socket.end();
  if (ok) console.log(`PASS: ${message}`);
  else fail(message);
}

function send(method, params) {
  const id = nextId++;
  socket.write(JSON.stringify({ id, method, params }) + '\\n');
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject, method });
    setTimeout(() => {
      if (pending.has(id)) {
        pending.delete(id);
        reject(new Error(`Timed out waiting for ${method} response`));
      }
    }, timeoutMs);
  });
}

const timer = setTimeout(() => finish(false, `timeout after ${timeoutMs} ms`), timeoutMs);

console.log(`Checking TLS/Stratum endpoint ${host}:${port}`);
console.log('No hashrate or accepted shares will be reported by this diagnostic.');

socket = tls.connect({
  host,
  port,
  servername: host,
  rejectUnauthorized: true,
  minVersion: 'TLSv1.2',
}, async () => {
  console.log('PASS: TLS connected and certificate validation succeeded.');
  try {
    const sub = await send('mining.subscribe', [`GÊNESE-check/1.0`]);
    if (sub.error) throw new Error(`subscribe rejected: ${JSON.stringify(sub.error)}`);
    console.log('PASS: Stratum subscribe response received.');

    const auth = await send('mining.authorize', [user, password]);
    if (auth.error) throw new Error(`authorize rejected: ${JSON.stringify(auth.error)}`);
    if (auth.result !== true) throw new Error(`authorize not accepted: ${JSON.stringify(auth.result)}`);
    console.log(`PASS: Stratum authorization accepted for worker ${worker}.`);
    finish(true, 'endpoint, TLS, subscribe and authorization validated. This is not proof of mining or payment.');
  } catch (err) {
    finish(false, err.message);
  }
});

socket.setEncoding('utf8');
socket.on('data', chunk => {
  buffer += chunk;
  const lines = buffer.split(/\\r?\\n/);
  buffer = lines.pop() || '';
  for (const line of lines) {
    if (!line.trim()) continue;
    let msg;
    try { msg = JSON.parse(line); }
    catch { console.error('WARN: received non-JSON Stratum line'); continue; }

    if (msg.method === 'mining.notify') {
      console.log('INFO: server sent a mining job notification.');
      continue;
    }
    if (msg.method === 'mining.set_difficulty') {
      console.log('INFO: server set share difficulty.');
      continue;
    }
    if (msg.id !== null && msg.id !== undefined && pending.has(msg.id)) {
      const item = pending.get(msg.id);
      pending.delete(msg.id);
      item.resolve(msg);
    }
  }
});
socket.on('error', err => finish(false, `TLS/socket error: ${err.message}`));
socket.on('end', () => {
  if (!finished) finish(false, 'server closed connection before checks completed');
});
