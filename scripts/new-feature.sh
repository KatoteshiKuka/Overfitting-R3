#!/usr/bin/env bash
# Genera lo scheletro di una feature (frontend + backend) senza toccare i file globali.
#
#   ./scripts/new-feature.sh tempi-attesa
#
# Crea le cartelle e i file, poi stampa le DUE righe da far accodare all'Orchestratore
# in routes.tsx e main.py. Non le scrive da solo: quei file sono append-only e sotto lock.
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Uso: $0 <nome-feature>   (kebab-case, es. tempi-attesa)" >&2
  exit 1
fi

SLUG="$1"
if ! [[ "$SLUG" =~ ^[a-z][a-z0-9-]*$ ]]; then
  echo "Il nome deve essere in kebab-case minuscolo (es. tempi-attesa)." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNAKE="${SLUG//-/_}"
# tempi-attesa -> TempiAttesa
PASCAL="$(echo "$SLUG" | awk -F- '{for(i=1;i<=NF;i++) printf toupper(substr($i,1,1)) substr($i,2)}')"

FE="$ROOT/frontend/src/features/$SLUG"
BE="$ROOT/backend/app/features/$SNAKE"

if [ -d "$FE" ] || [ -d "$BE" ]; then
  echo "La feature '$SLUG' esiste già. Scegli un altro nome." >&2
  exit 1
fi

mkdir -p "$FE" "$BE"

cat > "$FE/${PASCAL}Page.tsx" <<EOF
import { PageHeader } from '@/components/PageHeader';

export function ${PASCAL}Page() {
  return (
    <>
      <PageHeader title="${PASCAL}" description="Da scrivere." />
    </>
  );
}
EOF

cat > "$FE/use${PASCAL}.ts" <<EOF
import { apiGet } from '@/api/client';
import { useQuery } from '@tanstack/react-query';

// Sostituisci \`unknown\` con il tipo del contratto scritto in STATE.md.
export function use${PASCAL}() {
  return useQuery({
    queryKey: ['${SLUG}'],
    queryFn: () => apiGet<unknown>('/${SLUG}'),
  });
}
EOF

cat > "$BE/__init__.py" <<'EOF'
EOF

cat > "$BE/schemas.py" <<EOF
from pydantic import BaseModel


class ${PASCAL}Read(BaseModel):
    """Contratto della feature ${SLUG}. Tienilo allineato a STATE.md."""

    placeholder: str
EOF

cat > "$BE/service.py" <<EOF
from sqlalchemy.orm import Session

from app.features.${SNAKE}.schemas import ${PASCAL}Read


def get_${SNAKE}(db: Session) -> ${PASCAL}Read:
    # La logica sta qui: il router fa solo HTTP.
    del db
    return ${PASCAL}Read(placeholder="da implementare")
EOF

cat > "$BE/router.py" <<EOF
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.${SNAKE} import service
from app.features.${SNAKE}.schemas import ${PASCAL}Read

router = APIRouter(prefix="/${SLUG}", tags=["${SLUG}"])


@router.get("", response_model=${PASCAL}Read)
async def get_${SNAKE}(db: Annotated[Session, Depends(get_db)]) -> ${PASCAL}Read:
    return service.get_${SNAKE}(db)
EOF

cat <<EOF

Feature '$SLUG' creata.

  frontend/src/features/$SLUG/
  backend/app/features/$SNAKE/

Prossimi passi:

  1. Sposta la card in TASKS.md da TODO a IN_PROGRESS con il tuo ID agente.
  2. Scrivi il contratto di GET /api/v1/$SLUG in STATE.md.
  3. Chiedi all'Orchestratore di accodare queste due righe (file globali sotto lock):

     frontend/src/routes.tsx  ->  in fondo all'array ROUTES:
       { path: '/$SLUG', element: <${PASCAL}Page />, nav: { label: '${PASCAL}', icon: 'slot' } },
       import { ${PASCAL}Page } from '@/features/$SLUG/${PASCAL}Page';

     backend/app/main.py  ->  in fondo:
       from app.features.$SNAKE.router import router as ${SNAKE}_router  # noqa: E402
       app.include_router(${SNAKE}_router, prefix=settings.api_prefix)

  4. Prima del push: pnpm build, uv run ruff check ., ./check_compliance.sh
EOF
