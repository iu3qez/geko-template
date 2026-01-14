#!/bin/bash
# =============================================================================
# GEKO Magazine - Script di Deploy
# =============================================================================
#
# Esegui sul server per aggiornare l'app dopo un push su GitHub.
#
# Uso:
#   ./scripts/deploy.sh
#
# Requisiti:
#   - Docker e docker-compose installati
#   - Login a GHCR fatto (se repo privato)
#   - File secrets/anthropic_key.txt presente
#
# =============================================================================

set -e  # Esci al primo errore

# Colori per output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Avvio deploy GEKO Magazine...${NC}"

# Vai alla directory dello script
cd "$(dirname "$0")/.."

# Pull nuova immagine
echo -e "${YELLOW}📥 Download nuova immagine da GHCR...${NC}"
docker-compose -f docker-compose.prod.yml pull

# Riavvia container
echo -e "${YELLOW}🔄 Riavvio container...${NC}"
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Cleanup immagini vecchie
echo -e "${YELLOW}🧹 Pulizia immagini obsolete...${NC}"
docker image prune -f

# Verifica stato
echo -e "${YELLOW}✅ Verifica stato...${NC}"
sleep 3
docker-compose -f docker-compose.prod.yml ps

echo -e "${GREEN}✅ Deploy completato!${NC}"
echo ""
echo "Verifica l'app su http://localhost:8000"
