// Minimal Copilot CLI extension registering /turnbreak-interests.
// Logs activation and handler calls to a local file for debugging.
import { spawn } from 'child_process';
import path from 'path';
import os from 'os';
import fs from 'fs';

const homedir = os.homedir();
const debugLog = path.join(homedir, '.copilot', 'extensions', 'turnbreak', 'turnbreak.log');

function log(...parts) {
  try {
    const line = new Date().toISOString() + ' - ' + parts.map(p => (typeof p === 'string' ? p : JSON.stringify(p))).join(' ') + '\n';
    fs.appendFileSync(debugLog, line, { encoding: 'utf8', mode: 0o600 });
  } catch (e) {
    // best-effort; don't crash the extension if logging fails
    try { console.error('turnbreak: log failed', e && e.message); } catch (_) {}
  }
}

process.on('uncaughtException', (err) => { log('uncaughtException', err && err.stack ? err.stack : String(err)); });
process.on('unhandledRejection', (r) => { log('unhandledRejection', r && r.stack ? r.stack : String(r)); });

function launchEditor(editor, filePath) {
  log('launchEditor', editor, filePath);
  try {
    const child = spawn(editor, [filePath], {
      detached: true,
      stdio: 'ignore',
      shell: false,
    });
    child.unref();
    log('launched-direct', child.pid);
    return { ok: true, launched: true };
  } catch (err) {
    log('launch-direct-failed', err && err.message ? err.message : String(err));
    try {
      const child2 = spawn(`${editor} "${filePath}"`, {
        detached: true,
        stdio: 'ignore',
        shell: true,
      });
      child2.unref();
      log('launched-shell', child2.pid);
      return { ok: true, launched: true };
    } catch (err2) {
      log('launch-shell-failed', err2 && err2.message ? err2.message : String(err2));
      return { ok: false, error: (err2 && err2.message) || String(err2 || err) };
    }
  }
}

async function registerCommands(sdk) {
  const cmd = '/turnbreak-interests';
  const handler = async () => {
    try {
      const interests = path.join(homedir, '.config', 'turnbreak', 'interests.md');
      const editor = process.env.EDITOR || 'vi';
      log('handler-called', { cmd, interests, editor });
      const res = launchEditor(editor, interests);
      log('handler-result', res);
      if (res.ok) return { status: 'ok', path: interests, launched: !!res.launched };
      return { status: 'error', message: res.error || 'failed to launch editor', path: interests };
    } catch (e) {
      log('handler-exception', e && e.stack ? e.stack : String(e));
      return { status: 'error', message: e && e.message ? e.message : String(e) };
    }
  };

  try {
    log('registerCommands-enter', { hasSdk: !!sdk });
    if (sdk && typeof sdk.registerSlashCommand === 'function') {
      sdk.registerSlashCommand(cmd, handler);
      log('registered-sdk-registerSlashCommand');
    } else if (sdk && typeof sdk.register === 'function') {
      try { sdk.register(cmd, handler); log('registered-sdk-register'); } catch (e) { log('register-fallback-failed', e && e.message); }
    } else {
      log('no-sdk-api');
      console.warn('turnbreak: extension SDK not available or API mismatch; slash command may not be registered.');
    }
    console.log('turnbreak: registered', cmd);
    log('registerCommands-done');
  } catch (err) {
    log('registerCommands-exception', err && err.stack ? err.stack : String(err));
    console.warn('turnbreak: failed to register command', err && err.message ? err.message : err);
  }
}

let started = false;

export async function activate(sdk) {
  if (started) { log('activate-called-again'); return; }
  started = true;
  log('activate-start');
  await registerCommands(sdk);
  log('activate-done');
}

export default async function (sdk) {
  await activate(sdk);
}
