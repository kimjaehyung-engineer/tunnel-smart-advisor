# Tunnel Smart Advisor

AI-powered tunnel construction risk intelligence and knowledge graph platform.

The application analyzes tunnel site conditions such as process, ground condition, location, method, equipment, and free-text context, then returns ranked construction risks, mitigation strategies, and a knowledge graph.

## Project Structure

```text
backend/                 FastAPI API server
frontend/                React + Vite + TypeScript web client
data/
  tunnel_checklist/      Main tunnel ontology CSVs and source Excel checklist
  raw/                   Source PDFs and extracted raw text
  processed/             One-off processed CSV outputs
  neo4j_import/          Neo4j import-ready CSV exports
scripts/
  ontology/              Scripts that build or update tunnel ontology CSVs
  neo4j/                 Scripts that generate Neo4j CSV exports
  tools/                 Utility/debug scripts
scratch/                 Temporary inspection notes and previews
docs/                    Plans and operating documentation
```

## Requirements

- Python 3.11+
- Node.js 20+
- pip
- npm

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

Install frontend dependencies from the committed lockfile:

```powershell
npm ci --prefix frontend
```

Copy `.env.example` to `.env` when local overrides are needed. Production deployments must set `TUNNEL_ENV=production`, explicit `TUNNEL_CORS_ORIGINS`, `TUNNEL_DB_PATH`, and `VITE_API_BASE_URL` instead of relying on development defaults. This internal PoC does not implement user login or API key authentication; access is controlled by the deployed network/server boundary.

## Run the App

Start the API server:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
```

Start the React frontend in a second terminal:

```powershell
npm run dev --prefix frontend
```

Or start/restart both local servers with one command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 -Restart
```

Open:

- Frontend: http://127.0.0.1:2000/
- API health: http://127.0.0.1:8080/health
- API readiness: http://127.0.0.1:8080/health/ready
- API metrics: http://127.0.0.1:8080/metrics
- API docs: http://127.0.0.1:8080/docs

Do not use port `6000` for browser development. Major browsers block it as an unsafe port.

## Verification

Run backend syntax checks:

```powershell
python -m compileall -q backend scripts scratch
python scripts/tools/validate_ontology.py
python scripts/tools/smoke_load_data.py
pytest tests/backend -q
```

Run frontend tests and production build:

```powershell
npm ci --prefix frontend
npm run test:run --prefix frontend
npm run build --prefix frontend
```

## Non-Docker Deployment

Build the frontend static artifact:

```powershell
npm ci --prefix frontend
npm run build --prefix frontend
```

Deploy by running the backend with a process manager (for example Windows Task Scheduler, NSSM, systemd, or another supervisor) and serving `frontend/dist/` with a static web server or reverse proxy.

Quick API smoke test after starting the backend:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/health').read().decode())"
```

Smoke test a data endpoint:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/nodes/ground').status)"
```

The backend emits JSON logs to stdout. Startup logs include the data directory, CORS origins, and CSV row counts. API responses include `X-Request-ID`, and `/score/` logs include request id, selected filters, result count, and latency. `/metrics` exposes in-memory request count, latency, error count, score latency, and data-load failure count for the current process.

## Analysis History

Every `/score/` request is persisted to SQLite and returns a `history_id`. The default local database is `data/runtime/tunnel_history.sqlite3`; override it with `TUNNEL_DB_PATH` for staging/production persistent storage. The frontend History page reads `GET /history/analyses` with search, project, and date filters, and details are available at `GET /history/analyses/{history_id}`. Saved analyses can be re-executed with `POST /history/analyses/{history_id}/rerun`, which creates a new history snapshot.

## Reports

Saved analyses are exposed as reports without an extra report database. `GET /reports` lists available reports derived from analysis history, `GET /reports/{history_id}.html` renders a downloadable HTML snapshot, `GET /reports/{history_id}.pdf` returns a generated PDF summary, and `POST /reports/{history_id}/share` persists shared/unshared state.

## Notifications

Runtime notifications are persisted in the same SQLite database. `GET /notifications` lists system, data, and analysis-completion notifications; `POST /notifications/{id}/read`, `POST /notifications/{id}/important`, and `POST /notifications/read-all` persist read and important state. `/score/` creates an analysis-completion notification for each saved analysis.

## Data and Ontology Scripts

The FastAPI backend reads the primary ontology from `data/tunnel_checklist/`.

Common maintenance commands:

```powershell
python scripts/ontology/build_master_ontology.py
python scripts/ontology/expand_ontology.py
python scripts/neo4j/generate_rail_neo4j.py
python scripts/tools/extract_text.py "data/raw/input.pdf" "data/raw/output.txt"
```

Standard ontology refresh gate:

```powershell
python scripts/ontology/refresh_ontology.py --skip-smoke
```

With the backend running, omit `--skip-smoke` to verify `/health/ready`. The script also calls `/admin/cache/reload` after validation/tests so the in-process CSV cache is refreshed without a restart.

Generated dependency/build folders such as `node_modules/`, `frontend/node_modules/`, `frontend/dist/`, and `frontend/tsconfig.tsbuildinfo` are intentionally ignored.
