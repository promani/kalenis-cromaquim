#!/usr/bin/env bash
# Levanta el trytond local apuntando a la MISMA base Neon (us-east-1) que usa
# producción (Cloudflare Containers). No hay base local separada ni sync.
# Los secretos se leen de .env (no están en este archivo).
set -euo pipefail
cd "$(dirname "$0")"

set -a; source .env; set +a

# Neon requiere sslmode=require; la base es 'neondb' (se pasa con -d).
# La URI de Neon está en .env como NEW_DABTASE_URL.
export TRYTOND_database__uri=$(python3 -c "
from urllib.parse import urlsplit, urlunsplit
import os
s = urlsplit(os.environ['NEW_DABTASE_URL'])
netloc = s.netloc if s.port else s.netloc + ':5432'
print(urlunsplit((s.scheme, netloc, '/neondb', 'sslmode=require', '')))")
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
export TRYTOND_web__root="$HOME/kalenis_front_end/frontend_dist_6.0"

echo "trytond -> Neon (base 'neondb') en http://localhost:8000"
exec .venv/bin/trytond -d neondb -c trytond.dev.conf
