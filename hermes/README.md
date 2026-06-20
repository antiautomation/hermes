# Hermes — personal assistant hub

Always-on personal assistant that runs on a Raspberry Pi 4 (the **nervous system**:
connectors, scheduler, message I/O) and uses Claude as the **brain** (via the Anthropic
API / Agent SDK). You talk to it through your existing **Telegram bot**.

This repo is the scaffold. The actual wiring (OAuth flows, MCP tools, the agent loop)
gets built out interactively in **Claude Code** once the Pi is provisioned.

## Capability status (v1)

| Capability | Path | Phase |
|---|---|---|
| Email (3 Gmail + 1 IMAP) | Gmail API per account + IMAP/SMTP | 1 |
| Calendar / routine | Google Calendar API / CalDAV | 1 |
| Odoo | odoo-sidekick engine (existing) | 1 |
| Mercury accounting | Mercury MCP, **read-only token** | 1 |
| Obsidian KB | markdown vault on Pi + Syncthing/git sync | 1 |
| Fitbit | Fitbit Web API (OAuth2) | 2 |
| PaperclipAI approvals | poll/webhook your instances → Telegram inbox | 2 |
| WhatsApp (personal + work) | GoWa bridge (unofficial — see caveat) | 2 |
| Apple Health | iOS push (Health Auto Export) → webhook | 2 |
| iMessage | **deferred** (needs a Mac running BlueBubbles) | later |
| Google Fit | **dropped** — REST API dead end of 2026 | — |

> **WhatsApp / GoWa caveat:** GoWa drives WhatsApp Web via the unofficial whatsmeow
> library. It works but is against WhatsApp ToS with a real ban risk, especially on a
> personal number. Keep traffic human-like; use numbers you can afford to lose.

## Repo layout

```
hermes/
├── CLAUDE.md            # project context Claude Code reads on launch
├── docker-compose.yml   # agent + GoWa (personal/work) services
├── .env.example         # every credential you need to gather (copy to .env)
├── scripts/bootstrap.sh # one-shot Pi provisioning
├── agent/               # Python agent: Telegram I/O + Claude + approvals
├── mcp/servers.json     # MCP server config (Odoo, Mercury, …)
└── docs/ARCHITECTURE.md
```

## Part A — Flash the Pi (do this from your Mac)

**Image: Raspberry Pi OS Lite (64-bit)** — Debian 12 Bookworm, headless, no desktop.
It's the right base for a 24/7 Docker host. (Skip the Desktop image; you'll drive
everything over SSH + Telegram.)

1. Install **Raspberry Pi Imager** on your Mac → https://www.raspberrypi.com/software/
2. Choose Device: Raspberry Pi 4 → OS: *Raspberry Pi OS (other)* → **Raspberry Pi OS Lite (64-bit)**.
3. Storage: pick your SD card **or** (recommended) a USB3 SSD — SD cards die under
   constant DB writes. Boot-from-SSD is far more reliable for an always-on box.
4. Click the **gear / Edit Settings** before writing and set:
   - Hostname: `hermes`
   - Enable SSH → **Use public-key authentication** (paste your Mac's `~/.ssh/id_ed25519.pub`)
   - Username / password
   - Wi-Fi if not using Ethernet (Ethernet preferred for a server)
   - Locale / timezone: `Europe/Madrid`
5. Write. Insert into the Pi, power on.

## Part B — First login + provision

```bash
ssh <username>@hermes.local          # mDNS; or use the Pi's LAN IP
git clone <your-repo-url> hermes && cd hermes
bash scripts/bootstrap.sh            # installs Docker, Tailscale, Claude Code, firewall
# log out/in (or: newgrp docker) so the docker group applies
sudo tailscale up                    # secure remote access — no port forwarding
claude --version                     # confirm Claude Code is installed
```

`bootstrap.sh` installs Docker + compose, Tailscale, the **Claude Code native
installer** (no Node.js required), and a firewall that exposes only SSH + your Tailnet.

## Part C — Hand off to Claude Code

```bash
cp .env.example .env                 # then fill in what you have (see checklist below)
claude                               # launches Claude Code in the repo
```

In that session I (Claude) can read `CLAUDE.md`, run the OAuth flows, wire the MCP
servers, link GoWa via QR, and bring services up one at a time. We'll work
**phase by phase** — get the bot replying first, then add connectors.

## Secrets checklist (collect these for `.env`)

- [ ] `ANTHROPIC_API_KEY` (or use your Claude Teams login for Claude Code itself)
- [ ] `TELEGRAM_BOT_TOKEN` + your own `TELEGRAM_ALLOWED_USER_IDS` (lock the bot to you)
- [ ] Google OAuth client (covers the 3 Gmail accounts + Calendar)
- [ ] IMAP/SMTP host + credentials for the 4th mailbox
- [ ] `MERCURY_API_TOKEN` — **create a read-only token** in Mercury
- [ ] Odoo: URL, DB, user, API key (your odoo-sidekick profile)
- [ ] `FITBIT_CLIENT_ID` / `FITBIT_CLIENT_SECRET`
- [ ] GoWa basic-auth + webhook secret
- [ ] PaperclipAI instance base URLs + tokens
- [ ] Obsidian vault path on the Pi

Nothing real ever goes in git — `.env`, `data/`, and the vault are gitignored.
