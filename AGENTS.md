# Agent Runbook

## Local Startup Policy

When the user asks to start local, use this exact sequence and do not improvise:

1. `./dev refresh`
2. `./dev status`
3. If unhealthy, `./dev logs` and report the first actionable error.

## Canonical Commands

- Start clean: `make local`
- Hard reset/start: `make local-reset`
- Health check: `make local-check`
- Stop: `make down`

## Why

`./dev refresh` already handles stale PIDs, stale listeners, frontend cache reset, restart, and diagnostics. Reusing it avoids repeated manual troubleshooting.
