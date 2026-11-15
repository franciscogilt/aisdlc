#!/usr/bin/env bash
# Protege la rama main: PR obligatorio, 1 aprobacion, revision de code owners
# y checks `quality` y `secrets` en verde. Requiere `gh` autenticado con permisos de admin.
# Uso: ./scripts/protect-main.sh OWNER/REPO
set -euo pipefail
REPO="${1:?Uso: $0 OWNER/REPO}"
gh api -X PUT "repos/${REPO}/branches/main/protection" --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["quality", "secrets"] },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "require_code_owner_reviews": true,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
echo "Proteccion aplicada a main en ${REPO}"
