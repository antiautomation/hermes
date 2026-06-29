#!/bin/sh
set -e
# Railway mounts the volume root-owned; hand the workspace to the non-root app
# user so the agent (which runs as `hermes` for Claude Code's bypassPermissions)
# can write to it. Then drop privileges and start the bot.
chown -R hermes:hermes "${HERMES_WORKSPACE:-/app/workspace}" 2>/dev/null || true
exec gosu hermes python main.py
