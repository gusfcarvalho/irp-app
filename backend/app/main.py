from fastapi import FastAPI

from app.api.upload import router as upload_router

app = FastAPI(title="IRPF SINACOR API", version="0.1.0")
app.include_router(upload_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
