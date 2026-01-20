"""JSON API routes for GEKO Magazine."""

from fastapi import APIRouter

from .articles import router as articles_router
from .magazines import router as magazines_router
from .images import router as images_router
from .config import router as config_router

router = APIRouter(prefix="/api")

router.include_router(articles_router, tags=["articles"])
router.include_router(magazines_router, tags=["magazines"])
router.include_router(images_router, tags=["images"])
router.include_router(config_router, tags=["config"])
