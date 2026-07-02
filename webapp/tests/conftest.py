"""Fixture condivise per i test della webapp GEKO."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base, Magazine, MagazineStatus


@pytest_asyncio.fixture
async def db():
    """Sessione async su SQLite in-memory con schema creato da zero."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
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
