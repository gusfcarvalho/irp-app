from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.upload import router as upload_router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="IRPF SINACOR API", version="0.2.0", lifespan=lifespan)
app.include_router(upload_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
