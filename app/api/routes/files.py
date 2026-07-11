import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/download")
async def download(file: str = Query(..., description="Path relative to DATASET_ROOT")):
    dataset_root = os.path.abspath(get_settings().dataset_root)
    # Strip leading slashes so an absolute path can't escape DATASET_ROOT.
    requested = os.path.normpath(os.path.join(dataset_root, file.lstrip("/")))

    if requested != dataset_root and not requested.startswith(dataset_root + os.sep):
        logger.warning("Rejected traversal attempt: %s", requested)
        raise HTTPException(status_code=404, detail="Unauthorized access.")
    if not (os.path.exists(requested) and os.path.isfile(requested)):
        raise HTTPException(status_code=404, detail="File not found.")

    logger.info("Serving download: %s", requested)
    return FileResponse(requested, filename=os.path.basename(requested))
