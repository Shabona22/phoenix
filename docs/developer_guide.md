# Phoenix VPN V10 – Developer Guide

## Layout

```
src/           Core Python modules (orchestrator, protocols, security, …)
web/           Flask panel (configs, subscriptions, admin)
deploy/        Docker compose, remote deploy, health checks
tests/         Unit and integration tests
phoenix-output/ Generated configs (gitignored)
```

Set `PYTHONPATH=src` for CLI and tests.

## Common commands

```bash
# Install dependencies
pip3 install -r requirements.txt
pip3 install -r web/requirements_web.txt

# Run tests
PYTHONPATH=src python3 -m pytest tests/ -q

# Orchestrator CLI
PYTHONPATH=src python3 src/main.py status
PYTHONPATH=src python3 src/main.py generate

# Remote deploy to active Doprax nodes
PYTHONPATH=src python3 deploy/remote_deploy.py

# Reports
PYTHONPATH=src python3 src/completion_report_final.py

# Panel
cd web && ./run.sh
```

## Adding a protocol

1. Add `src/protocols/<name>_config.py` implementing the shared base interface.
2. Register it in `src/orchestrator/config_generator.py`.
3. Add server bootstrap in `deploy/remote_deploy.py` if needed.
4. Add unit tests under `tests/unit/`.

## Panel authentication

Credentials come from `.env`:

- `PHOENIX_PANEL_USER` (default: `admin`)
- `PHOENIX_PANEL_PASSWORD` or `PHOENIX_PANEL_PASSWORD_HASH`
- `SECRET_KEY` for Flask sessions

## Output conventions

Configs are written to:

```
phoenix-output/configs/<protocol>/<vm_code>/client.*
phoenix-output/subscriptions/<vm_code>.txt
```

Never commit `.env` or `phoenix-output/`.

## Hard Mode

See `docs/hard_mode_guide.md` and `PHOENIX_V10_HARD_MODE.md` for SSH/ICMP tunnels, mesh P2P, and emergency fallback flows.
