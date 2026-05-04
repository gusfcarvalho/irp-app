import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from app.api.b3_import import router as b3_import_router
from app.api.dashboard import router as dashboard_router
from app.api.manual_transactions import router as manual_transactions_router
from app.api.positions import router as positions_router
from app.api.quotes import router as quotes_router
from app.api.tax import router as tax_router
from app.api.ticker_aliases import router as ticker_aliases_router
from app.api.ticker_classifications import router as ticker_classifications_router
from app.api.upload import router as upload_router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="IRPF SINACOR API", version="0.2.0", lifespan=lifespan)
app.include_router(upload_router, prefix="/api")
app.include_router(b3_import_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(positions_router, prefix="/api")
app.include_router(quotes_router, prefix="/api")
app.include_router(manual_transactions_router, prefix="/api")
app.include_router(tax_router, prefix="/api")
app.include_router(ticker_aliases_router, prefix="/api")
app.include_router(ticker_classifications_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
