#!/bin/bash
# Install the toolkit into the user-level Claude Code directories.
#
# Everything real stays in this repo; only symlinks go into ~/.claude, so git
# remains the source of truth. The one thing that cannot be a symlink is the
# agent frontmatter: a user-level agent may declare its own MCP servers (which
# is the whole reason we are not a plugin), but neither ${HOME} nor ~ expands in
# that frontmatter — the command has to be an absolute path. So the agents are
# checked in as .md.in templates and rendered here.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS="$HOME/.claude/agents"
SKILLS="$HOME/.claude/skills"
BUILD="$ROOT/build/agents"

mkdir -p "$AGENTS" "$SKILLS" "$BUILD"

echo "==> rendering agent templates"
for tpl in "$ROOT"/agents/*.md.in; do
  name="$(basename "$tpl" .md.in)"
  sed "s|@@TOOLKIT_ROOT@@|$ROOT|g" "$tpl" > "$BUILD/$name.md"
  ln -sfn "$BUILD/$name.md" "$AGENTS/$name.md"
  echo "    $name"
done

echo "==> linking agents that need no rendering"
for src in "$ROOT"/agents/*.md; do
  [ -e "$src" ] || continue
  name="$(basename "$src")"
  ln -sfn "$src" "$AGENTS/$name"
  echo "    ${name%.md}"
done

echo "==> linking skills"
for dir in "$ROOT"/skills/*/; do
  name="$(basename "$dir")"
  ln -sfn "${dir%/}" "$SKILLS/$name"
  echo "    /$name"
done

# Only the director profiles are registered globally. The explorer profiles are
# declared inside the agents that need them and exist nowhere else — that is the
# isolation: the main loop cannot read a page or a post body because it has no
# tool for it, not because it was told not to.
echo "==> registering director MCP servers (user scope)"
reg() {
  claude mcp remove --scope user "$1" >/dev/null 2>&1 || true
  shift
  claude mcp add --scope user "$@" >/dev/null
}

reg websearch websearch \
  -e "PYTHONPATH=$ROOT/servers" \
  -- "$ROOT/.venv/bin/python" -m mcp_servers.firecrawl_server --profile director
reg reddit reddit \
  -e "PYTHONPATH=$ROOT/servers" \
  -- "$ROOT/.venv/bin/python" -m mcp_servers.reddit_server --profile director
reg x x \
  -e "AUTH_DIR=$ROOT/servers/x/.auth" \
  -- node "$ROOT/servers/x/dist/mcp.js" --profile director
reg linkedin linkedin \
  -- "$ROOT/servers/linkedin/.venv/bin/linkedin-mcp-server" --transport stdio --log-level ERROR
claude mcp remove --scope user xiaohongshu >/dev/null 2>&1 || true
claude mcp add --scope user --transport http xiaohongshu http://localhost:18060/mcp >/dev/null
echo "    websearch reddit x linkedin xiaohongshu"

# The old skills-dir plugin symlink would double-register everything.
if [ -L "$SKILLS/claude-toolkit" ]; then
  rm "$SKILLS/claude-toolkit"
  echo "==> removed the old plugin symlink (~/.claude/skills/claude-toolkit)"
fi

cat <<EOF

Installed. Restart Claude Code, then:

  /research <question>     long-horizon web research
  /digest                  screen the four social feeds into Notion

Isolation check — the main loop should NOT see any of these:
  mcp__explorer__scrape, mcp__*__get_post
EOF
