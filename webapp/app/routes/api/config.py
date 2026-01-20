"""JSON API for configuration."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...database import get_db
from ...models import Config

router = APIRouter(prefix="/config")


class ConfigUpdate(BaseModel):
    """Request body for updating configuration."""
    # Dynamic key-value pairs
    class Config:
        extra = "allow"


@router.get("")
async def get_all_config(db: AsyncSession = Depends(get_db)):
    """Get all configuration values."""
    return await Config.get_all(db)


@router.get("/{key}")
async def get_config(key: str, db: AsyncSession = Depends(get_db)):
    """Get a single configuration value."""
    all_config = await Config.get_all(db)

    if key not in all_config:
        # Return default if exists
        if key in Config.DEFAULTS:
            default_val, desc = Config.DEFAULTS[key]
            return {
                "key": key,
                "value": default_val,
                "description": desc,
                "updated_at": None
            }
        return {"key": key, "value": "", "description": "", "updated_at": None}

    config_item = all_config[key]
    return {
        "key": key,
        "value": config_item["value"],
        "description": config_item["description"],
        "updated_at": config_item["updated_at"].isoformat() if config_item["updated_at"] else None
    }


@router.put("")
async def update_config(data: dict, db: AsyncSession = Depends(get_db)):
    """Update configuration values."""
    for key, value in data.items():
        if isinstance(value, str):
            await Config.set(db, key, value)

    return {"status": "updated"}
