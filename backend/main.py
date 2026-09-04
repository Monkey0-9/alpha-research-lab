"""
QuantAlpha Research Lab - FastAPI Backend
Production-Grade Quantitative Alpha Research Platform
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import (
    data, features, alpha_discovery, statistical_engine,
    model_lab, validation, quality_gate, portfolio,
    execution, risk, live_research, monitoring, dashboard,
    backtest
)

app = FastAPI(
    title="Alpha Research Lab API",
    version="2.0.0",
    description="Tier-1 Institutional Quantitative Alpha Research Backend Engine",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
