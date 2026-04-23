# Predictive Maintenance Agent — MVP

Rule-based agent. Detects CPU/latency/error spikes. Delegates actions to n8n.
Includes Prophet-based CPU forecasting with predictive webhook triggers.

## Structure

```
backend/
  main.py                  # FastAPI app
  requirements.txt
  models/schemas.py        # Pydantic models
  core/
    rules_engine.py        # IF/THEN rule evaluation (replace with ML in Phase 2)
    prometheus_sim.py      # Metric generator (replace with real Prometheus)
    state_store.py         # In-memory ring buffer (replace with Redis/TimescaleDB)
    action_layer.py        # Action execution + n8n delegation
    predictive_monitor.py  # CSV persistence + Prophet forecasting + threshold webhook
  api/
    metrics.py             # POST /metrics/ingest, GET /metrics/status, simulate
    alerts.py              # GET /alerts, POST /alerts/:id/resolve
    actions.py             # POST /actions/trigger/:action
    webhooks.py            # n8n webhook endpoints
dashboard/
  index.html               # Self-contained HTML dashboard (no build step)
n8n-examples/
  alert-handler-workflow.json   # Import into n8n directly
```

## Run backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

> Nota: `plotly` está incluido en dependencias para evitar el warning de Prophet:
> `Importing plotly failed. Interactive plots will not work.`

API docs: http://localhost:8000/docs

## Run dashboard

```bash
# Any static server works
cd dashboard
python -m http.server 3000
# Open http://localhost:3000
```

## Test with curl

```bash
# Manual metric ingest
curl -X POST http://localhost:8000/metrics/ingest \
  -H "Content-Type: application/json" \
  -d '{"cpu_percent":91,"ram_percent":70,"latency_ms":300,"error_rate":2}'

# Simulate a scenario
curl "http://localhost:8000/metrics/simulate?scenario=cascade"

# Check system status
curl http://localhost:8000/metrics/status | python -m json.tool

# Get alerts
curl http://localhost:8000/alerts/

# Forecast CPU for next 24h and trigger webhook on predicted threshold breach
curl "http://localhost:8000/metrics/predict/cpu?threshold=90&trigger_webhook=true" | python -m json.tool

# Debug Prophet dataset (ds,y)
curl "http://localhost:8000/metrics/debug/prophet-dataset?limit=20" | python -m json.tool
```

## Bootstrap rápido de datos para Prophet

Si aún no tienes histórico suficiente, puedes generar datos sintéticos:

```bash
python backend/scripts/bootstrap_prophet_data.py \
  --out backend/data/metrics.csv \
  --points 240 \
  --interval-minutes 60 \
  --spike-every 18
```

Luego ejecuta:

```bash
curl "http://localhost:8000/metrics/predict/cpu?threshold=90&trigger_webhook=false" | python -m json.tool
```

## n8n integration

1. Run n8n: `docker run -p 5678:5678 n8nio/n8n`
2. Import `n8n-examples/alert-handler-workflow.json`
3. Set `N8N_ENABLED = True` in `backend/core/action_layer.py`
4. Activate workflow in n8n

## Rules (core/rules_engine.py)

| Metric      | Threshold | Severity | Action         |
|-------------|-----------|----------|----------------|
| cpu_percent | > 80%     | WARNING  | scale_up       |
| cpu_percent | > 90%     | CRITICAL | scale_up       |
| ram_percent | > 85%     | WARNING  | clear_cache    |
| ram_percent | > 95%     | CRITICAL | restart_service|
| latency_ms  | > 500ms   | WARNING  | clear_cache    |
| latency_ms  | > 1000ms  | CRITICAL | scale_up       |
| error_rate  | > 5%      | WARNING  | alert_team     |
| error_rate  | > 10%     | CRITICAL | alert_team     |

## Phase 2 migration (ML)

1. Replace `core/rules_engine.py → evaluate()` with Isolation Forest inference
2. Replace `core/prometheus_sim.py` with real `prometheus_api_client` scrape
3. Replace `core/state_store.py` with TimescaleDB + Redis
4. All API contracts stay identical — no dashboard changes needed
