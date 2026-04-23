from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.metrics import router as metrics_router
from .api.alerts import router as alerts_router
from .api.actions import router as actions_router
from .api.webhooks import router as webhooks_router

app = FastAPI(title="Predictive Maintenance Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
app.include_router(actions_router, prefix="/actions", tags=["actions"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["n8n"])


@app.get("/health")
def health():
    return {"status": "ok"}
