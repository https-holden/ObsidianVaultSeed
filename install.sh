#!/bin/sh
# Install the vault-seed skill for Claude Code by linking it into ~/.claude/skills.
# A link, not a copy: `git pull` in this clone is the whole update, and the skill
# pulls for itself each time it runs.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
dest="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
mkdir -p "$dest"
if [ -e "$dest/vault-seed" ] && [ ! -L "$dest/vault-seed" ]; then
  echo "A vault-seed skill that is not a link already exists at $dest/vault-seed. Move it away and rerun." >&2
  exit 1
fi
ln -sfn "$here/skills/vault-seed" "$dest/vault-seed"
echo "Linked $dest/vault-seed -> $here/skills/vault-seed"
echo "Start a new Claude Code session in any project and type /vault-seed"
