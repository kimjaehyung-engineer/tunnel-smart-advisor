# tunnel-smart-advisor -- AGENTS.md

## 1. Project Purpose

**Purpose**: AI-powered tunnel construction risk intelligence and knowledge graph platform.
- Analyzes site conditions (ground, method, equipment, location) and suggests engineering risks + mitigation strategies based on a structured ontology.
- Serves as a decision-support tool for tunnel construction engineers.

**Evidence**: `backend/` -- FastAPI API with risk scoring and graph JSON services; `frontend/` -- React/Vite UI; `scripts/ontology/build_master_ontology.py` -- builds nodes/rels from Excel checklist.

---

## 2. Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React + Vite (TypeScript) in `frontend/` |
| **API Backend** | FastAPI in `backend/` |
| **Visualization** | vis-network in the React frontend, graph JSON from FastAPI |
| **Data** | Pandas (CSV, Excel), Python |
| **Knowledge Graph** | Neo4j CSV import format (nodes + rels) |
| **Styling** | Custom CSS with Pretendard font |

**Languages**: Python 73.7%, HTML 19.2%, JavaScript 7.1%

**Evidence**: `requirements.txt`, `backend/`, `frontend/package.json`.

---

## 3. Package Manager & Scripts

- **Package manager**: pip (no pyproject.toml or Poetry found)
- **requirements.txt** contents:
  `
  pandas
  fastapi
  uvicorn[standard]
  `

**Install**: pip install -r requirements.txt

**Run FastAPI backend**: uvicorn backend.main:app --host 127.0.0.1 --port 8080

**Run React frontend**: npm run dev --prefix frontend

**Important**: Do not use port 6000 for browser development. Major browsers block it as an unsafe X11 port.

**No** setup.py, pyproject.toml, or Makefile found. Frontend uses `frontend/package.json`.

---

## 4. Important Directories

| Directory | Purpose |
|-----------|---------|
| data/tunnel_checklist/ | Primary data directory -- contains all CSV node/rel files + source Excel checklist |
| data/neo4j_import/ | Separate Neo4j CSV set (nodes_lesson, nodes_process, nodes_project, nodes_risk, nodes_strategy, rels) -- for graph DB import |
| data/raw/ | Raw source PDFs and extracted text |
| data/processed/ | One-off processed CSV outputs |
| scripts/ontology/ | Ontology build and update scripts |
| scripts/neo4j/ | Neo4j CSV generation scripts |
| lib/ | Static assets: bindings/, tom-select/, vis-9.1.2/ (graph visualization library) |
| scratch/ | One-off inspection scripts: inspect_excel.py, save_excel_preview.py |

**Key data files** (all under data/tunnel_checklist/):
- nodes_risk.csv (52 KB), nodes_strategy.csv (70 KB) -- core knowledge base
- rels_total.csv (34 KB) -- integrated relationship graph
- 터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx -- source Excel (198 KB)

---

## 5. Build / Run / Test Commands

| Command | Description |
|---------|-------------|
| pip install -r requirements.txt | Install dependencies |
| uvicorn backend.main:app --host 127.0.0.1 --port 8080 | Launch the FastAPI backend |
| npm run dev --prefix frontend | Launch the React/Vite frontend on port 2000 |
| npm run build --prefix frontend | Type-check and build the React frontend |
| python scripts/ontology/build_master_ontology.py | Re-build master ontology CSV nodes/rels from source Excel |
| python scripts/ontology/expand_ontology.py | Run extended ontology expansion (more ground/standard keywords) |
| python scripts/tools/extract_text.py | Extract text from PDFs/documents |
| python scripts/ontology/generate_tunnel_nodes.py | Generate tunnel-specific nodes |
| python scripts/ontology/generate_tunnel_nodes_enriched.py | Generate enriched tunnel nodes |
| python scripts/ontology/generate_tunnel_rels.py | Generate tunnel relationships |
| python scripts/neo4j/generate_neo4j_csv.py | Generate Neo4j CSV export |
| python scripts/neo4j/generate_rail_neo4j.py | Generate rail-specific Neo4j CSVs |
| python scripts/tools/test_graph.py | Smoke-test knowledge graph JSON generation |
| python scripts/ontology/update_nodes_with_project.py | Update nodes with project metadata |

**No test framework** (pytest/unittest) found. No CI/CD configured.

---

## 6. Likely Workflows

1. **Data authoring**: Engineer maintains 터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx -- structured tunnel risk checklist
2. **Ontology build**: Run scripts/ontology/build_master_ontology.py --> generates CSV nodes/rels in data/tunnel_checklist/
3. **Graph export**: Run scripts/neo4j/generate_neo4j_csv.py / generate_rail_neo4j.py --> Neo4j import format in data/neo4j_import/
4. **App serve**: Run FastAPI + React
5. **Investigation**: Files in scratch/ used for one-off Excel inspection/debugging

---

## 7. Notable Risks & Conventions

### Warning: Hard-coded absolute paths
Ontology scripts now resolve paths relative to the repository root and write to `data/tunnel_checklist/`.

### Warning: No test framework
No unit/integration tests found. Changes to ontology build scripts carry high regression risk.

### Warning: No CI/CD
No GitHub Actions or deployment pipeline configured.

### Warning: Large binary asset in repo
터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx (198 KB) is committed to the repo -- source data should ideally be in a separate data repo or LFS.

### Warning: Korean file/directory names
All project data uses Korean naming. The entire codebase is Korean-language.

### Warning: Single-owner, early-stage repo
- Created 2026-05-05, only 24 commits, no description
- No issues, no PRs, no releases
- Likely a personal/side project in active prototyping
