# =============================================================================
# GEKO Radio Magazine — build e deploy in PRODUZIONE
# =============================================================================
# Build locale sull'host, niente registry (GHCR eliminato). L'immagine è
# costruita dal working tree del repo; i sorgenti Typst (template.typ) sono
# montati come directory su /app/typst/src, quindi le modifiche al template
# sono viste live senza rebuild.
#
# Uso tipico sul server di produzione:
#   make prod-deploy     # git pull + rebuild immagine + ricrea i container
# =============================================================================

# Il compose prod usa ${PWD} per i mount: va eseguito dalla dir webapp/.
COMPOSE := docker compose -f docker-compose.prod.yml

.PHONY: help prod-build prod-deploy prod-logs prod-down prod-ps test

help:
	@echo "GEKO — target disponibili:"
	@echo "  make prod-build   Builda l'immagine locale dal working tree corrente"
	@echo "  make prod-deploy  git pull + rebuild + ricrea i container (webapp + geko-mcp)"
	@echo "  make prod-logs    Segue i log del webapp"
	@echo "  make prod-ps      Stato dei container"
	@echo "  make prod-down    Ferma i servizi"
	@echo "  make test         Esegue la suite pytest (venv in webapp/.venv)"

# Builda l'immagine locale (webapp e geko-mcp condividono la stessa immagine)
prod-build:
	cd webapp && $(COMPOSE) build

# Deploy completo: aggiorna il codice, ricostruisce e ricrea i container.
# Il vecchio container resta su finché la nuova immagine è pronta (downtime minimo).
prod-deploy:
	git pull --ff-only
	cd webapp && $(COMPOSE) up -d --build
	@echo "Deploy completato. Stato:"
	cd webapp && $(COMPOSE) ps

prod-logs:
	cd webapp && $(COMPOSE) logs -f webapp

prod-ps:
	cd webapp && $(COMPOSE) ps

prod-down:
	cd webapp && $(COMPOSE) down

# Esegue i test con il venv locale (vedi CLAUDE.md)
test:
	cd webapp && .venv/bin/python -m pytest -q
