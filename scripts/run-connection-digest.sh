#!/bin/bash
# One scheduled /connection_digest run. Invoked by launchd once a day.
#
# Simpler than run-feed-digest.sh because there is only one platform and it speaks
# stdio: no HTTP server to start, nothing to adopt or leave running. What this
# script contributes is the two guards the skill cannot enforce on itself.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HOME/.local/state/connection-digest"
mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# No network means no run. An empty Connection Feed reads as "nobody good
# today", which is a different and much worse claim than "I could not look".
if ! ping -c1 -t3 1.1.1.1 >/dev/null 2>&1; then
  log "no network — skipping this run"
  date +%s > "$LOG_DIR/skipped-at"
  exit 0
fi

# Unlike the feed digest, this job is nothing but LinkedIn: a logged-out account costs fifty
# minutes to discover there is nobody to find, and leaves behind an empty Connection Digest
# that reads as "nobody good today". The server quarantines its auth state into an
# invalid-state-* directory when a session dies, so a missing source-state.json is the
# signal — confirmed present on a logged-in host 2026-08-26. Refusing is right here: there
# is no reduced version of this run that works without the account.
#
# Recover with: servers/linkedin/.venv/bin/linkedin-mcp-server --login
if [[ ! -f "$HOME/.linkedin-mcp/source-state.json" ]]; then
  log "LinkedIn is logged out (no source-state.json) — skipping; recover with --login"
  date +%s > "$LOG_DIR/skipped-at"
  exit 0
fi

# The feed digest fires at 12:23 on the same LinkedIn account. This job starts at
# 10:31 and the skill holds itself to 90 minutes, but a skill cannot be trusted
# to enforce its own wall clock — a hung page load does not read the rules. The
# hard kill is here, and it is deliberately a few minutes short of 12:23.
DEADLINE_SECONDS=$(( 105 * 60 ))

log "starting connection digest run (hard deadline ${DEADLINE_SECONDS}s)"
cd "$REPO" || exit 1

# Two LinkedIn sessions on one account is the failure this whole design avoids,
# so refuse to start rather than overlap with a feed digest that is running late.
if pgrep -f "claude -p /feed_digest" >/dev/null 2>&1; then
  log "a feed digest run is still going — skipping rather than sharing the account"
  exit 0
fi

# macOS ships no `timeout`, so the watchdog is a background sleep that TERMs the
# run and is itself killed the moment the run finishes on its own.
claude -p "/connection_digest" --permission-mode acceptEdits &
CLAUDE_PID=$!
( sleep "$DEADLINE_SECONDS"; kill -TERM "$CLAUDE_PID" 2>/dev/null ) &
WATCHDOG_PID=$!

wait "$CLAUDE_PID"
STATUS=$?
kill "$WATCHDOG_PID" 2>/dev/null
wait "$WATCHDOG_PID" 2>/dev/null

# 128 + SIGTERM. Worth distinguishing in the log: a killed run and a run that
# found nobody leave the same empty database behind.
if [[ $STATUS -eq 143 ]]; then
  log "connection digest run hit the ${DEADLINE_SECONDS}s deadline and was killed"
else
  log "connection digest run finished (exit $STATUS)"
fi
exit $STATUS
