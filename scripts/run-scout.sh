#!/bin/bash
# One scheduled /linkedin_scout run. Invoked by launchd once a day.
#
# Simpler than run-digest.sh because there is only one platform and it speaks
# stdio: no HTTP server to start, nothing to adopt or leave running. What this
# script contributes is the two guards the skill cannot enforce on itself.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HOME/.local/state/scout"
mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# No network means no run. An empty Connection Feed reads as "nobody good
# today", which is a different and much worse claim than "I could not look".
if ! ping -c1 -t3 1.1.1.1 >/dev/null 2>&1; then
  log "no network — skipping this run"
  date +%s > "$LOG_DIR/skipped-at"
  exit 0
fi

# The digest fires at 12:23 on the same LinkedIn account. This job starts at
# 10:31 and the skill holds itself to 90 minutes, but a skill cannot be trusted
# to enforce its own wall clock — a hung page load does not read the rules. The
# hard kill is here, and it is deliberately a few minutes short of 12:23.
DEADLINE_SECONDS=$(( 105 * 60 ))

log "starting scout run (hard deadline ${DEADLINE_SECONDS}s)"
cd "$REPO" || exit 1

# Two LinkedIn sessions on one account is the failure this whole design avoids,
# so refuse to start rather than overlap with a digest that is running late.
if pgrep -f "claude -p /digest" >/dev/null 2>&1; then
  log "a digest run is still going — skipping rather than sharing the account"
  exit 0
fi

# macOS ships no `timeout`, so the watchdog is a background sleep that TERMs the
# run and is itself killed the moment the run finishes on its own.
claude -p "/linkedin_scout" --permission-mode acceptEdits &
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
  log "scout run hit the ${DEADLINE_SECONDS}s deadline and was killed"
else
  log "scout run finished (exit $STATUS)"
fi
exit $STATUS
