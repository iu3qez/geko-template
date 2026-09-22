"""Database configuration and session management."""

from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.models import Base

# Database file path
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/geko.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_migrations(conn):
    """Run schema migrations for existing databases (sync, called via run_sync)."""
    def columns(table):
        try:
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            return {row[1] for row in result.fetchall()}
        except Exception:
            return None

    images_cols = columns("images")
    if images_cols is not None and "alt_text" not in images_cols:
        try:
            conn.execute(text("ALTER TABLE images ADD COLUMN alt_text TEXT DEFAULT ''"))
            print("Migration: added alt_text column to images")
        except Exception as e:
            print(f"Migration warning: {e}")

    magazines_cols = columns("magazines")
    if magazines_cols is not None and "pdf_built_at" not in magazines_cols:
        try:
            conn.execute(text("ALTER TABLE magazines ADD COLUMN pdf_built_at DATETIME"))
            print("Migration: added pdf_built_at column to magazines")
        except Exception as e:
            print(f"Migration warning: {e}")


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Create new tables
        await conn.run_sync(Base.metadata.create_all)
        # Run migrations for existing tables
        await conn.run_sync(run_migrations)


async def get_db():
    """Dependency for FastAPI routes."""
    async with async_session() as session:
        yield session
