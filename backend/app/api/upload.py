from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

router = APIRouter(tags=["importer"])
UPLOAD_DIR = Path("/data/uploads")


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)) -> dict[str, str]:
    upload_id = str(uuid4())
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / f"{upload_id}_{file.filename}"
    data = await file.read()
    target.write_bytes(data)
    return {"id": upload_id, "filename": file.filename}
