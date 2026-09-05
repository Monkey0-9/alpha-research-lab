"""
QuantAlpha Research Lab - FastAPI Backend
Production-Grade Quantitative Alpha Research Platform
"""
import asyncio
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import (
    data, features, alpha_discovery, statistical_engine,
    model_lab, validation, quality_gate, portfolio,
    execution, risk, live_research, monitoring, dashboard,
    backtest
)

logger = logging.getLogger("quantalpha")


async def eod_market_sync_daemon():
    """Background asynchronous daemon for automated EOD market ingestion."""
    logger.info("QuantAlpha automated EOD market ingestion daemon initialized.")
    while True:
        try:
            # Check every 6 hours in background
            await asyncio.sleep(21600)
            from core.data_pipeline import data_pipeline
            logger.info("Executing scheduled EOD market data sync...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: data_pipeline.run_sync(provider="auto", persist=True))
            logger.info("Scheduled EOD market sync completed.")
        except asyncio.CancelledError:
            logger.info("EOD market ingestion daemon stopped gracefully.")
            break
        except Exception as exc:
            logger.error(f"EOD market sync daemon error: {exc}")
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    daemon_task = asyncio.create_task(eod_market_sync_daemon())
    yield
    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Alpha Research Lab API",
    version="2.0.0",
    description="Tier-1 Institutional Quantitative Alpha Research Backend Engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "environment": "institutional_production",
        "modules_online": 12
    }


# Register all 12 institutional modules + backtest router
app.include_router(dashboard.router,          prefix="/api/dashboard",          tags=["00 Dashboard"])
app.include_router(data.router,               prefix="/api/data",               tags=["01 Data"])
app.include_router(features.router,           prefix="/api/features",           tags=["02 Features"])
app.include_router(alpha_discovery.router,    prefix="/api/alpha-discovery",    tags=["03 Alpha Discovery"])
app.include_router(statistical_engine.router, prefix="/api/statistical-engine", tags=["04 Statistical Engine"])
app.include_router(model_lab.router,          prefix="/api/model-lab",          tags=["05 Model Lab"])
app.include_router(validation.router,         prefix="/api/validation",         tags=["06 Validation"])
app.include_router(quality_gate.router,       prefix="/api/quality-gate",       tags=["07 Quality Gate"])
app.include_router(portfolio.router,          prefix="/api/portfolio",          tags=["08 Portfolio"])
app.include_router(execution.router,          prefix="/api/execution",          tags=["09 Execution"])
app.include_router(risk.router,               prefix="/api/risk",               tags=["10 Risk"])
app.include_router(live_research.router,      prefix="/api/live-research",      tags=["11 Live Research"])
app.include_router(monitoring.router,         prefix="/api/monitoring",         tags=["12 Monitoring"])
app.include_router(backtest.router,           prefix="/api/backtest",           tags=["Backtest Engine"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
