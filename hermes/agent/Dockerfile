FROM python:3.12-slim

# The Claude Agent SDK bundles the Claude Code CLI as a native binary — no Node.js
# needed. git is handy for Claude Code's built-in tools; ca-certificates for TLS.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Run as non-root: Claude Code refuses bypassPermissions (autonomous write/shell)
# under root. hermes needs a writable HOME (claude config) + workspace.
RUN useradd -m -u 10001 hermes \
    && mkdir -p /app/workspace \
    && chown -R hermes:hermes /app
ENV HOME=/home/hermes \
    HERMES_WORKSPACE=/app/workspace
USER hermes

CMD ["python", "main.py"]
