"""
QuantAlpha Research Lab - FastAPI Backend
Entry point: runs on localhost:8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import (
    data, features, backtest, validation, model_lab,
    portfolio, risk, execution, quality_gate, live_research,
    monitoring, dashboard,
)

app = FastAPI(
    title="Alpha Research Lab API",
    version="1.0.0",
    description="Production-grade quantitative alpha research backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": "1.0.0"}


# Register all routers
app.include_router(data.router,          prefix="/api/data",          tags=["Data"])
app.include_router(features.router,      prefix="/api/features",      tags=["Features"])
app.include_router(backtest.router,      prefix="/api/backtest",      tags=["Backtest"])
app.include_router(validation.router,    prefix="/api/validation",    tags=["Validation"])
app.include_router(model_lab.router,     prefix="/api/model-lab",     tags=["Model Lab"])
app.include_router(portfolio.router,     prefix="/api/portfolio",     tags=["Portfolio"])
app.include_router(risk.router,          prefix="/api/risk",          tags=["Risk"])
app.include_router(execution.router,     prefix="/api/execution",     tags=["Execution"])
app.include_router(quality_gate.router,  prefix="/api/quality-gate",  tags=["Quality Gate"])
app.include_router(live_research.router, prefix="/api/live-research", tags=["Live Research"])
app.include_router(monitoring.router,    prefix="/api/monitoring",    tags=["Monitoring"])
app.include_router(dashboard.router,     prefix="/api/dashboard",     tags=["Dashboard"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
