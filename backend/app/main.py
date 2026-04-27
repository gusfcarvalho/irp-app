from fastapi import FastAPI

from app.api.upload import router as upload_router
from app.db import init_db

app = FastAPI(title="IRPF SINACOR API", version="0.2.0")
app.include_router(upload_router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
