# Phoenix VPN V10 – User Guide

## Setup

1. Copy `.env.example` to `.env` and set your `DOPRAX_API_KEY`
2. Install dependencies: `pip install -r requirements.txt`
3. Verify API connectivity: `python3 src/main.py status`

## Commands

| Command | Description |
|---------|-------------|
| `python3 src/main.py status` | List Doprax VMs |
| `python3 src/main.py generate` | Generate configs for all nodes |
| `python3 src/main.py provision --name my-node` | Create new VM |
| `python3 src/main.py deploy` | Prepare deploy bundles |
| `python3 src/main.py heal` | Run healing/fallback check |

## Generated Output

Configs are written to `phoenix-output/configs/{protocol}/{node_id}/`.

Subscriptions are exported to `phoenix-output/subscriptions/`.

## Server Deployment

1. Copy `deploy/` and generated configs to your server
2. Run `bash deploy/bootstrap.sh`
3. Verify with `bash deploy/health_check.sh`

## Security

- Never commit `.env` to git
- Rotate API keys if exposed
- Use kill switch in dry-run mode unless you have admin access

## Troubleshooting

- **API errors**: Check `DOPRAX_API_KEY` in `.env`
- **No nodes**: Run `provision` or add VMs in Doprax panel
- **Config missing IP**: Wait for VM to finish provisioning, then re-run `generate`
