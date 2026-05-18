# PRD P0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the P0 requirements from `PRD.md` as small, testable vertical slices.

**Architecture:** Keep changes incremental and aligned with existing FastAPI router/service patterns and React page/component patterns. Prefer additive API expansion before richer UI workflows.

**Tech Stack:** FastAPI, pandas CSV loaders, SQLite stores, React/Vite/TypeScript, TanStack Query, Vitest, pytest.

---

## Slice 0: Remove API Key Authentication

**Status:** Completed on 2026-05-18.

**Files:**
- Modified: `backend/main.py`
- Modified: `backend/config.py`
- Modified: `tests/backend/test_admin_cache.py`
- Deleted: `tests/backend/test_api_key_guard.py`
- Modified: `scripts/ontology/refresh_ontology.py`
- Modified: `.env.example`, `README.md`, `docs/RUNBOOK.md`, `docs/ROADMAP.md`

- [x] Remove `TUNNEL_API_KEY` config.
- [x] Remove API key middleware and admin dependency.
- [x] Make `/admin/cache/reload` callable without auth.
- [x] Update admin cache test.
- [x] Remove API key docs and env sample.

**Verification:**

```powershell
python -m compileall -q backend scripts scratch
python scripts/tools/validate_ontology.py
pytest tests/backend -q
```

## Slice 1: Make Workspace Risk-Level Filters Functional

**Status:** Completed on 2026-05-18.

**Files:**
- Modified: `frontend/src/pages/Workspace.tsx`
- Modified: `frontend/src/pages/Workspace.test.tsx`

- [x] Add selected risk-level state.
- [x] Derive visible risks from selected levels.
- [x] Make `전체` clear selected levels.
- [x] Reset selected levels after new analysis and full filter reset.
- [x] Add frontend regression test.

**Verification:**

```powershell
npm run test:run --prefix frontend -- Workspace.test.tsx
npm run test:run --prefix frontend
npm run build --prefix frontend
```

## Slice 2: Expose Role, Standard, Impact Nodes

**Status:** Completed on 2026-05-18.

**Files:**
- Modified: `backend/config.py`
- Modified: `backend/services/data_loader.py`
- Modified: `backend/routers/nodes.py`
- Modified: `tests/backend/test_nodes_api.py`

- [x] Add `role`, `standard`, `impact` CSV paths to `NODE_FILES`.
- [x] Load the three node types in `load_data()`.
- [x] Add node display keys in `/nodes/{node_type}`.
- [x] Add API tests for `/nodes/role`, `/nodes/standard`, `/nodes/impact`.

**Verification:**

```powershell
pytest tests/backend/test_nodes_api.py tests/backend/test_admin_cache.py tests/backend/test_health_ready.py -q
pytest tests/backend -q
```

## Slice 3: Graph Node Click Detail Panel

**Status:** Completed on 2026-05-18 with enriched graph node metadata.

**Files:**
- Modify: `frontend/src/components/KnowledgeGraph.tsx`
- Modify: `frontend/src/pages/Workspace.tsx`
- Possibly create: `frontend/src/components/RiskDetailPanel.tsx`
- Modify: `frontend/src/types/index.ts`
- Test: `frontend/src/pages/Workspace.test.tsx`

- [x] Add optional `onNodeSelect` prop to `KnowledgeGraph`.
- [x] Register `network.on("click", ...)` and pass selected node id/data to parent.
- [x] Add Workspace selected evidence node state.
- [x] Render a detail panel with available graph node information first.
- [x] Add frontend test for node selection and detail panel rendering.
- [x] Expand backend/API graph node detail for related project, matched conditions, strategies, impacts, standards, and roles.
- [x] Add source LL/cause/impact text after canonical risk schema includes those fields.

## Slice 4: Condition Save

**Status:** Completed on 2026-05-18 for save/list/delete API and Workspace save action.

**Files:**
- Create: `backend/routers/conditions.py`
- Create: `backend/services/conditions_store.py`
- Modify: `backend/routers/__init__.py`
- Modify: `backend/main.py`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/queries.ts`
- Modify: `frontend/src/pages/Workspace.tsx`
- Test: new backend tests and `Workspace.test.tsx`

- [x] Store saved filter/query conditions globally in SQLite.
- [x] Enable the disabled `조건 저장` button.
- [x] Add backend list/delete APIs for saved conditions.
- [x] Add Workspace save action and success feedback.
- [x] Add saved-condition list/load/delete UI in Workspace.

## Slice 5: Data Version Display

**Status:** Completed on 2026-05-18.

**Files:**
- Modify: `scripts/ontology/build_master_ontology.py`
- Create: `data/tunnel_checklist/ontology_version.json` generated artifact if acceptable.
- Modify: `backend/services/data_loader.py`
- Modify: `backend/routers/score.py`
- Modify: `backend/routers/reports.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Workspace.tsx`

- [x] Generate ontology build metadata from source file name/hash and timestamp.
- [x] Include data version in score response and saved history.
- [x] Display version in Workspace and Reports.

## Slice 6: Impact Filter and Dashboard Metric

**Status:** Completed on 2026-05-18.

**Files:**
- Modify: `backend/services/risk_scoring.py`
- Modify: `backend/routers/score.py`
- Modify: `backend/routers/history.py`
- Modify: `backend/routers/conditions.py`
- Modify: `backend/routers/content.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/FilterPanel.tsx`
- Modify: `frontend/src/pages/Workspace.tsx`
- Modify: `frontend/src/pages/Dashboard.tsx`
- Test: backend scoring/API/condition tests and Workspace/Dashboard tests

- [x] Add `impact` as a selectable Workspace analysis condition.
- [x] Score risks through reverse `Risk -> Impact` `AFFECTS` relationships.
- [x] Preserve `impact` in saved conditions and analysis reruns.
- [x] Add impact distribution to dashboard summary and UI.
- [x] Add regression tests for impact scoring/API/UI paths.

## Slice 7: KCSC Standards Evidence Lookup

**Status:** Completed on 2026-05-18 as MCP-seeded evidence lookup.

**Files:**
- Create: `backend/services/standards_evidence.py`
- Create: `backend/routers/standards.py`
- Modify: `backend/routers/__init__.py`
- Modify: `backend/main.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/queries.ts`
- Modify: `frontend/src/pages/Workspace.tsx`
- Modify: `frontend/src/styles.css`
- Test: `tests/backend/test_standards_api.py` and `Workspace.test.tsx`

- [x] Use KCSC Standards MCP to identify current tunnel standard candidates and clause evidence.
- [x] Add `/standards/evidence` endpoint exposing code, standard name, clause path, excerpt, source URL, and version.
- [x] Connect graph node standard labels to KCSC evidence lookup in Workspace detail panel.
- [x] Render up to three KCSC evidence clauses with source links.
- [x] Add backend and frontend regression tests.

## Slice 8: Canonical Ontology Source-of-Truth Runbook

**Status:** Completed on 2026-05-18.

**Files:**
- Modify: `docs/RUNBOOK.md`
- Modify: `docs/superpowers/plans/2026-05-18-prd-p0-implementation-plan.md`

- [x] Document the Excel checklist in `data/tunnel_checklist/` as the official source of truth.
- [x] Document `scripts/ontology/build_master_ontology.py` as the canonical builder.
- [x] Classify expansion, legacy generation, Neo4j export, and tool scripts as auxiliary/experimental.
- [x] Document manual Excel replacement, rebuild, schema validation, smoke test, cache reload, and diff review workflow.

## Slice 9: Source LL, Cause, and Impact Detail Fields

**Status:** Completed on 2026-05-18.

**Files:**
- Modify: `scripts/ontology/build_master_ontology.py`
- Regenerate: `data/tunnel_checklist/nodes_risk.csv`
- Regenerate: `data/tunnel_checklist/ontology_version.json`
- Modify: `backend/services/graph_builder.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Workspace.tsx`
- Test: `tests/backend/test_graph_builder.py` and `Workspace.test.tsx`

- [x] Persist Excel risk title as `source_ll` in Risk nodes.
- [x] Persist Excel cause and impact columns as `cause` and `impact_text`.
- [x] Include source LL, cause, and impact text in graph node detail payloads.
- [x] Render the three fields in the Workspace selected-node detail panel.
- [x] Add backend and frontend regression checks.

## Deferred P1/P2 Work

- Statistical risk scoring model redesign.
- Clustering-based risk bands.
- Design-change before/after comparison workflow.
- KCSC Standards persisted integration service.
- Knowledge authoring/admin registration workflow.
