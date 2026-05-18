# PRD P1/P2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue from the completed P0 slices and implement the remaining PRD requirements as small, testable vertical slices.

**Architecture:** Preserve the existing FastAPI router/service split and React page/component patterns. Add scoring model metadata and workflow APIs incrementally, keeping the existing CSV/pandas runtime model until there is enough data for real statistical modeling. Prefer explainable deterministic heuristics over pretending the current PoC is statistically validated.

**Tech Stack:** FastAPI, pandas CSV loaders, SQLite history/notification stores, React/Vite/TypeScript, TanStack Query, pytest, Vitest.

---

## Current Baseline

P0 is complete through `docs/superpowers/plans/2026-05-18-prd-p0-implementation-plan.md`:

- No login/API key policy is reflected in code and docs.
- Workspace risk-level filters, saved conditions, data version display, graph click detail, `Role`/`Standard`/`Impact` exposure, impact analysis filter, dashboard impact distribution, KCSC seed evidence, and source LL/cause/impact detail fields are implemented.
- Latest full verification before this plan:
  - `python -m compileall -q backend scripts scratch`
  - `python scripts/tools/validate_ontology.py`
  - `pytest tests/backend -q` → `49 passed`
  - `npm run test:run --prefix frontend` → `20 passed`
  - `npm run build --prefix frontend` → success with Vite chunk-size warning only.

## Files and Responsibilities

### Backend

- `backend/services/risk_scoring.py`: scoring model, risk level assignment, score rationale metadata.
- `backend/routers/score.py`: Score API response shape, model version inclusion, notification triggers for high-risk outcomes.
- `backend/services/history_store.py`: analysis history persistence and summary shape.
- `backend/routers/history.py`: rerun flow for saved analyses.
- `backend/routers/reports.py`: HTML/PDF report rendering, model version and rationale display.
- `backend/routers/compare.py` (new): design-change before/after comparison endpoint.
- `backend/services/design_compare.py` (new): deterministic comparison of two score responses.
- `backend/services/missing_review.py` (new): simple missing-risk/missing-condition recommendations.
- `backend/services/notification_store.py`: notification persistence; may need delete/archive fields.
- `scripts/ontology/build_master_ontology.py`: source schema extraction for P1 scoring fields when source Excel supports them.

### Frontend

- `frontend/src/types/index.ts`: Score API, model metadata, comparison, missing review, notification type extensions.
- `frontend/src/api/client.ts`: new compare/missing-review/notification operations.
- `frontend/src/api/queries.ts`: TanStack Query hooks/mutations.
- `frontend/src/pages/Workspace.tsx`: score rationale, model version, missing review recommendations.
- `frontend/src/pages/Reports.tsx`: model version/rationale visibility in report list if exposed.
- `frontend/src/pages/History.tsx`: model version in saved analysis table.
- `frontend/src/pages/Notifications.tsx`: delete/archive notification actions.
- New compare UI can be either `frontend/src/pages/DesignCompare.tsx` or an added mode inside Workspace; choose the smaller integration after inspecting routing.

---

## Slice 1: Explainable P1 Scoring Metadata

**Status:** Completed on 2026-05-18 using Oracle-recommended bounded rule-components v1 approach.

**Goal:** Extend the current deterministic score engine with explicit model metadata and per-risk explainability without claiming statistical validity.

**Files:**
- Modify: `backend/services/risk_scoring.py`
- Modify: `backend/routers/score.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Workspace.tsx`
- Test: `tests/backend/test_risk_scoring.py`, `tests/backend/test_score_api.py`, `frontend/src/pages/Workspace.test.tsx`

- [x] **Step 1: Decide formula details from Oracle recommendation**
  - Required input: Oracle result for minimal safe scoring slice.
  - Expected output: model fields and formula documented in this plan before code changes.

- [x] **Step 2: Write backend tests for model metadata**
  - Add tests requiring Score API responses to include a stable `model_version` and each risk to include explainability fields such as `likelihood`, `impact_score`, `confidence`, and `rationale`.
  - Run: `pytest tests/backend/test_score_api.py -q`
  - Expected: FAIL before implementation.

- [x] **Step 3: Implement minimal scoring metadata**
  - Add a constant model version, e.g. `MODEL_VERSION = "heuristic-v1"`.
  - Preserve existing ranking unless Oracle recommends a safe alternative.
  - Populate rationale from matched conditions, relation types, natural-language hits, and available `impact_text`/strategy count.

- [x] **Step 4: Render score rationale in Workspace**
  - Display model version near the data version.
  - Display per-risk score rationale in risk cards or a collapsible detail.

- [x] **Step 5: Verify**
  - Run: `pytest tests/backend/test_risk_scoring.py tests/backend/test_score_api.py -q`
  - Run: `npm run test:run --prefix frontend -- Workspace.test.tsx`

**Implemented formula summary:** `MODEL_VERSION = "p1_rule_components_v1"`; existing graph score is retained as `base_score`, then a capped component boost is computed from matched factor count, natural-language match, impact match/text, and evidence completeness. Frequency, recency, expert weight, and project similarity are exposed with neutral default `1.0` until the source data gains quantitative columns.

---

## Slice 2: Model Version in History and Reports

**Status:** Completed on 2026-05-18.

**Goal:** Satisfy PRD auditability/report requirements that reports include model version.

**Files:**
- Modify: `backend/services/history_store.py`
- Modify: `backend/routers/reports.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/History.tsx`
- Modify: `frontend/src/pages/Reports.tsx`
- Test: `tests/backend/test_history_api.py`, `tests/backend/test_reports_api.py`, `frontend/src/pages/History.test.tsx`, `frontend/src/pages/Reports.test.tsx`

- [x] **Step 1: Write backend tests**
  - History detail should preserve `result.model_version`.
  - HTML report should contain `모델 버전`.
  - PDF text lines should include `Model version`.

- [x] **Step 2: Implement report rendering**
  - Read `model_version` from saved result snapshots.
  - Add model version next to data version in HTML and PDF reports.

- [x] **Step 3: Add frontend list display**
  - Add optional `model_version` to report/history types.
  - Show model version as text or badge where table space allows.

- [x] **Step 4: Verify**
  - Run: `pytest tests/backend/test_history_api.py tests/backend/test_reports_api.py -q`
  - Run: `npm run test:run --prefix frontend -- History.test.tsx Reports.test.tsx`

---

## Slice 3: Missing Review Recommendations

**Status:** Completed on 2026-05-18.

**Goal:** Add P1-5 missing-risk/missing-condition recommendations as non-blocking “추가 검토 권고.”

**Files:**
- Create: `backend/services/missing_review.py`
- Modify: `backend/routers/score.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Workspace.tsx`
- Test: `tests/backend/test_missing_review.py`, `tests/backend/test_score_api.py`, `frontend/src/pages/Workspace.test.tsx`

- [x] **Step 1: Write recommendation tests**
  - NATM + 파쇄대 without 지하수/침하 context should recommend additional groundwater/settlement review if matching ontology relationships exist.
  - Empty or unrelated selections should return an empty list, not warnings.

- [x] **Step 2: Implement deterministic recommendation service**
  - Use existing ontology relationships and simple keyword rules.
  - Return objects like `{type, title, reason, suggested_filter}`.
  - Avoid hard errors; this is advisory only.

- [x] **Step 3: Expose in Score API**
  - Add `recommendations` to score response.

- [x] **Step 4: Render in Workspace**
  - Add a small card or section labelled `추가 검토 권고`.

- [x] **Step 5: Verify**
  - Run targeted backend and Workspace tests.

---

## Slice 4: Design-Change Comparison API

**Status:** Completed on 2026-05-18 for backend API.

**Goal:** Implement P1-4 backend comparison of before/after conditions.

**Files:**
- Create: `backend/services/design_compare.py`
- Create: `backend/routers/compare.py`
- Modify: `backend/routers/__init__.py`
- Modify: `backend/main.py`
- Test: `tests/backend/test_compare_api.py`

- [x] **Step 1: Write failing API test**
  - POST `/compare/design-change` with `{before: ScoreRequest, after: ScoreRequest}`.
  - Expect `new_risks`, `removed_risks`, `increased_risks`, `decreased_risks`, `additional_strategies`, `related_standards`.

- [x] **Step 2: Implement comparison service**
  - Reuse `score_risks` and graph-building helpers.
  - Compare top risk id sets and scores.
  - Keep output deterministic and limited to top 15 risks each side.

- [x] **Step 3: Register router**
  - Include compare router in `backend/main.py`.

- [x] **Step 4: Verify**
  - Run: `pytest tests/backend/test_compare_api.py -q`

---

## Slice 5: Design-Change Comparison UI

**Status:** Completed on 2026-05-18.

**Goal:** Provide a minimal UI for before/after condition comparison.

**Files:**
- Modify: route/navigation files after inspecting frontend router.
- Create or modify: `frontend/src/pages/DesignCompare.tsx` or `Workspace.tsx`.
- Modify: `frontend/src/api/client.ts`, `frontend/src/api/queries.ts`, `frontend/src/types/index.ts`
- Test: new or existing frontend test.

- [x] **Step 1: Inspect frontend routing and navigation**
- [x] **Step 2: Add API client and types**
- [x] **Step 3: Build minimal before/after filter form**
- [x] **Step 4: Render comparison result tables**
- [x] **Step 5: Verify frontend test and build**

---

## Slice 6: Report Quality Improvements

**Status:** Completed on 2026-05-18.

**Goal:** Expand HTML/PDF reports toward PRD P1-6.

**Files:**
- Modify: `backend/routers/reports.py`
- Test: `tests/backend/test_reports_api.py`

- [x] Include input conditions, top risks, scoring rationale, strategies, relationship summary, KCSC clauses, roles, written date, data version, and model version in HTML reports.
- [x] Keep PDF lightweight: include the same headings and top excerpts, accepting latin-1 fallback limitations already present.
- [x] Add tests for the presence of the major headings.

---

## Slice 7: Notification Lifecycle and High-Risk Events

**Status:** Completed on 2026-05-18.

**Goal:** Implement P1-7 missing notification events and lifecycle actions.

**Files:**
- Modify: `backend/services/notification_store.py`
- Modify: `backend/routers/notifications.py`
- Modify: `backend/routers/score.py`
- Modify: `scripts/ontology/refresh_ontology.py` if data update notifications are generated through the backend later.
- Modify: `frontend/src/pages/Notifications.tsx`
- Test: backend notification tests and frontend notification tests.

- [x] Add delete/archive state and endpoints.
- [x] Create high-risk notification when analysis has critical risks.
- [x] Create report-shared notification when share state changes.
- [x] Document data-update notification trigger path.

---

## Slice 8: Knowledge Library Detail (P2 Seed)

**Status:** Completed on 2026-05-18.

**Goal:** Add read-only detail pages before implementing admin authoring.

**Files:**
- Modify: `backend/routers/content.py`
- Modify: frontend library routing/page files.
- Test: backend and frontend library tests.

- [x] Add `GET /library/items/{risk_id}`.
- [x] Return risk detail, related conditions, strategies, impacts, standards, roles, and source fields.
- [x] Link list rows to detail page.
- [x] Render read-only detail page.

---

## Slice 9: P1-2 Gap-Analysis Risk Bands

**Status:** Completed on 2026-05-18 using Oracle-recommended additive gap-analysis bands.

**Goal:** Add auditable cluster-style risk bands without breaking existing percentile-derived `level`, graph colors, reports, or high-risk notifications.

**Files:**
- Modify: `backend/services/risk_scoring.py`
- Modify: `backend/routers/score.py`
- Modify: `backend/routers/reports.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/ui/RiskCard.tsx`
- Test: `tests/backend/test_risk_scoring.py`, `tests/backend/test_score_api.py`, `tests/backend/test_reports_api.py`, `frontend/src/api/client.test.ts`

- [x] Add dependency-free `compute_cluster_bands()` using deterministic score gap analysis.
- [x] Keep tied scores in the same band and limit output to at most four bands.
- [x] Expose per-risk `cluster_band`, `cluster_label`, score range, size, color, and rank.
- [x] Expose top-level `banding_method`, `banding_model_version`, `band_boundaries`, and fallback reason.
- [x] Render banding metadata in HTML/PDF reports while tolerating old histories.
- [x] Keep existing `level`, `color`, and `critical_count` behavior for compatibility.

**Implemented formula summary:** `MODEL_VERSION = "p1_rule_components_gap_bands_v1"`; `BANDING_MODEL_VERSION = "p1_gap_bands_v1"`. Bands are generated from adjusted score gaps where `gap >= max(score_range * 0.15, median_gap * 1.5, 0.001)`, with at most three cut points and four resulting bands (`B1` highest through `B4` lowest). Empty, small, tied, or uniform score sets return a single/fallback band rather than fabricating statistical clusters.

---

## Slice 10: P2-5 Operational Dashboard Signals

**Status:** Completed on 2026-05-18.

**Goal:** Surface operational dashboard signals requested by P2-5 without changing analysis/scoring behavior.

**Files:**
- Modify: `backend/routers/content.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Dashboard.tsx`
- Test: `tests/backend/test_dashboard_api.py`, `frontend/src/pages/Dashboard.test.tsx`

- [x] Add operational status summary to `GET /dashboard/summary`.
- [x] Include total risk count and top-risk candidate count.
- [x] Include data freshness and latest ontology build age from ontology version metadata.
- [x] Include system error/data-load failure status from in-memory metrics.
- [x] Include shared report count from report share state.
- [x] Render the status list in the Dashboard UI.

---

## Slice 11: Project Node API Exposure

**Status:** Completed on 2026-05-18.

**Goal:** Close PRD 9.2 `/nodes/{node_type}` support for `project` and seed P2-2 project graph integration.

**Files:**
- Modify: `backend/config.py`
- Modify: `backend/services/data_loader.py`
- Modify: `backend/routers/nodes.py`
- Test: `tests/backend/test_nodes_api.py`

- [x] Load `project` nodes from `data/tunnel_checklist/nodes_project.csv` when present, otherwise fall back to `data/processed/nodes_project.csv`.
- [x] Support `GET /nodes/project` sorted by project `name`.
- [x] Add PRD node-type regression coverage for `project`.

---

## Slice 12: P2-3 Backend Library Search Filters

**Status:** Completed on 2026-05-18.

**Goal:** Move Knowledge Library search toward backend-supported keyword/tag/relationship filtering while preserving the existing UI behavior.

**Files:**
- Modify: `backend/routers/content.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/queries.ts`
- Modify: `frontend/src/pages/Library.tsx`
- Test: `tests/backend/test_library_api.py`, `frontend/src/pages/Library.test.tsx`

- [x] Add optional `query`, `category`, and `tag` params to `GET /library/items`.
- [x] Search risk title, source project, and related tags server-side.
- [x] Keep category and popular tag facets available from the full data set.
- [x] Wire the Library page query hook to send current search/category/tag filters.
- [x] Preserve client-side filtering as a harmless second pass for compatibility.

---

## Slice 13: P2-4 Link-Based Report Sharing

**Status:** Completed on 2026-05-18.

**Goal:** Extend existing report share state into a link-based sharing workflow without adding user invitations or authentication.

**Files:**
- Modify: `backend/routers/reports.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Reports.tsx`
- Test: `tests/backend/test_reports_api.py`, `frontend/src/pages/Reports.test.tsx`

- [x] Return `share_url` for reports whose persisted share state is active.
- [x] Add `GET /reports/shared/{history_id}.html` for link-based shared report access.
- [x] Gate the shared URL with existing share state and return 404 when inactive.
- [x] Render a `공유 링크` action in the Reports table for shared reports.

---

## Slice 14: P1-3 Risk and Strategy Schema Fields

**Status:** Completed on 2026-05-18.

**Goal:** Extend the canonical ontology output and runtime APIs with P1-3 schema fields while keeping quantitative values honest until source data gains real columns.

**Files:**
- Modify: `scripts/ontology/build_master_ontology.py`
- Regenerate: `data/tunnel_checklist/nodes_risk.csv`, `data/tunnel_checklist/nodes_strategy.csv`, relationship CSVs, ontology version metadata
- Modify: `scripts/tools/validate_ontology.py`
- Modify: `backend/services/risk_scoring.py`
- Modify: `backend/services/graph_builder.py`
- Modify: `backend/routers/content.py`
- Modify: `backend/routers/nodes.py`
- Modify: `frontend/src/types/index.ts`, `frontend/src/pages/Workspace.tsx`, `frontend/src/pages/Library.tsx`
- Test: node, score, graph, library, workspace regressions

- [x] Add Risk fields: `cause`, `impact`, `likelihood`, `impact_score`, `frequency`, `recency`, `confidence`, `expert_weight`, `source_project`, `source_version`.
- [x] Add Strategy fields: `target_risk`, `expected_effect`, `required_equipment`, `related_standard`, `responsible_role`.
- [x] Use neutral quantitative defaults where the Excel source has no explicit values.
- [x] Expose `source_version` in score evidence, graph detail, and library detail.
- [x] Sanitize node API rows so optional blank CSV fields return JSON-safe empty strings instead of `NaN`.
- [x] Expand ontology validation required columns for the P1-3 schema.

---

## Slice 15: P1-7 Data Update Notification Event

**Status:** Completed on 2026-05-18.

**Goal:** Create an actual data-update notification from the operational cache reload path, not only a runbook reminder.

**Files:**
- Modify: `backend/main.py`
- Test: `tests/backend/test_notifications_api.py`

- [x] Create category `data` notification when `POST /admin/cache/reload` succeeds.
- [x] Include loaded risk and relationship counts in the notification message.
- [x] Keep existing reload response shape unchanged: `{status, data}`.

---

## Slice 16: P2-2 Canonical Project Graph Integration

**Status:** Completed on 2026-05-18.

**Goal:** Move project case information from string-only properties toward canonical Project graph nodes and Project↔Risk/Strategy relationships.

**Files:**
- Modify: `scripts/ontology/build_master_ontology.py`
- Regenerate: `data/tunnel_checklist/nodes_project.csv`, `rels_project_risk.csv`, `rels_project_strategy.csv`, `rels_total.csv`, ontology version metadata
- Modify: `backend/config.py`, `backend/services/data_loader.py`, `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_nodes_api.py`

- [x] Generate `Project` nodes from source Excel project names.
- [x] Add `HAS_RISK_CASE` relationships from Project to Risk.
- [x] Add `APPLIED_STRATEGY` relationships from Project to Strategy.
- [x] Include `project` in canonical `NODE_FILES` and ontology validation.
- [x] Verify relationship counts match Risk and Strategy row counts.

---

## Slice 17: P2-4 Report Package Download

**Status:** Completed on 2026-05-18.

**Goal:** Provide an external-submission-friendly report package without adding a separate report database.

**Files:**
- Modify: `backend/routers/reports.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Reports.tsx`
- Test: `tests/backend/test_reports_api.py`, `frontend/src/pages/Reports.test.tsx`

- [x] Add `package_url` to report list items.
- [x] Add `GET /reports/{history_id}.zip`.
- [x] Include HTML report, PDF report, and `metadata.json` in the ZIP package.
- [x] Render a `패키지` download link in the Reports table.

---

## Slice 18: Standards Search and Verification API

**Status:** Completed on 2026-05-18.

**Goal:** Expand the seeded KCSC Standards integration from evidence lookup into read-only search, clause search, and code verification endpoints.

**Files:**
- Modify: `backend/services/standards_evidence.py`
- Modify: `backend/routers/standards.py`
- Modify: `frontend/src/types/index.ts`, `frontend/src/api/client.ts`
- Test: `tests/backend/test_standards_api.py`, `frontend/src/api/client.test.ts`

- [x] Add `GET /standards/search` for unique standard summaries.
- [x] Add `GET /standards/clauses` for clause search with optional standard code filter.
- [x] Add `GET /standards/verify?code=...` for seeded KCS/KDS code validation.
- [x] Add frontend API types and client functions for future UI use.

---

## Slice 19: Standards Manual Revalidation API

**Status:** Completed on 2026-05-18.

**Goal:** Add a manual standards revalidation path over current ontology Standard nodes, satisfying the PRD requirement for 기준 업데이트 감지 또는 수동 재검증.

**Files:**
- Modify: `backend/services/standards_evidence.py`
- Modify: `backend/routers/standards.py`
- Modify: `frontend/src/types/index.ts`, `frontend/src/api/client.ts`
- Test: `tests/backend/test_standards_api.py`, `frontend/src/api/client.test.ts`

- [x] Add `POST /standards/revalidate`.
- [x] Distinguish exact verified KCS/KDS codes from keyword/alias candidate matches.
- [x] Return total, verified, candidate, unknown counts plus per-node status messages.
- [x] Add frontend client/types for future settings/admin UI use.

---

## Slice 20: Standards Link Persistence API

**Status:** Completed on 2026-05-18.

**Goal:** Add a lightweight persistence path for risk/strategy-to-standard clause links without mutating ontology CSV source data.

**Files:**
- Create: `backend/services/standards_link_store.py`
- Modify: `backend/routers/standards.py`
- Modify: `backend/main.py`
- Modify: `frontend/src/types/index.ts`, `frontend/src/api/client.ts`
- Test: `tests/backend/test_standards_api.py`

- [x] Add SQLite-backed `standards_links` table initialized at startup and lazily by store functions.
- [x] Add `POST /standards/links` with seeded KCSC code validation.
- [x] Add `GET /standards/links` with target/code filters.
- [x] Add frontend client/types for future Library/Workspace/Admin UI use.

---

## Slice 21: P2-1 Knowledge Registration Seed API

**Status:** Completed on 2026-05-18.

**Goal:** Seed the P2-1 administrator knowledge registration workflow without introducing user login/API keys or mutating canonical Excel/CSV data.

**Files:**
- Create: `backend/services/knowledge_store.py`
- Create: `backend/routers/admin_knowledge.py`
- Modify: `backend/routers/__init__.py`, `backend/main.py`
- Modify: `frontend/src/types/index.ts`, `frontend/src/api/client.ts`, `frontend/src/api/queries.ts`
- Test: `tests/backend/test_admin_knowledge_api.py`, `frontend/src/api/client.test.ts`

- [x] Add SQLite-backed `knowledge_submissions` table for risk, strategy, lesson, project, standard, equipment, and method submissions.
- [x] Add `POST /admin/knowledge/items` that stores submitted knowledge with `pending_review` verification status and ontology data-version snapshot.
- [x] Add `GET /admin/knowledge/items` filters for item type and verification status.
- [x] Add `POST /admin/knowledge/items/{id}/status` for verification/rejection curation.
- [x] Add frontend client/types/hooks for future Settings/Admin UI use.

---

## Slice 22: P2-1 Knowledge Registration Settings UI

**Status:** Completed on 2026-05-18.

**Goal:** Expose the knowledge registration queue through the existing Settings navigation so internal operators can submit and curate knowledge without direct SQLite access.

**Files:**
- Create: `frontend/src/pages/Settings.tsx`
- Create: `frontend/src/pages/Settings.test.tsx`
- Modify: `frontend/src/App.tsx`

- [x] Replace the `/settings` placeholder with a real Settings page.
- [x] Add a knowledge submission form for risk, strategy, lesson, project, standard, equipment, and method items.
- [x] Show submitted items with verification status and ontology data-version source file.
- [x] Add verification/rejection actions backed by existing TanStack Query mutations.
- [x] Add frontend regression coverage for submit and status update flows.

---

## Slice 23: P1-4 Design-Change Comparison Reports

**Status:** Completed on 2026-05-18.

**Goal:** Make design-change comparison results reusable as reports, closing the PRD requirement that comparison review output can become internal/external report material rather than only an in-session result.

**Files:**
- Create: `backend/services/comparison_report_store.py`
- Modify: `backend/main.py`, `backend/routers/compare.py`, `backend/routers/reports.py`
- Modify: `frontend/src/types/index.ts`, `frontend/src/api/client.ts`, `frontend/src/api/queries.ts`
- Modify: `frontend/src/pages/DesignCompare.tsx`, `frontend/src/pages/Reports.tsx`
- Test: `tests/backend/test_reports_api.py`, `frontend/src/api/client.test.ts`, `frontend/src/pages/DesignCompare.test.tsx`, `frontend/src/pages/Reports.test.tsx`

- [x] Add SQLite-backed comparison report snapshots storing before/after conditions, comparison result, model version, and ontology data-version snapshot.
- [x] Add `POST /compare/design-change/reports` to persist the current comparison and return report URLs.
- [x] Add `GET /reports/compare/{id}.html`, `.pdf`, and `.zip` for comparison report downloads.
- [x] Include comparison reports in `GET /reports` with `report_type: "comparison"` and comparison-specific download URLs.
- [x] Add Design Compare UI action to save a comparison report and open the generated HTML report.
- [x] Render comparison report entries in the Reports table without applying single-analysis share actions.

---

## Slice 24: P2-3 Library Full-Text and Relationship Search

**Status:** Completed on 2026-05-18.

**Goal:** Move Knowledge Library search closer to PRD P2-3 by preserving MVP keyword search while expanding backend matching across detail fields and adding relationship-type filtering.

**Files:**
- Modify: `backend/routers/content.py`
- Modify: `frontend/src/types/index.ts`, `frontend/src/api/client.ts`
- Modify: `frontend/src/pages/Library.tsx`
- Test: `tests/backend/test_library_api.py`, `frontend/src/pages/Library.test.tsx`, `frontend/src/api/client.test.ts`

- [x] Expand backend keyword search beyond title/project/tags into source LL, cause, impact text, strategy labels, standard labels, role labels, impact labels, and relationship types.
- [x] Add `relation_type` query filter to `GET /library/items`.
- [x] Return relation-type facets and per-item `relationTypes` metadata.
- [x] Add Library UI relation-type selector/sidebar filters using existing app styling.
- [x] Add backend and frontend regression coverage for relationship filtering and expanded search behavior.

---

## Slice 25: PRD 9.1 Score Risk Evidence Fields

**Status:** Completed on 2026-05-18.

**Goal:** Close the remaining Score API shape gap by exposing risk-level `standards`, `roles`, and top-level `source_evidence` fields directly in each risk item.

**Files:**
- Modify: `backend/routers/score.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/ui/RiskCard.tsx`
- Test: `tests/backend/test_score_api.py`, `frontend/src/pages/Workspace.test.tsx`

- [x] Resolve related standards through Risk → Strategy → Standard relationships.
- [x] Resolve responsible roles through Risk → Strategy → Role relationships.
- [x] Promote `source_evidence` to each top-level Score API risk item while keeping the nested explanation field for compatibility.
- [x] Extend frontend risk types and render standards/roles on risk cards when available.
- [x] Add backend regression assertions for the new fields.

---

## Slice 26: P2-2 Lesson Learned Node Exposure

**Status:** Completed on 2026-05-18.

**Goal:** Expose the existing Lesson Learned seed nodes through the runtime node API and ontology validation so PRD P2-2 lessons are visible to clients without mutating the canonical tunnel checklist CSVs.

**Files:**
- Modify: `backend/config.py`
- Modify: `backend/services/data_loader.py`
- Modify: `backend/routers/nodes.py`
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_nodes_api.py`

- [x] Load `data/neo4j_import/nodes_lesson.csv` as the `lesson` node frame with safe fallback seed rows.
- [x] Add `/nodes/lesson` support sorted by lesson `content`.
- [x] Validate required Lesson Learned fields and row count in ontology validation.
- [x] Add backend regression coverage for the Lesson Learned node API.
- [x] Keep lesson exposure additive; canonical `data/tunnel_checklist/rels_total.csv` is unchanged in this slice.

---

## Slice 27: P2-2 Lesson Learned Library Relationship Integration

**Status:** Completed on 2026-05-18.

**Goal:** Make Lesson Learned evidence useful in Knowledge Library list/detail/search by joining seed `LEARNED_AS` relations without mutating canonical `data/tunnel_checklist/rels_total.csv`.

**Files:**
- Modify: `backend/config.py`
- Modify: `backend/services/data_loader.py`
- Modify: `backend/routers/content.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Library.tsx`
- Test: `tests/backend/test_library_api.py`, `frontend/src/pages/Library.test.tsx`

- [x] Load lesson seed relationships from `data/neo4j_import/rels.csv` as `lesson_rels` while keeping `rels_total.csv` canonical.
- [x] Map seed `Risk_1` style IDs to canonical `Risk_001` IDs for `LEARNED_AS` lookups.
- [x] Include `LEARNED_AS` in Library relation-type facets/filtering and full-text search through lesson content.
- [x] Return `lessons` in `GET /library/items/{risk_id}` using Lesson Learned node `content` labels.
- [x] Render Lesson Learned evidence in the Library read-only detail panel.

---

## Slice 28: PRD 9.3 Standards Manual Revalidation UI

**Status:** Completed on 2026-05-18.

**Goal:** Expose the existing standards revalidation endpoint in the operator Settings UI so KCSC seed evidence checks are usable without calling the API manually.

**Files:**
- Modify: `frontend/src/api/queries.ts`
- Modify: `frontend/src/pages/Settings.tsx`
- Test: `frontend/src/pages/Settings.test.tsx`

- [x] Add a TanStack Query mutation wrapper for `POST /standards/revalidate`.
- [x] Add a Settings card with a manual “기준 코드 재검증” action.
- [x] Display source, total/verified/candidate/unknown counts, and top candidate messages.
- [x] Add frontend regression coverage for invoking revalidation and rendering the result.

---

## Slice 29: P1-7 System Error Notifications

**Status:** Completed on 2026-05-18.

**Goal:** Close the P1-7 system-error notification event by persisting an important system notification when an unhandled request exception reaches the API middleware.

**Files:**
- Modify: `backend/main.py`
- Test: `tests/backend/test_notifications_api.py`

- [x] Add regression coverage using `/health/ready` with a forced data-load exception and `raise_server_exceptions=False`.
- [x] Create an important `system` notification containing method, path, request id, and exception type.
- [x] Keep notification persistence defensive so a notification-store failure cannot mask the original request exception.

---

## Slice 30: PRD 10.3 Ontology Version Metadata Validation

**Status:** Completed on 2026-05-18.

**Goal:** Extend the ontology validation gate to cover PRD 10.3 source version/hash evidence, ensuring data refreshes fail if `ontology_version.json` is missing or incomplete.

**Files:**
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_ontology_validation.py`

- [x] Require ontology version metadata fields: `source_file`, `source_file_hash`, `source_file_mtime`, and `ontology_build_at`.
- [x] Reject blank or `missing` metadata values.
- [x] Validate `source_file_hash` as a 64-character SHA-256 hex digest.
- [x] Add focused regression tests for missing hash rejection and valid hash acceptance.

---

## Slice 31: P2-1/P2-3 Library Detail Related Graph Summary

**Status:** Completed on 2026-05-18.

**Goal:** Close the Library detail gap from PRD 6.3 by exposing related graph data alongside source evidence, without introducing a second vis-network canvas.

**Files:**
- Modify: `backend/routers/content.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Library.tsx`
- Test: `tests/backend/test_library_api.py`, `frontend/src/pages/Library.test.tsx`

- [x] Add `graph: { nodes, edges }` to `GET /library/items/{risk_id}` using existing related conditions, strategies, impacts, standards, roles, and lessons.
- [x] Preserve the existing flat Library detail fields for compatibility.
- [x] Render top graph relationships in the Library detail panel as readable relationship triples.
- [x] Add backend and frontend regression coverage for graph nodes/edges, including `LEARNED_AS` lesson edges.

---

## Slice 32: PRD 10.3 Relationship Type Validation

**Status:** Completed on 2026-05-18.

**Goal:** Strengthen the data refresh validation gate by rejecting unsupported ontology relationship `:TYPE` values before they reach runtime scoring/search.

**Files:**
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_ontology_validation.py`

- [x] Define the canonical allowed relation types currently present in `rels_total.csv`.
- [x] Validate `rels_total.csv` `:TYPE` values against the allow-list.
- [x] Add focused tests that reject a typo relationship and accept canonical relationship types.

---

## Slice 33: PRD 9.3 Standards Link Management UI

**Status:** Completed on 2026-05-18.

**Goal:** Expose the existing risk/strategy ↔ KDS/KCS clause link persistence API in the operator Settings UI, closing the manual usability gap for PRD 9.3 standards clause linkage.

**Files:**
- Modify: `frontend/src/api/queries.ts`
- Modify: `frontend/src/pages/Settings.tsx`
- Test: `frontend/src/pages/Settings.test.tsx`

- [x] Add query/mutation hooks for `GET /standards/links` and `POST /standards/links`.
- [x] Add a Settings form to save target type/id, standard code, clause path, label, and note.
- [x] Render recent saved standards links with target, standard, clause, and note columns.
- [x] Add frontend regression coverage for listing and creating standards links.

---

## Slice 34: PRD 10.3 Source Metadata Value Validation

**Status:** Completed on 2026-05-18.

**Goal:** Strengthen ontology validation so required provenance fields are present and populated, not merely declared as CSV columns.

**Files:**
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_ontology_validation.py`

- [x] Require non-empty `Risk.source_project` and `Risk.source_version` values.
- [x] Require non-empty `Strategy.source_project` values.
- [x] Reject blank or `missing` provenance values during validation.
- [x] Add focused tests for blank rejection and populated metadata acceptance.

---

## Slice 35: PRD 10.3 Risk Scoring Numeric Validation

**Status:** Completed on 2026-05-18.

**Goal:** Ensure P1 scoring columns remain machine-readable by rejecting non-numeric risk score values during ontology validation.

**Files:**
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_ontology_validation.py`

- [x] Validate `Risk.likelihood`, `Risk.impact_score`, `Risk.frequency`, `Risk.recency`, `Risk.confidence`, and `Risk.expert_weight` as numeric values.
- [x] Add focused tests rejecting non-numeric score fields and accepting valid numeric fields.
- [x] Keep validation integrated with the standard ontology refresh gate.

---

## Slice 36: PRD 10.3 Risk Scoring Range Validation

**Status:** Completed on 2026-05-18.

**Goal:** Extend numeric validation to reject out-of-range P1 scoring fields before runtime scoring clamps or consumes malformed values.

**Files:**
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_ontology_validation.py`

- [x] Validate `Risk.likelihood` and `Risk.impact_score` are within `1.0..5.0`.
- [x] Validate `Risk.confidence` is within `0.0..1.0`.
- [x] Validate `Risk.frequency`, `Risk.recency`, and `Risk.expert_weight` are non-negative.
- [x] Add focused tests for above-range and below-range rejection.

---

## Slice 37: P1-3 Strategy Required Value Validation

**Status:** Completed on 2026-05-18.

**Goal:** Strengthen P1-3 Strategy schema support by validating populated strategy provenance and target/effect fields during ontology refresh.

**Files:**
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_ontology_validation.py`

- [x] Require non-empty `Strategy.source_project`, `Strategy.target_risk`, and `Strategy.expected_effect` values.
- [x] Keep currently sparse `required_equipment`, `related_standard`, and `responsible_role` as schema-required columns only until source data is fully populated.
- [x] Add focused tests for blank strategy target rejection and populated strategy metadata acceptance.

---

## Slice 38: P1-3 Strategy Target Risk Reference Validation

**Status:** Completed on 2026-05-18.

**Goal:** Ensure populated `Strategy.target_risk` values point to existing Risk nodes so strategy metadata remains navigable and reportable.

**Files:**
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_ontology_validation.py`

- [x] Validate every `Strategy.target_risk` value against `Risk.id:ID` values.
- [x] Add focused tests for rejecting unknown target risks and accepting existing target risks.
- [x] Keep the check inside the standard ontology validation gate.

---

## Slice 39: P2-2 Lesson Learned Relation Validation

**Status:** Completed on 2026-05-18.

**Goal:** Validate the Lesson Learned seed relationships loaded for Library search/detail so broken `LEARNED_AS` edges fail during ontology validation.

**Files:**
- Modify: `scripts/tools/validate_ontology.py`
- Test: `tests/backend/test_ontology_validation.py`

- [x] Load `LESSON_RELS_FILE` during validation.
- [x] Require at least one `LEARNED_AS` row in the lesson relationship seed.
- [x] Validate `LEARNED_AS` start IDs against canonical Risk IDs and supported `Risk_1`/`Risk_001` aliases.
- [x] Validate `LEARNED_AS` end IDs against Lesson Learned node IDs.
- [x] Add focused tests for unknown lesson rejection and Risk alias acceptance.

---

## Full Verification Gate

Run after every completed slice:

```powershell
python -m compileall -q backend scripts scratch
python scripts/tools/validate_ontology.py
pytest tests/backend -q
npm run test:run --prefix frontend
npm run build --prefix frontend
```

Known acceptable warning:

- Vite may warn that the main chunk is larger than 500 kB. This is currently non-blocking unless bundle optimization is the active task.
