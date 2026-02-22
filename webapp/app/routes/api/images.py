"""JSON API for images."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import uuid
import aiofiles

from ...database import get_db
from ...models import Image, Article, Magazine, MagazineStatus

router = APIRouter(prefix="/images")

UPLOAD_DIR = "data/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class ImageUpdate(BaseModel):
    alt_text: Optional[str] = None
    article_id: Optional[int] = None


class ImageResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    path: str
    alt_text: str
    article_id: Optional[int]
    uploaded_at: datetime
    url: str
    is_published: bool

    class Config:
        from_attributes = True


def image_to_response(image: Image, is_published: bool = False) -> dict:
    """Convert Image model to response dict."""
    return {
        "id": image.id,
        "filename": image.filename,
        "original_filename": image.original_filename,
        "path": image.path,
        "alt_text": image.alt_text or "",
        "article_id": image.article_id,
        "uploaded_at": image.uploaded_at.isoformat() if image.uploaded_at else None,
        "url": image.url,
        "is_published": is_published,
    }


@router.get("")
async def list_images(
    article_id: Optional[int] = None,
    magazine_id: Optional[int] = None,
    published: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all images with optional filters."""
    query = (
        select(Image)
        .options(selectinload(Image.article).selectinload(Article.magazines))
        .order_by(Image.uploaded_at.desc())
    )

    if article_id:
        query = query.where(Image.article_id == article_id)

    result = await db.execute(query)
    images = result.scalars().all()

    # Filter by magazine or published status
    filtered_images = []
    for img in images:
        is_pub = False
        if img.article and img.article.magazines:
            is_pub = any(
                m.stato == MagazineStatus.PUBBLICATO
                for m in img.article.magazines
            )

            if magazine_id:
                if not any(m.id == magazine_id for m in img.article.magazines):
                    continue

        if published is not None:
            if is_pub != published:
                continue

        filtered_images.append(image_to_response(img, is_published=is_pub))

    return filtered_images


@router.get("/{image_id}")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single image by ID."""
    query = (
        select(Image)
        .options(selectinload(Image.article).selectinload(Article.magazines))
        .where(Image.id == image_id)
    )
    result = await db.execute(query)
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    is_pub = False
    if image.article and image.article.magazines:
        is_pub = any(
            m.stato == MagazineStatus.PUBBLICATO
            for m in image.article.magazines
        )

    return image_to_response(image, is_published=is_pub)


@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    article_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload a single image."""
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:8]
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in ".-_")
    filename = f"{unique_id}_{safe_name}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    # Validate article_id if provided
    if article_id:
        art_result = await db.execute(select(Article).where(Article.id == article_id))
        if not art_result.scalar_one_or_none():
            article_id = None

    # Create database record
    image = Image(
        filename=filename,
        original_filename=file.filename,
        path=filepath,
        article_id=article_id
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return image_to_response(image)


@router.post("/batch")
async def upload_images_batch(
    files: list[UploadFile] = File(...),
    article_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload multiple images."""
    results = []
    errors = []

    # Validate article_id once
    if article_id:
        art_result = await db.execute(select(Article).where(Article.id == article_id))
        if not art_result.scalar_one_or_none():
            article_id = None

    for file in files:
        try:
            # Validate file extension
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                errors.append({
                    "filename": file.filename,
                    "error": f"File type not allowed"
                })
                continue

            # Read file content
            content = await file.read()

            # Check file size
            if len(content) > MAX_FILE_SIZE:
                errors.append({
                    "filename": file.filename,
                    "error": "File too large"
                })
                continue

            # Generate unique filename
            unique_id = uuid.uuid4().hex[:8]
            safe_name = "".join(c for c in file.filename if c.isalnum() or c in ".-_")
            filename = f"{unique_id}_{safe_name}"
            filepath = os.path.join(UPLOAD_DIR, filename)

            # Ensure upload directory exists
            os.makedirs(UPLOAD_DIR, exist_ok=True)

            # Save file
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(content)

            # Create database record
            image = Image(
                filename=filename,
                original_filename=file.filename,
                path=filepath,
                article_id=article_id
            )
            db.add(image)
            await db.commit()
            await db.refresh(image)

            results.append(image_to_response(image))

        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "images": results,
        "errors": errors
    }


@router.put("/{image_id}")
async def update_image(
    image_id: int,
    data: ImageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update image metadata."""
    query = select(Image).where(Image.id == image_id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Update fields
    if data.alt_text is not None:
        image.alt_text = data.alt_text

    if data.article_id is not None:
        # Validate article exists
        if data.article_id > 0:
            art_result = await db.execute(select(Article).where(Article.id == data.article_id))
            if not art_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Article not found")
            image.article_id = data.article_id
        else:
            image.article_id = None

    await db.commit()
    await db.refresh(image)

    return image_to_response(image)


@router.delete("/{image_id}")
async def delete_image(image_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an image."""
    query = select(Image).where(Image.id == image_id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete file from disk
    if os.path.exists(image.path):
        os.remove(image.path)

    # Delete database record
    await db.delete(image)
    await db.commit()

    return {"status": "deleted"}
