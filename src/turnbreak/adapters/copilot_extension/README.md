Copilot CLI extension template for turnbreak

Copilot CLI uses JavaScript extensions (Node.js entry files) rather than a
simple hook-script config. This template explains how to add a small
extension that exposes a slash command to open your turnbreak interests
file, and how to install it into your user extensions folder.

Why an extension?
- Copilot CLI discovers extensions under `~/.copilot/extensions/NAME/` or
  `.github/extensions/NAME/` in a repo. Extensions are JavaScript modules
  run directly by Node.js, and can add slash commands and tools to the
  interactive session.

Files in this template
- `extension.mjs` (skeleton): a commented starter file showing where to
  add a slash command that opens the interests file. See Copilot docs:
  https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-extensions

Install (user-level)
1. Copy this directory to `~/.copilot/extensions/turnbreak/`.
2. Restart Copilot CLI with `--experimental` or run `/experimental on` in
   an interactive session to enable extensions.
3. The extension should register a `/turnbreak-interests` slash command
   which opens `~/.config/turnbreak/interests.md` in $EDITOR.

Notes
- Extensions run with your user privileges. Only install extensions you
  trust.
- This is a template: fill `extension.mjs` using the APIs in the Copilot
  extensions tutorial linked above. The SDK is stable in preview, and
  the tutorial shows how to register slash commands and handle requests.

Skeleton (example to adapt in extension.mjs)

// Pseudocode: adapt from Copilot extensions tutorial
import { registerSlashCommand } from '@copilot/cli/sdk'

registerSlashCommand('/turnbreak-interests', async (ctx) => {
  // spawn your system editor to open the interests file
  const path = require('path')
  const child_process = require('child_process')
  const homedir = require('os').homedir()
  const interests = path.join(homedir, '.config', 'turnbreak', 'interests.md')
  const editor = process.env.EDITOR || 'vi'
  child_process.spawn(editor, [interests], { stdio: 'inherit' })
  return { status: 'ok' }
})

See the Copilot CLI extension tutorial for exact APIs and examples.
