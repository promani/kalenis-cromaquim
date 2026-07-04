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

El despliegue se apoya en **Cloudflare** y **Supabase**:

- **Supabase**: provee el **PostgreSQL** gestionado que usa Tryton como base de datos.
  Toda la persistencia vive acá (los contenedores son efímeros).
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
                              Supabase PostgreSQL
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

# 4. Variables
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib   # WeasyPrint encuentra las libs de brew
export TRYTOND_database__uri=postgresql://localhost:5432
export TRYTOND_web__root=$HOME/kalenis_front_end/frontend_dist_6.0

# 5. Inicializar la base LOCAL (una sola vez; TRYTONPASSFILE evita el prompt de password)
brew install postgresql@16 && brew services start postgresql@16
createdb kalenislims
.venv/bin/trytond-admin -d kalenislims -c trytond.dev.conf --all -l es --email <email>
.venv/bin/trytond-admin -d kalenislims -c trytond.dev.conf -u lims_analysis_sheet user_view --activate-dependencies

# 6. Correr el servidor
.venv/bin/trytond -d kalenislims -c trytond.dev.conf
# → http://localhost:8000
```

### Supabase

**Importante:** inicializar Tryton directamente contra Supabase no es viable: el ORM
de Tryton hace decenas de miles de queries chicas y la latencia a `us-west-1` lo
convierte en horas. El camino es inicializar en el Postgres local y **migrar con
dump/restore** (COPY masivo, minutos):

```bash
# El pooler exige modo sesión (:5432, sin ?pgbouncer=true); el modo transacción rompe a Tryton
pg_dump -d kalenislims --no-owner --no-privileges | psql "$SUPABASE_SESSION_URL"
```

Tryton usa la base `postgres` del proyecto Supabase (schema `public`).

Notas:
- `numpy` debe quedar en `<1.24` (`pip install 'numpy==1.23.5'`): el `openpyxl 2.6.4`
  que pinea Kalenis usa `np.float`, eliminado en numpy 1.24.
- `trytond.dev.conf` está versionado y no contiene secretos; la URI de la base va por env.
- Desarrollo diario: usar la base local (rápida). Supabase queda como base del
  entorno desplegado.

## Próximos pasos

- [x] Crear el proyecto en Supabase y la base de datos para Tryton.
- [ ] Dockerizar el backend con su configuración (`kalenis.conf`).
- [ ] Crear el Worker + `wrangler.toml` para desplegar el contenedor en Cloudflare Containers.
- [ ] Definir storage para adjuntos (R2 o Supabase Storage).
- [ ] Configurar dominio, DNS y TLS en Cloudflare.
- [ ] Documentar el proceso de actualización desde los repos upstream.
