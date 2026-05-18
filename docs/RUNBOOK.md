# Runbook

## Local Development

1. Install backend dependencies: `pip install -r requirements.txt`
2. Install frontend dependencies: `npm ci --prefix frontend`
3. Start backend: `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080`
4. Start frontend: `npm run dev --prefix frontend`
5. Open http://127.0.0.1:2000/

Optional local configuration can be copied from `.env.example`. For production, set `TUNNEL_ENV=production`, `TUNNEL_CORS_ORIGINS`, `TUNNEL_DATA_DIR`, `TUNNEL_DB_PATH`, `TUNNEL_LOG_LEVEL`, and `VITE_API_BASE_URL` explicitly. This internal PoC does not implement user login or API key authentication; access is controlled by the deployed network/server boundary.

Production startup intentionally fails when `TUNNEL_ENV=production` and `TUNNEL_CORS_ORIGINS` is missing, empty, or `*`.

Shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 -Restart
```

## Expected Ports

| Service | Port | URL |
| --- | ---: | --- |
| FastAPI | 8080 | http://127.0.0.1:8080 |
| Vite dev server | 2000 | http://127.0.0.1:2000 |
| Vite preview | 4173 | http://127.0.0.1:4173 |

Avoid port `6000`; browsers block it as unsafe.

## Health Checks

```powershell
python -m compileall -q backend scripts scratch
python scripts/tools/validate_ontology.py
python scripts/tools/smoke_load_data.py
pytest tests/backend -q
npm ci --prefix frontend
npm run test:run --prefix frontend
npm run build --prefix frontend
```

## Non-Docker Deployment

```powershell
pip install -r requirements.txt
npm ci --prefix frontend
npm run build --prefix frontend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
```

Serve `frontend/dist/` with a static file server or reverse proxy, and proxy API requests to the FastAPI backend. Keep `data/tunnel_checklist/` readable by the backend process and set `TUNNEL_DB_PATH` to a persistent runtime path.

Production process checklist:

- backend command is supervised/restarted by the host process manager
- `frontend/dist/` is served by a static web server or reverse proxy
- `TUNNEL_ENV=production`
- `TUNNEL_CORS_ORIGINS` is set to the deployed frontend origin
- `TUNNEL_DATA_DIR` points to the deployed ontology CSV directory
- `TUNNEL_DB_PATH` points to persistent storage

With the backend running:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/health').read().decode())"
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/health/ready').read().decode())"
```

Expected health response:

```json
{"status":"ok"}
```

Data endpoint smoke test:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/nodes/ground').status)"
```

## Logs

- Backend logs are JSON lines written to stdout.
- Startup emits `event=startup_context` with data directory, CORS origins, and loaded CSV row counts.
- Every response includes an `X-Request-ID` header. Send `X-Request-ID` in the request to use a caller-provided id.
- `/score/` emits `event=score_request` with request id, selected filters, result count, and latency in milliseconds.
- Unhandled exceptions emit `event=request_exception` with traceback and request id.

## Metrics

`GET /metrics` returns in-memory process metrics:

- request count
- request latency average and p95
- error count
- score endpoint latency average and p95
- data load failure count

These metrics reset when the backend process restarts.

## Analysis History

- `/score/` stores each analysis request and result snapshot in SQLite, then returns `history_id`.
- Default local path: `data/runtime/tunnel_history.sqlite3`.
- Override with `TUNNEL_DB_PATH` in production and mount/backup that directory as persistent runtime data.
- `GET /history/analyses?query=<term>&project=<name>&date_from=<iso>&date_to=<iso>` lists recent analyses and searches query text, top risk, selected filters, source project text, and created-at ranges.
- `GET /history/analyses/{history_id}` returns the saved request metadata plus full result snapshot.
- `POST /history/analyses/{history_id}/rerun` replays saved filters and query through the same score engine, persists a new snapshot, and returns the new `history_id`.

## Reports

- `GET /reports` lists HTML reports derived from saved analysis history.
- `GET /reports/{history_id}.html` renders a standalone HTML report for browser viewing or saving.
- `GET /reports/{history_id}.pdf` downloads a generated PDF summary for the same saved analysis snapshot.
- `POST /reports/{history_id}/share` with `{ "shared": true|false }` persists report sharing state.
- Reports currently reuse the SQLite history store instead of maintaining a separate report table.

## Notifications

- `GET /notifications?filter=all|unread|important` lists persisted runtime notifications.
- `POST /notifications/{notification_id}/read` marks one notification as read.
- `POST /notifications/{notification_id}/important` with `{ "is_important": true|false }` toggles important state.
- `POST /notifications/read-all` marks all notifications as read.
- The backend seeds system/data operation notifications when the notification store is empty.
- `/score/` creates an analysis-completion notification after saving analysis history.

## Data Locations

- `data/tunnel_checklist/`: active CSV ontology used by the backend
- `data/raw/`: source PDFs and extracted text
- `data/processed/`: generated intermediate CSV outputs
- `data/neo4j_import/`: Neo4j import CSV bundle
- `data/runtime/`: ignored local runtime data such as SQLite analysis history

## Data Refresh Procedure

The official source of truth for the runtime ontology is the tunnel checklist Excel file in `data/tunnel_checklist/`:

- `터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx`

`scripts/ontology/build_master_ontology.py` is the canonical builder. It reads the source Excel, writes the active CSV ontology files under `data/tunnel_checklist/`, and updates `ontology_version.json` so analyses and reports can show the data build version.

Other ontology and Neo4j scripts are auxiliary/experimental utilities unless they are explicitly called by `build_master_ontology.py` or `refresh_ontology.py`:

- `scripts/ontology/expand_ontology.py`: optional expansion experiment for additional keywords.
- `scripts/ontology/generate_tunnel_nodes*.py`, `generate_tunnel_rels.py`: legacy/inspection generators.
- `scripts/neo4j/*.py`: export utilities for Neo4j import bundles, not the API runtime source.
- `scripts/tools/*`: validation, smoke tests, extraction, and inspection helpers.

After manually replacing the source Excel checklist or changing ontology scripts, run the standard refresh gate:

```powershell
python scripts/ontology/refresh_ontology.py
```

This performs ontology build, CSV schema validation, backend tests, `/health/ready` smoke test, cache reload, and CSV diff summary. If the backend is not running locally, use:

```powershell
python scripts/ontology/refresh_ontology.py --skip-smoke
```

Cache policy:

- The backend caches CSV data with `@lru_cache(maxsize=1)` after first load.
- Production deploys should restart the backend after data updates.
- `POST /admin/cache/reload` reloads the in-process CSV cache and returns row counts.
- Non-Docker deployments should update the host data directory and restart the backend or call the admin reload endpoint.

Manual Excel replacement checklist:

1. Replace only the source Excel in `data/tunnel_checklist/`, preserving the expected filename or updating `excel_file` in `build_master_ontology.py` deliberately.
2. Run `python scripts/ontology/refresh_ontology.py --skip-smoke` if no backend is running, or omit `--skip-smoke` when the local backend is available.
3. Review the CSV diff summary for unexpected node/relationship drops.
4. Confirm `data/tunnel_checklist/ontology_version.json` changed when the source Excel changed.
5. Restart the deployed backend or call `POST /admin/cache/reload` after publishing the updated CSVs.

## Troubleshooting

- If the frontend cannot reach the API, confirm the backend is running on `127.0.0.1:8080`.
- If node lists fail, confirm `data/tunnel_checklist/nodes_ground.csv` and `data/tunnel_checklist/rels_total.csv` exist.
- If updated CSVs do not appear in API responses, restart the backend or call `POST /admin/cache/reload`.
- If analysis history disappears after backend restart, confirm `TUNNEL_DB_PATH` points to a persistent directory such as `data/runtime/tunnel_history.sqlite3`.
- If the Reports page is empty, run at least one Workspace analysis first so `/score/` can save a history snapshot.
- If the Notifications page is empty after deleting runtime data, restart the backend or call `/notifications` so the SQLite notification store is initialized and seeded.
- If Vite or build output leaves generated files, they are covered by `.gitignore`.
