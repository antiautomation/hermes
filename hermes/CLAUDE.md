# CLAUDE.md — context for Claude Code

## What this is
Hermes: a personal assistant hub on a Raspberry Pi 4 (Raspberry Pi OS Lite 64-bit).
Pi = always-on connectors + scheduler + message I/O. Brain = **Claude Code**, driven
programmatically via the **Claude Agent SDK** (`claude-agent-sdk`).
User-facing surface = an existing **Telegram bot**.
(Also deployable as a container on Railway — project `Davids_Hermes`, service `hermes-agent`.)

## Owner conventions
- Create branches and PRs proactively for non-trivial changes; don't wait to be asked.
- Track open work as GitHub issues so nothing gets lost.
- Owner is high technical skill but not a software engineer — explain decisions briefly.

## Hard rules
- **Mercury is read-only.** Never configure or use a read-write/transactional token.
  Hermes never moves money.
- **Approvals before irreversible actions.** Any Odoo write, outbound email/WhatsApp,
  or PaperclipAI action goes through the Telegram approve/reject flow first
  (this is the unified out-of-band approval surface — owner's "Pattern A").
- Lock the Telegram bot to `TELEGRAM_ALLOWED_USER_IDS`; ignore everyone else.
- Secrets live in `.env` only — never commit them.

## Build order (phases)
1. Telegram bot live + Claude reply loop → Email (Gmail API + IMAP) → Calendar → Odoo
   (odoo-sidekick) → Mercury (read-only) → Obsidian vault read/write.
2. PaperclipAI approval inbox → Fitbit → Apple Health webhook → GoWa WhatsApp (×2).
3. (Deferred) iMessage via a Mac + BlueBubbles, if/when added.

## Stack
- `agent/` Python (python-telegram-bot + `claude-agent-sdk`). Async.
  The Agent SDK spawns the Claude Code CLI, so the image installs Node.js +
  `@anthropic-ai/claude-code`. Auth via `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN`.
- `docker-compose.yml` runs the agent and two GoWa instances.
- `mcp/servers.json` declares MCP tools (Odoo, Mercury, …).

## Notes / TODO to verify when wiring
- GoWa env/flags in docker-compose are placeholders — confirm against the GoWa README
  before relying on exact names.
- The 2 org Gmail accounts may require Workspace admin consent for API scopes.
- Apple Health has no server pull — data is pushed from iOS (Health Auto Export → webhook).
