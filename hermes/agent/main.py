"""
Hermes agent — minimal runnable skeleton.

What works now:
  - Telegram bot, locked to TELEGRAM_ALLOWED_USER_IDS
  - If ANTHROPIC_API_KEY is set, replies via Claude; otherwise echoes
  - /approve demo showing the inline approve/reject pattern used for all
    irreversible actions (Odoo writes, outbound messages, Paperclip tickets)

What Claude Code fills in next:
  - MCP tools (Odoo, Mercury), email/calendar/Fitbit connectors, GoWa webhook
  - The real agent loop + scheduler
"""
import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hermes")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED = {
    int(x) for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if x.strip()
}
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")


def authorized(update: Update) -> bool:
    user = update.effective_user
    return bool(user) and (not ALLOWED or user.id in ALLOWED)


async def think(text: str) -> str:
    """Send a turn to Claude. Falls back to echo until the key is set."""
    if not ANTHROPIC_KEY:
        return f"(echo — no ANTHROPIC_API_KEY yet) {text}"
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=ANTHROPIC_KEY)
    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are Hermes, a concise, neutral personal assistant.",
        messages=[{"role": "user", "content": text}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


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
    await update.message.reply_text(await think(update.message.text))


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


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve_demo))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    log.info("Hermes agent starting…")
    app.run_polling()


if __name__ == "__main__":
    main()
