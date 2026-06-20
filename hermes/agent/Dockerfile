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

# Writable scratch dir the agent runs in (mount the Obsidian vault here later).
ENV HERMES_WORKSPACE=/app/workspace
RUN mkdir -p /app/workspace

CMD ["python", "main.py"]
