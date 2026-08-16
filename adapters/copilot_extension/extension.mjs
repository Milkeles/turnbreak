// Minimal Copilot CLI extension registering /turnbreak-interests.
// Adapted from the Copilot CLI extensions tutorial. This file is a
// template and may need adjustment against the exact SDK version you
// have installed. It intentionally avoids risky operations and simply
// launches the user's $EDITOR to edit ~/.config/turnbreak/interests.md.

import { spawn } from 'child_process';
import path from 'path';
import os from 'os';

// The Copilot CLI extension SDK exposes different APIs across previews.
// Try the documented helper then fall back to a best-effort registration
// approach and a helpful console message if the runtime API is absent.

async function registerCommands(sdk) {
  try {
    // Preferred SDK API (example):
    sdk.registerSlashCommand('/turnbreak-interests', async (ctx) => {
      const homedir = os.homedir();
      const interests = path.join(homedir, '.config', 'turnbreak', 'interests.md');
      const editor = process.env.EDITOR || 'vi';
      spawn(editor, [interests], { stdio: 'inherit' });
      return { status: 'ok' };
    });
    console.log('turnbreak: registered /turnbreak-interests');
  } catch (err) {
    console.warn('turnbreak: extension SDK not available or API mismatch; this extension may need adapting.');
    console.warn(err && err.message ? err.message : err);
  }
}

// Entry point: Copilot CLI typically looks for a top-level exported
// function or just runs the module. Attempt to hook into common export
// patterns.

let started = false;

export async function activate(sdk) {
  if (started) return;
  started = true;
  await registerCommands(sdk);
}

// Some versions of the SDK call the default function directly.
export default async function (sdk) {
  await activate(sdk);
}
