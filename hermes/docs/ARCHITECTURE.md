# Architecture

```
        Telegram (you, anywhere)
                 │
        ┌────────▼────────┐         ┌──────────────────────────┐
        │   agent (Pi)    │◄───────►│  Claude (Anthropic API)  │  ← the brain
        │  python-tg-bot  │         └──────────────────────────┘
        │  + scheduler    │
        │  + approvals    │
        └───┬───┬───┬─────┘
            │   │   │  MCP tools / connectors
   ┌────────┘   │   └─────────┐
   ▼            ▼             ▼
 Odoo        Mercury       Gmail / IMAP / Calendar / Fitbit
(sidekick)  (read-only)
            │
        GoWa ×2 (WhatsApp) ── webhook ──► agent:8080
        Apple Health (iOS push) ──────────► agent:8080
        PaperclipAI instances ── poll/webhook ─► approval inbox
```

Principles:
- The Pi is I/O-bound (calls cloud APIs); a Pi 4 is sufficient for v1.
- One approval flow (Telegram inline buttons) gates every irreversible action.
- Remote access is via Tailscale only — no ports exposed to the internet.
