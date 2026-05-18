# Repository Structure

## Runtime Code

- `backend/`: FastAPI app, routers, data loading, risk scoring, and graph JSON generation.
- `frontend/`: React/Vite application for filters, risk dashboard, and graph rendering.
- `legacy/`: Streamlit implementation retained as a migration reference.

## Data

- `data/tunnel_checklist/`: source Excel and active CSV ontology files used by runtime code.
- `data/raw/`: original PDFs and extracted text inputs.
- `data/processed/`: generated CSVs from exploratory parsing scripts.
- `data/neo4j_import/`: CSV files shaped for Neo4j import.

## Scripts

- `scripts/ontology/`: rebuilds or enriches the tunnel checklist ontology.
- `scripts/neo4j/`: creates Neo4j import files from raw rail/subway lessons data.
- `scripts/tools/`: utilities for text extraction and graph smoke testing.
- `scratch/`: short-lived inspection scripts and previews.

## Documentation

- `README.md`: overview, setup, run, and verification commands.
- `docs/RUNBOOK.md`: operational startup and troubleshooting notes.
- `docs/superpowers/plans/`: migration implementation plan archive.
