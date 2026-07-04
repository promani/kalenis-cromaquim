# Kalenis LIMS backend (Tryton 6.0) para Cloudflare Containers
FROM python:3.9-slim-bookworm

# Runtime: libpq (psycopg2), pango/gdk-pixbuf (WeasyPrint), fuentes para reportes
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
        libpq5 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 shared-mime-info fonts-dejavu-core curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend: install no-editable => los módulos quedan en trytond/modules/
COPY backend/ /app/backend/
RUN pip install --no-cache-dir ./backend && pip install --no-cache-dir 'numpy==1.23.5'
RUN apt-get purge -y build-essential libpq-dev && apt-get autoremove -y

# Frontend precompilado (Kalenis SAO dist para Tryton 6.0)
RUN mkdir -p /app/frontend \
    && curl -fsSL https://downloads.kalenislims.com/frontend_dist_6.0.tar.gz \
       | tar xz -C /app/frontend

COPY trytond.prod.conf /etc/trytond.conf

ENV TRYTOND_web__root=/app/frontend/frontend_dist_6.0
# TRYTOND_database__uri llega por env desde el Worker (secret TRYTOND_DATABASE_URI)

EXPOSE 8000
CMD ["trytond", "-d", "postgres", "-c", "/etc/trytond.conf"]
