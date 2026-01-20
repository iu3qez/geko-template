# =============================================================================
# GEKO Magazine Web App - Dockerfile
# =============================================================================
#
# Build multi-stage per immagine ottimizzata:
# 1. Stage "builder": installa dipendenze Python
# 2. Stage "runtime": immagine finale leggera
#
# Uso:
#   docker build -t geko-webapp .
#   docker run -p 8000:8000 -v ./data:/app/data geko-webapp
#
# Con docker-compose (raccomandato):
#   docker-compose up -d
#

# =============================================================================
# -----------------------------------------------------------------------------
# Stage 1: Builder - Installazione dipendenze
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Evita creazione file .pyc e buffering output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Installa dipendenze di build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e installa requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Immagine finale
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# Metadata
LABEL maintainer="GEKO Magazine Team"
LABEL description="GEKO Radio Magazine Web App"
LABEL version="1.0.1"

# Variabili ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Utente non-root per sicurezza
RUN groupadd --gid 1000 geko \
    && useradd --uid 1000 --gid geko --shell /bin/bash --create-home geko

WORKDIR /app

# Installa dipendenze runtime
# - fonts-linuxlibertine: font per Typst
# - fontconfig: gestione font
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-linuxlibertine \
    fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Copia wheels e installa
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copia applicazione
COPY --chown=geko:geko . .

# Crea directory dati con permessi corretti
RUN mkdir -p /app/data/articles /app/data/images /app/data/output /app/typst/generated \
    && chown -R geko:geko /app/data /app/typst

# Copia template Typst dalla directory parent (se presente)
# Nota: in produzione, montare come volume o copiare durante build
# COPY --chown=geko:geko ../template.typ /app/typst/

# Esponi porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Passa a utente non-root
USER geko

# Comando di avvio
# - workers: numero processi (1 per semplicità, aumentare in produzione)
# - host: bind su tutte le interfacce
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
