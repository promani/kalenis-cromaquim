# Kalenis Cromaquim

## Fin del proyecto

Este repositorio es un **monorepo** que reúne el backend y el frontend de
[Kalenis LIMS](http://kalenislims.com/) para implementar el sistema de gestión de
laboratorio (LIMS) de **Cromaquim**. Kalenis LIMS es una solución open source
orientada a laboratorios de alimentos, bebidas y medio ambiente, alineada con las
normas ISO 17025 y GLP, y construida sobre [Tryton](https://www.tryton.org/).

El objetivo es tener en un solo lugar:

1. El código de ambos proyectos upstream, para poder aplicar personalizaciones
   propias de Cromaquim sin depender de los repos originales.
2. La configuración de despliegue (infraestructura, base de datos y publicación web).

## Estructura

| Carpeta     | Contenido | Origen |
|-------------|-----------|--------|
| `backend/`  | Kalenis LIMS backend: servidor Tryton en Python con los módulos `lims_*` | [Kalenis/kalenislims](https://github.com/Kalenis/kalenislims) |
| `frontend/` | Kalenis LIMS frontend: extensión de Tryton SAO (JavaScript) con list views mejoradas | [Kalenis/kalenis_frontend](https://github.com/Kalenis/kalenis_frontend) |

### Origen del código (snapshot)

El código se importó como copia limpia (sin historia git) desde estos commits,
para poder traer actualizaciones de upstream en el futuro:

- `backend/` ← `Kalenis/kalenislims @ bc33db4ebbb25d551d9973838cdc571a858faf93` (master, 2026-06-12)
- `frontend/` ← `Kalenis/kalenis_frontend @ 301d7c828865ad42d0b50490a40eabe4b31a5d19` (main, 2025-09-08)

Ambos proyectos son GPL-3.0 (ver los archivos `LICENSE`/`COPYRIGHT` en cada carpeta
y en cada módulo del backend); las modificaciones de este repo heredan esa licencia.

## Arquitectura de despliegue (plan)

El despliegue se apoya en **Cloudflare** y **Neon**:

- **Neon**: provee el **PostgreSQL** gestionado (base `neondb`, región `us-east-1`,
  cerca del contenedor de Miami para minimizar latencia). Toda la persistencia vive
  acá (los contenedores son efímeros). Conexión con `sslmode=require`. Es serverless
  (scale-to-zero): puede haber cold start tras inactividad.
  > Migrado de Supabase (us-west-1) a Neon (us-east-1) por latencia — ~45% más rápido.
  > La base de Supabase quedó como respaldo.
- **Cloudflare Containers**: el backend Tryton corre **dockerizado en Cloudflare
  Containers**, orquestado por un Worker (que hace de router/ingress hacia el
  contenedor). Cloudflare también aporta DNS, CDN y TLS del dominio público.
  Consideraciones: el disco del contenedor es efímero y las instancias tienen
  límites de CPU/memoria según el *instance type*, por lo que el estado debe ir
  siempre a Supabase y los adjuntos/archivos a un storage externo (p. ej. R2 o
  Supabase Storage).
- **Frontend**: al ser una extensión de SAO, el build resultante (carpeta `sao`) es
  estático. Se sirve desde el propio `trytond` dentro del contenedor (sección `[web]`
  de la configuración); alternativamente puede publicarse como assets estáticos del
  Worker o en Cloudflare Pages apuntando al backend como API (requiere CORS en Tryton).

```
Usuario ──► Cloudflare (DNS/CDN/TLS)
                │
                ▼
        Worker (ingress) ──► Cloudflare Container
                              └── trytond (backend + frontend SAO/Kalenis)
                                      │
                                      ▼
                              Neon PostgreSQL (us-east-1, base 'neondb')
```

## Puesta en marcha local

Requisitos: Python 3.9 (Tryton 6.0 no soporta versiones más nuevas), Homebrew.

```bash
# 1. Dependencias de sistema (macOS)
brew install libpq pango gdk-pixbuf libffi

# 2. Backend en el venv (psycopg2 necesita flags en Apple Silicon)
ARCHFLAGS="-arch arm64" \
LDFLAGS="-L/opt/homebrew/opt/libpq/lib -L/opt/homebrew/opt/openssl@3/lib" \
CPPFLAGS="-I/opt/homebrew/opt/libpq/include -I/opt/homebrew/opt/openssl@3/include" \
PATH=/opt/homebrew/opt/libpq/bin:$PATH \
.venv/bin/pip install -e ./backend

# 2b. Con install editable, trytond necesita los módulos en trytond/modules/: symlinks
MODDIR=.venv/lib/python3.9/site-packages/trytond/modules
for d in backend/lims*; do ln -sf "$PWD/$d" "$MODDIR/$(basename $d)"; done

# 3. Frontend precompilado (Tryton 6.0)
mkdir -p ~/kalenis_front_end
curl -fsSL https://downloads.kalenislims.com/frontend_dist_6.0.tar.gz | tar xz -C ~/kalenis_front_end

# 4. Correr el server local apuntando a Neon (MISMA base que producción)
./run-local.sh
# → http://localhost:8000  (lee la URI de .env; base 'neondb' de Neon)
```

### Una sola base: Neon

Local (desarrollo) y producción (Cloudflare Containers) usan **la misma base de
Neon** (`neondb`, `us-east-1`). No hay base local separada ni sincronización: los
cambios que hacés en local se ven en producción y viceversa. `run-local.sh` arma la
URI desde `.env` (variable `NEW_DABTASE_URL`) y levanta trytond contra Neon.

- Conexión: `sslmode=require` (obligatorio en Neon). trytond preserva el `sslmode`
  de la URI. La base se llama `neondb` (se pasa con `-d neondb`; en el contenedor
  vía la env `TRYTOND_DB=neondb`).
- Neon es **serverless (scale-to-zero)**: tras inactividad se pausa y el primer
  request paga un cold start.
- **Bootstrap / migraciones:** requieren `pg_dump` **≥ 17** (Supabase corría PG 17;
  Neon corre PG 18). Instalar `postgresql@17`.

**Respaldo:** la base de **Supabase** (us-west-1) quedó como copia de respaldo de
antes de la migración a Neon.

Notas:
- `numpy` debe quedar en `<1.24` (`pip install 'numpy==1.23.5'`): el `openpyxl 2.6.4`
  que pinea Kalenis usa `np.float`, eliminado en numpy 1.24.
- `trytond.dev.conf` y `run-local.sh` están versionados y no contienen secretos;
  la URI de la base (con password) se deriva de `.env`.

## Próximos pasos

- [x] Crear el proyecto en Supabase y la base de datos para Tryton.
- [x] Dockerizar el backend (`Dockerfile` + `trytond.prod.conf`).
- [x] Crear el Worker + `wrangler.jsonc` y desplegar en Cloudflare Containers
      → https://kalenis-cromaquim.promani7.workers.dev
- [ ] Definir storage para adjuntos (R2 o Supabase Storage).
- [ ] Configurar dominio propio, DNS y TLS en Cloudflare.
- [ ] Documentar el proceso de actualización desde los repos upstream.

### Deploy (Cloudflare Containers)

```bash
npm install
# secret con la URI de Supabase en modo sesión (una sola vez)
echo 'postgresql://<user>:<pass>@aws-1-us-west-1.pooler.supabase.com:5432' \
  | npx wrangler secret put TRYTOND_DATABASE_URI
# build de imagen + push + publicación del Worker
npx wrangler deploy
```

El Worker (`worker/index.js`) enruta cada request al contenedor (Durable Object
`KalenisBackend`, 1 instancia `standard`, se duerme tras 30 min sin tráfico — el
primer request posterior paga el arranque de Tryton).
