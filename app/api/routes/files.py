import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/download")
async def download(file: str = Query(..., description="Path relative to MEDIA_ROOT")):
    media_root = os.path.abspath(get_settings().media_root)
    # Strip leading slashes so an absolute path can't escape MEDIA_ROOT.
    requested = os.path.normpath(os.path.join(media_root, file.lstrip("/")))

    if requested != media_root and not requested.startswith(media_root + os.sep):
        logger.warning("Rejected traversal attempt: %s", requested)
        raise HTTPException(status_code=404, detail="Unauthorized access.")
    if not (os.path.exists(requested) and os.path.isfile(requested)):
        raise HTTPException(status_code=404, detail="File not found.")

    logger.info("Serving download: %s", requested)
    return FileResponse(requested, filename=os.path.basename(requested))
