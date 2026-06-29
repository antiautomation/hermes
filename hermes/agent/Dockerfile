FROM python:3.12-slim

# The Claude Agent SDK bundles the Claude Code CLI as a native binary — no Node.js.
# git for Claude Code's tools; gosu to drop root in the entrypoint; ca-certificates for TLS.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git gosu \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Non-root app user (Claude Code refuses bypassPermissions under root). The
# container starts as ROOT so the entrypoint can chown a freshly-mounted volume,
# then drops to `hermes` via gosu to run the agent.
RUN useradd -m -u 10001 hermes \
    && mkdir -p /app/workspace \
    && chown -R hermes:hermes /app \
    && chmod +x /app/entrypoint.sh
ENV HOME=/home/hermes \
    HERMES_WORKSPACE=/app/workspace

ENTRYPOINT ["/app/entrypoint.sh"]
