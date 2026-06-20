FROM python:3.12-slim

# The Claude Agent SDK drives the Claude Code CLI as a subprocess, so the image
# needs Node.js + the `claude` binary on PATH. git is handy for Claude Code's tools.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @anthropic-ai/claude-code \
    && apt-get purge -y curl && apt-get autoremove -y \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Writable scratch dir the agent runs in (mount the Obsidian vault here later).
ENV HERMES_WORKSPACE=/app/workspace
RUN mkdir -p /app/workspace

CMD ["python", "main.py"]
