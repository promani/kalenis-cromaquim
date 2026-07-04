#!/usr/bin/env bash
# Levanta el trytond local apuntando a la MISMA base de Supabase que usa
# producción (Cloudflare Containers). No hay base local separada ni sync.
# Los secretos se leen de .env (no están en este archivo).
set -euo pipefail
cd "$(dirname "$0")"

set -a; source .env; set +a

# Supabase en modo sesión (:5432, sin pgbouncer): el modo transacción rompe Tryton.
# Se quita el path /postgres porque la base se pasa con -d.
export TRYTOND_database__uri=$(echo "$DATABASE_URL" \
    | sed -e 's/:6543/:5432/' -e 's#/postgres?pgbouncer=true##' -e 's#/postgres$##')
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
export TRYTOND_web__root="$HOME/kalenis_front_end/frontend_dist_6.0"

echo "trytond -> Supabase (base 'postgres') en http://localhost:8000"
exec .venv/bin/trytond -d postgres -c trytond.dev.conf
