# Hermes scripts

Operational scripts for the Hermes gateway box (hermes-dedicated). The fleet runs against that machine, so these live there and are tracked here for reference.

## active-device

Tells you which device the user is talking to Hermes from.

The Hermes desktop app connects to the gateway on port 9119 from the device the user is on. This script reads the established connections with `ss`, maps the peer tailnet IPs to device names with `tailscale status`, and prints the connected devices.

```
$ active-device
fedora (6 connections)
windows (1 connection)
```

The device with the most sockets and the active data flow is the one the user is using.

Pitfall: the desktop app runs locally on hermes-dedicated all the time (it is the always-on gateway), so a local app process is NOT a sign of the user being there. Read the connection table instead.

Run on: hermes-dedicated.
Deps: bash, ss (iproute2), tailscale, python3.

## fleet-online.sh

Monitor script for the device online watchdog cron job (every 15m, monitor mode).

Emits one stable line per device:

- `<dev>:IDLE` - no queued actions (quiet)
- `<dev>:WAITING` - actions queued but device unreachable (quiet)
- `<dev>:READY[-N]` - actions queued AND device reachable (wakes the agent)

The cron monitor hashes the output byte for byte. The agent only fires when the hash changes, so IDLE and WAITING stay silent. READY appears only when a queued task can actually run. -N is a retry counter the agent bumps on failure so a stuck action wakes the watchdog again.

Output must stay stable: no timestamps, no latency values, no random ordering.

Queued actions live in `~/.hermes/pending-actions/<device>/*.md` on hermes-dedicated. Reachability is tested with `ssh peter@<device>` over the tailnet.

Run on: hermes-dedicated (as the cron monitor script).
Deps: bash, ssh, the tailnet hostnames of the fleet.
