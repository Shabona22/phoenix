#!/usr/bin/env bash
# Pre-commit hook: block accidental secret commits
set -euo pipefail

BLOCKED_PATTERNS=(
  'DOPRAX_API_KEY=[^y]'
  '0eb9087c\.'
  '^\.env$'
  'phoenix-output/'
)

while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  for pat in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$file" | grep -qE "$pat"; then
      echo "BLOCKED: refusing to commit sensitive file/pattern: $file"
      exit 1
    fi
  done
  if [[ -f "$file" ]] && grep -qE 'DOPRAX_API_KEY=[a-zA-Z0-9._-]{20,}' "$file" 2>/dev/null; then
    if [[ "$file" != ".env.example" ]]; then
      echo "BLOCKED: $file appears to contain a real DOPRAX_API_KEY"
      exit 1
    fi
  fi
done < <(git diff --cached --name-only --diff-filter=ACM)

exit 0
