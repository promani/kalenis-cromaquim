# Scripts de configuración (Kalenis / Cromaquim)

Scripts de [proteus](https://docs.tryton.org/projects/proteus/) que arman la
configuración de negocio sobre una base Kalenis ya inicializada. Son
**idempotentes** (reejecutables sin duplicar) y se corren en orden.

Se aplican contra la base de Supabase (la única base; ver el README raíz):

```bash
set -a; source ../.env; set +a
export TRYTOND_database__uri=$(echo "$DATABASE_URL" \
    | sed -e 's/:6543/:5432/' -e 's#/postgres?pgbouncer=true##' -e 's#/postgres$##')
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
../.venv/bin/python 01_setup_compania_lab.py postgres
../.venv/bin/python 02_catalogo_microbiologia.py postgres
../.venv/bin/python 03_ingreso_muestras.py postgres
```

| Script | Qué crea |
|--------|----------|
| `01_setup_compania_lab.py` | Compañía CROMAQUIM SRL (CUIT, ARS), laboratorio Microbiología, María Soledad Kessel como profesional/responsable, departamento Microbiología |
| `02_catalogo_microbiologia.py` | Config de producto/cuaderno, 8 análisis de micro con métodos (ref. ISO), matrices Alimentos/Aguas y tipificaciones |
| `03_ingreso_muestras.py` | Año de trabajo 2026 con secuencias (entrada/muestra/servicio/informe) y tipos de fracción |

Los métodos usan referencias ISO como punto de partida: ajustar a los PNTs
reales de Cromaquim, y cargar límites/especificaciones por determinación.
