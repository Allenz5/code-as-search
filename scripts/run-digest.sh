#!/bin/bash
# One scheduled /digest run. Invoked by launchd three times a day.
#
# Two things this has to get right that a bare `claude -p` does not:
#   - USER and LOGNAME must be set. Without them Claude Code cannot reach its
#     credentials in the macOS Keychain and comes up "Not logged in" — which in
#     launchd's stripped environment is otherwise silent.
#   - The Xiaohongshu server speaks HTTP, so it has to be running. It is started
#     and stopped per run rather than left up: a process left up for a day gets
#     into a state where the login page stops rendering.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HOME/.local/state/digest"
mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# No network means no run. Writing an empty digest would read as "nothing good
# today", which is a different and much worse claim than "I could not look".
if ! ping -c1 -t3 1.1.1.1 >/dev/null 2>&1; then
  log "no network — skipping this run"
  date +%s > "$LOG_DIR/skipped-at"
  exit 0
fi

XHS_BIN="$REPO/servers/xiaohongshu/bin/xiaohongshu-mcp"
if [[ ! -x "$XHS_BIN" ]]; then
  log "xiaohongshu binary missing — run: make build"
  exit 1
fi

pkill -f xiaohongshu-mcp >/dev/null 2>&1
sleep 1
( cd "$REPO/servers/xiaohongshu" && "$XHS_BIN" -headless=true ) >"$LOG_DIR/xhs.log" 2>&1 &
XHS_PID=$!
trap 'kill $XHS_PID 2>/dev/null; wait $XHS_PID 2>/dev/null' EXIT

for _ in $(seq 20); do
  curl -sf http://localhost:18060/health >/dev/null 2>&1 && break
  sleep 1
done
if ! curl -sf http://localhost:18060/health >/dev/null 2>&1; then
  log "xiaohongshu server did not come up — running without it"
fi

log "starting digest run"
cd "$REPO" || exit 1
claude -p "/digest" --permission-mode acceptEdits
STATUS=$?
log "digest run finished (exit $STATUS)"
exit $STATUS
