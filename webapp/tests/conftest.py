"""Fixture condivise per i test della webapp GEKO."""

from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.models import Base, Magazine, MagazineStatus

WEBAPP_DIR = Path(__file__).resolve().parent.parent
TYPST_DIR = WEBAPP_DIR / "typst"
REPO_DIR = WEBAPP_DIR.parent


@pytest.fixture(scope="session", autouse=True)
def ensure_docker_like_typst_layout():
    """Garantisce che `webapp/typst/{src,assets}` esistano.

    In Docker `typst/src` è un mount di DIRECTORY della root del repo (vedi
    docker-compose.yml) e `typst/assets` un mount di `../assets`; in un
    checkout locale/CI nudo non esistono, e sia i doc generati da
    MagazineBuilder sia i probe di `try_compile_snippet` importano
    `../src/template.typ` relativo a `typst/generated/`. Creiamo symlink
    idempotenti verso la root del repo così i test di build funzionano
    anche a partire da un checkout pulito, senza toccare il layout Docker.
    """
    links = {
        TYPST_DIR / "src": REPO_DIR,
        TYPST_DIR / "assets": REPO_DIR / "assets",
    }
    for link_path, target in links.items():
        if link_path.exists() or link_path.is_symlink():
            continue
        link_path.parent.mkdir(parents=True, exist_ok=True)
        link_path.symlink_to(target)


@pytest_asyncio.fixture
async def db():
    """Sessione async su SQLite in-memory con schema creato da zero."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def sample_magazine(db):
    """Un numero rivista di prova, ritorna il suo id."""
    mag = Magazine(numero="99", mese="Gennaio", anno="2026", stato=MagazineStatus.BOZZA)
    db.add(mag)
    await db.commit()
    await db.refresh(mag)
    return {"id": mag.id, "numero": mag.numero}
