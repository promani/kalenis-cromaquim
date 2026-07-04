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

## Puesta en marcha local (referencia)

- Backend: requiere Python y PostgreSQL. Ver `backend/README.md`
  (`kalenis_cli.py`, `kalenis.conf.dist`) para setup y ejecución.
- Frontend: requiere el módulo `kalenis_user_view` instalado en Tryton y se compila
  con `./install.sh` desde `frontend/utils/`; el directorio `sao` generado se
  referencia en la sección `[web]` de la configuración de Tryton.

## Próximos pasos

- [ ] Crear el proyecto en Supabase y la base de datos para Tryton.
- [ ] Dockerizar el backend con su configuración (`kalenis.conf`).
- [ ] Crear el Worker + `wrangler.toml` para desplegar el contenedor en Cloudflare Containers.
- [ ] Definir storage para adjuntos (R2 o Supabase Storage).
- [ ] Configurar dominio, DNS y TLS en Cloudflare.
- [ ] Documentar el proceso de actualización desde los repos upstream.
