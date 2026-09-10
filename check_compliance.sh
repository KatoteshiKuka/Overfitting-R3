#!/usr/bin/env bash
# Verifica che un branch feature non abbia toccato i file globali sotto lock.
# Uso: ./check_compliance.sh [base]   (base di default: origin/main, con fallback su main)
set -euo pipefail

BASE="${1:-}"
if [ -z "$BASE" ]; then
  if git rev-parse --verify --quiet origin/main >/dev/null; then
    BASE="origin/main"
  else
    BASE="main"
  fi
fi

# File che solo l'Orchestratore può modificare (vedi REVIEWER_PROMPT.md).
PROTECTED='^(backend/app/main\.py|backend/pyproject\.toml|backend/uv\.lock|frontend/src/routes\.tsx|frontend/package\.json|frontend/pnpm-lock\.yaml|frontend/tailwind\.config\.ts|frontend/src/styles/theme\.css)$'

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if ! git rev-parse --verify --quiet "$BASE" >/dev/null; then
  echo "check_compliance: base '$BASE' non trovata, salto il controllo."
  exit 0
fi

CHANGED="$(git diff --name-only "$BASE"...HEAD)"
VIOLATIONS="$(printf '%s\n' "$CHANGED" | grep -E "$PROTECTED" || true)"

if [ -n "$VIOLATIONS" ]; then
  echo "COMPLIANCE FALLITA — il branch '$BRANCH' modifica file globali sotto lock:"
  printf '  - %s\n' $VIOLATIONS
  echo
  echo "Questi file li tocca solo l'Orchestratore. Annota la riga che ti serve in STATE.md"
  echo "nella sezione 'Richieste di modifica ai file globali' e chiedi l'integrazione."
  echo "Se questa PR E' l'integrazione, aggiungi la label 'integration'."
  exit 1
fi

echo "COMPLIANCE OK — nessun file globale toccato da '$BRANCH'."
