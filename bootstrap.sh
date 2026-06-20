#!/usr/bin/env bash
# Provision a fresh Raspberry Pi OS Lite (64-bit) box for Hermes.
# Run once, after your first SSH login, from inside the cloned repo.
set -euo pipefail

echo ">> System update"
sudo apt-get update && sudo apt-get -y upgrade
sudo apt-get install -y ca-certificates curl git ufw tmux

echo ">> Docker (+ compose plugin)"
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"

echo ">> Tailscale (secure remote access; avoids port-forwarding)"
curl -fsSL https://tailscale.com/install.sh | sh

echo ">> Claude Code (native installer — no Node.js needed)"
curl -fsSL https://claude.ai/install.sh | bash

echo ">> Firewall: SSH + Tailnet only"
sudo ufw allow 22/tcp
sudo ufw allow in on tailscale0
sudo ufw --force enable

cat <<'NOTE'

Done.
  1) Log out/in (or run: newgrp docker) so the docker group applies.
  2) sudo tailscale up        # authenticate this box to your Tailnet
  3) Open a new shell, then:  claude --version
  4) cp .env.example .env  &&  edit .env  &&  claude

NOTE
