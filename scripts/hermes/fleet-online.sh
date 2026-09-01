#!/usr/bin/env bash
# Fleet actionability watchdog for hermes-dedicated.
#
# Emits ONE line per device with a *stable* state that only changes when
# there is something for the agent to DO:
#   <dev>:IDLE     — no queued actions (no wake)
#   <dev>:WAITING  — actions queued but device unreachable (no wake)
#   <dev>:READY[-N]— actions queued AND device reachable (CHANGE -> wake)
#
# The cron monitor hashes this exact output: the agent only fires on a hash
# change, so IDLE/WAITING states stay quiet forever. READY appears when a
# task can actually be executed; -N is a retry counter bumped by the agent
# on failure so a stuck action wakes the watchdog again instead of silently
# parking.
#
# IMPORTANT: no timestamps / latency / variable text anywhere in the output,
# or the hash changes every tick and the agent wakes constantly.
set -u

PENDING_ROOT="$HOME/.hermes/pending-actions"
DEVICES="fedora book4-edge"

for DEV in $DEVICES; do
  # queued actions = *.md directly in the device's pending dir (not done/)
  QUEUED=0
  if compgen -G "$PENDING_ROOT/$DEV/*.md" >/dev/null 2>&1; then
    QUEUED=1
  fi

  if [ "$QUEUED" = "0" ]; then
    echo "$DEV:IDLE"
    continue
  fi

  # attempt counter (agent bumps this on failure to force a re-fire)
  RETRY=0
  if [ -f "$PENDING_ROOT/$DEV/.attempt" ]; then
    RETRY=$(cat "$PENDING_ROOT/$DEV/.attempt" 2>/dev/null || echo 0)
  fi

  if timeout 6 ssh -o BatchMode=yes -o ConnectTimeout=4 -o StrictHostKeyChecking=accept-new \
      -o UserKnownHostsFile=/dev/null peter@"$DEV" true >/dev/null 2>&1; then
    if [ "$RETRY" -gt 0 ]; then
      echo "$DEV:READY-$RETRY"
    else
      echo "$DEV:READY"
    fi
  else
    echo "$DEV:WAITING"
  fi
done