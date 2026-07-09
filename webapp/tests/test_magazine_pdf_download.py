"""Regression: il download PDF non deve servire una copia in cache stantia.

Bug: dopo aver rigenerato il PDF (contenuti cambiati), il download restituiva
il PDF vecchio. Causa: `FileResponse` emette `Last-Modified`/`ETag` ma nessun
`Cache-Control`, quindi il browser applica il caching euristico (RFC 9111
§4.2.2) e serve la copia in cache senza rivalidare. Fix: `Cache-Control:
no-cache` sull'endpoint di download, così il browser rivalida sempre (e con
ETag che cambia a ogni build riceve il file aggiornato).
"""

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app


@pytest.fixture
def client(db):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


async def test_download_pdf_sets_no_cache(client, sample_magazine):
    """Il download deve inibire il caching euristico del browser."""
    # Scrive un PDF fittizio dove l'endpoint lo cerca (CWD-relative).
    pdf_path = Path("data") / "output" / f"geko{sample_magazine['numero']}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4 fake")
    try:
        async with client as c:
            resp = await c.get(f"/api/magazines/{sample_magazine['id']}/pdf")
        assert resp.status_code == 200
        cache_control = resp.headers.get("cache-control", "").lower()
        # no-cache o no-store: entrambi forzano la rivalidazione/refetch.
        assert "no-cache" in cache_control or "no-store" in cache_control, (
            f"Cache-Control mancante o permissivo: {cache_control!r}"
        )
    finally:
        os.remove(pdf_path)
