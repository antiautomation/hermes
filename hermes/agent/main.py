"""
Hermes agent — Telegram front-end + Claude Code brain.

What works now:
  - Telegram bot, locked to TELEGRAM_ALLOWED_USER_IDS
  - The brain is Claude Code, driven programmatically via the Claude Agent SDK
    (`claude-agent-sdk`). Each message runs one agentic turn with a locked,
    read-only tool allowlist. Falls back to echo until auth is provided.
  - /approve demo showing the inline approve/reject pattern used for all
    irreversible actions (Odoo writes, outbound messages, Paperclip tickets)

Auth (set ONE in the environment):
  - ANTHROPIC_API_KEY        pay-as-you-go API billing
  - CLAUDE_CODE_OAUTH_TOKEN  a Claude Pro/Max/Team subscription (`claude setup-token`)

What Claude Code fills in next:
  - MCP tools (Odoo, Mercury), email/calendar/Fitbit connectors, GoWa webhook
  - Per-chat session memory + scheduler, and wiring writes through /approve
"""
import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Conflict
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hermes")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Lock the bot to the owner. Numeric IDs are the robust form; usernames are a
# convenience (case-insensitive, can change/be reassigned — prefer IDs long-term).
# If BOTH lists are empty the bot is unlocked (replies to anyone).
ALLOWED_IDS = {
    int(x) for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if x.strip()
}
ALLOWED_USERNAMES = {
    x.strip().lstrip("@").lower()
    for x in os.getenv("TELEGRAM_ALLOWED_USERNAMES", "").split(",")
    if x.strip()
}
LOCKED = bool(ALLOWED_IDS or ALLOWED_USERNAMES)

# The Claude Agent SDK / Claude Code CLI read either of these from the env.
HAS_AUTH = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_CODE_OAUTH_TOKEN"))
MODEL = os.getenv("HERMES_MODEL", "claude-opus-4-8")
WORKSPACE = os.getenv("HERMES_WORKSPACE", "/app/workspace")

# Tool surface. Read-only by default. Set HERMES_WRITE_TOOLS=1 to also grant
# filesystem writes + shell so the owner can configure Hermes from the chat.
#   - read-only  -> permission_mode "dontAsk": run the allow-list, deny the rest,
#                   never block on a prompt.
#   - write mode -> permission_mode "bypassPermissions": run anything unattended
#                   (requires a non-root container — Claude Code refuses bypass as root).
# Irreversible EXTERNAL actions (email/WhatsApp/Odoo/money) are NOT exposed here
# and still go through the Telegram /approve flow.
READ_TOOLS = ["Read", "Glob", "Grep", "WebSearch", "WebFetch"]
WRITE_TOOLS = ["Write", "Edit", "MultiEdit", "Bash"]
WRITE_ENABLED = os.getenv("HERMES_WRITE_TOOLS", "").strip().lower() in ("1", "true", "yes", "on")
ALLOWED_TOOLS = READ_TOOLS + (WRITE_TOOLS if WRITE_ENABLED else [])
PERMISSION_MODE = "bypassPermissions" if WRITE_ENABLED else "dontAsk"

SYSTEM_PROMPT = (
    "You are Hermes, a concise personal assistant for your owner, reachable over "
    "Telegram. Be direct and neutral; skip filler. You run inside a container on an "
    "always-on server; when write tools are enabled you can read/write files and run "
    "shell commands there. That filesystem is EPHEMERAL — anything outside a mounted "
    "volume is lost on the next redeploy, so flag it when persistence matters, and "
    "make lasting changes in the git repo. Never take or claim to have taken an "
    "irreversible EXTERNAL action — sending email or WhatsApp, moving money, or "
    "writing to Odoo — those go through a separate Telegram approval flow and are not "
    "wired yet. Mercury banking is strictly read-only. If you can't yet do something, say so plainly."
)

# Telegram hard-caps a single message at 4096 chars.
TG_LIMIT = 4000


def authorized(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    if not LOCKED:
        return True
    if user.id in ALLOWED_IDS:
        return True
    return (user.username or "").lower() in ALLOWED_USERNAMES


async def think(text: str) -> str:
    """Run one Claude Code turn via the Agent SDK. Echoes until auth is set."""
    if not HAS_AUTH:
        return f"(echo — set ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN) {text}"

    from claude_agent_sdk import (
        query, ClaudeAgentOptions, AssistantMessage, TextBlock,
    )

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=ALLOWED_TOOLS,
        permission_mode=PERMISSION_MODE,
        cwd=WORKSPACE,
    )

    parts: list[str] = []
    async for message in query(prompt=text, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
    return "".join(parts).strip() or "(no response)"


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return
    await update.message.reply_text(
        "Hermes online. Send me anything. /approve shows the approval flow."
    )


async def on_message(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return
    await update.message.chat.send_action("typing")
    try:
        reply = await think(update.message.text)
    except Exception as e:  # never let a brain error crash the handler
        log.exception("think failed")
        reply = f"⚠️ Brain error: {e}"
    await update.message.reply_text(reply[:TG_LIMIT])


async def approve_demo(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Every irreversible action surfaces as one of these before it runs."""
    if not authorized(update):
        return
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data="approve:demo-1"),
        InlineKeyboardButton("❌ Reject", callback_data="reject:demo-1"),
    ]])
    await update.message.reply_text(
        "Pending action: post invoice INV/2026/0142 in Odoo (€1,240).", reply_markup=kb
    )


async def on_callback(update: Update, _: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    decision, action_id = q.data.split(":", 1)
    # TODO: look up action_id and execute/cancel the gated action
    await q.edit_message_text(
        f"{'Approved' if decision == 'approve' else 'Rejected'}: {action_id}"
    )


async def on_error(_: object, context: ContextTypes.DEFAULT_TYPE):
    """A second poller (normal during a deploy rollover) makes Telegram return a
    409 Conflict. It self-heals once the old container stops, so log it quietly
    instead of dumping a traceback. Everything else logs with the stack."""
    err = context.error
    if isinstance(err, Conflict):
        log.warning("getUpdates conflict (another poller — usually a deploy rollover); retrying")
        return
    log.error("Unhandled error", exc_info=err)


def main():
    log.info(
        "Hermes starting — brain=%s model=%s lock=%s tools=%s",
        "claude-code" if HAS_AUTH else "echo (no auth)", MODEL,
        "OPEN (no allowlist!)" if not LOCKED
        else f"ids={len(ALLOWED_IDS)} usernames={sorted(ALLOWED_USERNAMES)}",
        f"read+write ({PERMISSION_MODE})" if WRITE_ENABLED else "read-only",
    )
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve_demo))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_error_handler(on_error)
    # Drop any backlog of updates queued while we were redeploying.
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
