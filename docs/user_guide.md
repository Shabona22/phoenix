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

- Never commit `.env` to git (`.env` and `phoenix-output/` are gitignored)
- Rotate API keys if exposed in chat or logs
- Use kill switch in dry-run mode unless you have admin access

### Git hygiene (if secrets were ever committed)

Current repo history does **not** contain `.env` or `phoenix-output/`. If that changes:

```bash
# Stop tracking without deleting local files
git rm --cached .env
git rm -r --cached phoenix-output/

# Rewrite history (install git-filter-repo first)
git filter-repo --path .env --invert-paths
git filter-repo --path phoenix-output --invert-paths

# Force-push only after team agreement
# git push --force-with-lease
```

Install the pre-commit secret guard:

```bash
cp scripts/pre-commit-secrets.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### API key rotation

1. Revoke old key in Doprax panel
2. Create new key
3. Update local `.env`: `DOPRAX_API_KEY=new-key-here`
4. Never paste keys in chat

## Troubleshooting

- **API errors**: Check `DOPRAX_API_KEY` in `.env`
- **No nodes**: Run `provision` or add VMs in Doprax panel
- **Config missing IP**: Wait for VM to finish provisioning, then re-run `generate`
