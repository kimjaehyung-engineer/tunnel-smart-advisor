# Tunnel Smart Advisor Migration Plan

> Status: superseded by the current FastAPI backend and React/Vite frontend implementation. Legacy Streamlit/PyVis references below are retained as historical migration context only.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-file Streamlit app with a FastAPI Python backend + React/Vite SPA frontend, preserving all risk scoring, filtering, and graph visualization logic.

**Architecture:**
- **Backend (FastAPI):** Serves CSV data via REST endpoints, implements all risk scoring/filtering logic in Python/pandas, returns graph data as JSON `{ nodes, edges }`.
- **Frontend (React/Vite):** SPA with condition inputs, risk dashboard, and vis-network based knowledge graph — replaces Streamlit UI entirely.
- **Data:** Static CSV files under `터널표준체크리스트/` — unchanged, served by FastAPI.

**Tech Stack:** Python 3.11+, FastAPI, pandas, uvicorn, React 18+, Vite, TanStack Query, react-graph-vis (vis-network wrapper), Pretendard font (CDN).

---

## File Structure

```
tunnel-smart-advisor/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # BASE_DIR, CSV paths
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── nodes.py         # GET /nodes/{type} → node lists
│   │   └── score.py         # POST /score → risk results + graph data
│   └── services/
│       ├── __init__.py
│       ├── data_loader.py    # load_data() — loads 8 CSVs
│       ├── risk_scoring.py  # apply_filter(), score_risks(), classify_levels()
│       └── graph_builder.py # build_graph_json() → { nodes, edges }
├── frontend/
│   ├── (scaffolded via Vite)
│   └── src/
│       ├── api/             # TanStack Query hooks → FastAPI endpoints
│       ├── components/
│       │   ├── FilterPanel.tsx
│       │   ├── RiskDashboard.tsx
│       │   ├── RiskCard.tsx
│       │   ├── StrategyPanel.tsx
│       │   └── KnowledgeGraph.tsx
│       ├── types/
│       │   └── index.ts     # Risk, Node, GraphData interfaces
│       └── App.tsx
├── requirements.txt          # updated: fastapi, uvicorn[standard], pandas, pyvis
├── app.py                   # REMAINS — reference until new frontend verified
└── AGENTS.md                # updated: new stack + commands
```

---

## PHASE 1: Python 로직 분리 (Reference Implementation)

### Task 1: Create backend directory structure

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/services/__init__.py`

- [ ] **Step 1: Create directories**

```powershell
New-Item -ItemType Directory -Path "backend/routers" -Force
New-Item -ItemType Directory -Path "backend/services" -Force
# Add __init__.py files
".." | Set-Content "backend/__init__.py" -Encoding UTF8
".." | Set-Content "backend/routers/__init__.py" -Encoding UTF8
".." | Set-Content "backend/services/__init__.py" -Encoding UTF8
```

Run: verify `Test-Path backend/services/__init__.py`

- [ ] **Step 2: Write config.py**

```python
# backend/config.py
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "터널표준체크리스트"

NODE_FILES = {
    "ground":      DATA_DIR / "nodes_ground.csv",
    "method":      DATA_DIR / "nodes_method.csv",
    "equipment":   DATA_DIR / "nodes_equipment.csv",
    "risk":        DATA_DIR / "nodes_risk.csv",
    "process":     DATA_DIR / "nodes_process.csv",
    "location":    DATA_DIR / "nodes_location.csv",
    "strategy":    DATA_DIR / "nodes_strategy.csv",
}
RELS_FILE = DATA_DIR / "rels_total.csv"
```

- [ ] **Step 3: Write services/data_loader.py**

```python
# backend/services/data_loader.py
import pandas as pd
from pathlib import Path
from .config import NODE_FILES, RELS_FILE
from functools import lru_cache

@lru_cache(maxsize=1)
def load_data():
    """Load all 8 CSVs. Cached on first call. Matches original app.py lines 126-136."""
    return {
        "ground":     pd.read_csv(NODE_FILES["ground"]),
        "method":     pd.read_csv(NODE_FILES["method"]),
        "equipment":  pd.read_csv(NODE_FILES["equipment"]),
        "risk":       pd.read_csv(NODE_FILES["risk"]),
        "process":    pd.read_csv(NODE_FILES["process"]),
        "location":   pd.read_csv(NODE_FILES["location"]),
        "strategy":   pd.read_csv(NODE_FILES["strategy"]),
        "rels":       pd.read_csv(RELS_FILE),
    }
```

- [ ] **Step 4: Write services/risk_scoring.py**

```python
# backend/services/risk_scoring.py
import re
from collections import defaultdict
from .data_loader import load_data

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s))]

def apply_filter(df_rels, target_nodes, risk_scores, risk_matches, node_id, node_label, rel_type):
    """Port of original apply_filter — lines 177-187."""
    if node_id not in target_nodes:
        target_nodes[node_id] = (node_label, "#3b82f6")
        r_ids = df_rels[(df_rels[':START_ID'] == node_id) & (df_rels[':TYPE'] == rel_type)][':END_ID'].tolist()
        degree = len(r_ids) if r_ids else 1
        for r_id in r_ids:
            risk_scores[r_id] *= degree
            if node_label not in risk_matches[r_id]:
                risk_matches[r_id].append(node_label)

def score_risks(selection: dict, user_query: str = ""):
    """
   selection = {
        "process":  "1. 터널 본坑..."  or None,
        "ground":   "파쇄대"          or None,
        "location":"도심지"           or None,
        "method":   "NATM"            or None,
        "equipment":"탱크크레인"      or None,
    }
    user_query = free-text string (Korean)
    Returns: { sorted_risks, risk_levels, critical_count, target_nodes, risk_matches }
    """
    data = load_data()
    df_rels   = data["rels"]
    df_risk   = data["risk"]
    df_strat  = data["strategy"]
    df_proc   = data["process"]
    df_ground = data["ground"]
    df_loc    = data["location"]
    df_method = data["method"]
    df_equip  = data["equipment"]

    risk_scores  = defaultdict(lambda: 1.0)
    risk_matches = defaultdict(list)
    target_nodes = {}

    def apply(node_id, label, rel_type):
        apply_filter(df_rels, target_nodes, risk_scores, risk_matches, node_id, label, rel_type)

    # Dropdown filters
    if selection.get("process"):
        row = df_proc[df_proc['name'] == selection["process"]].iloc[0]
        apply(row['id:ID'], selection["process"], 'ENCOUNTERS')

    if selection.get("ground"):
        row = df_ground[df_ground['condition_name'] == selection["ground"]].iloc[0]
        apply(row['id:ID'], selection["ground"], 'TRIGGER')

    if selection.get("location"):
        row = df_loc[df_loc['loc_name'] == selection["location"]].iloc[0]
        apply(row['id:ID'], selection["location"], 'OCCURS_AT')

    if selection.get("method"):
        row = df_method[df_method['method_name'] == selection["method"]].iloc[0]
        apply(row['id:ID'], selection["method"], 'ASSOCIATED_WITH')

    if selection.get("equipment"):
        eq_id = df_equip[df_equip['equip_name'] == selection["equipment"]]['id:ID'].values[0]
        if eq_id not in target_nodes:
            target_nodes[eq_id] = (selection["equipment"], '#3b82f6')
            strat_ids = df_rels[(df_rels[':END_ID'] == eq_id) & (df_rels[':TYPE'] == 'REQUIRES')][':START_ID'].tolist()
            strat_ids = [s for s in strat_ids if s.startswith('Strat')]
            for s_id in strat_ids:
                r_ids = df_rels[(df_rels[':END_ID'] == s_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':START_ID'].tolist()
                degree = len(r_ids) if r_ids else 1
                for r_id in r_ids:
                    risk_scores[r_id] *= degree
                    if selection["equipment"] not in risk_matches[r_id]:
                        risk_matches[r_id].append(selection["equipment"])

    # Natural language filter
    if user_query:
        query_words = [w for w in re.split(r'\W+', user_query) if len(w) >= 2]

        for _, row in df_proc.dropna(subset=['name']).iterrows():
            name = row['name']
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'ENCOUNTERS')
                    break

        for _, row in df_ground.dropna(subset=['condition_name']).iterrows():
            name = row['condition_name']
            if name in user_query or (len(name) >= 2 and name[:2] in user_query):
                apply(row['id:ID'], name, 'TRIGGER')

        for _, row in df_loc.dropna(subset=['loc_name']).iterrows():
            name = row['loc_name']
            for cw in name.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'OCCURS_AT')
                    break

        for _, row in df_method.dropna(subset=['method_name']).iterrows():
            name = row['method_name']
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'ASSOCIATED_WITH')
                    break

        for _, row in df_equip.dropna(subset=['equip_name']).iterrows():
            name = row['equip_name']
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    eq_id = row['id:ID']
                    if eq_id not in target_nodes:
                        target_nodes[eq_id] = (name, '#8b5cf6')
                        strat_ids = df_rels[(df_rels[':END_ID'] == eq_id) & (df_rels[':TYPE'] == 'REQUIRES')][':START_ID'].tolist()
                        strat_ids = [s for s in strat_ids if s.startswith('Strat')]
                        for s_id in strat_ids:
                            r_ids = df_rels[(df_rels[':END_ID'] == s_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':START_ID'].tolist()
                            degree = len(r_ids) if r_ids else 1
                            for r_id in r_ids:
                                risk_scores[r_id] *= degree
                                if name not in risk_matches[r_id]:
                                    risk_matches[r_id].append(name)
                    break

        for _, row in df_risk.dropna(subset=['description']).iterrows():
            r_id = row['id:ID']
            desc = row['description']
            for qw in query_words:
                if qw in desc:
                    risk_scores[r_id] *= 2.0
                    if "자연어 내용 매칭" not in risk_matches[r_id]:
                        risk_matches[r_id].append("자연어 내용 매칭")

    if not risk_scores:
        return {"sorted_risks": [], "risk_levels": {}, "critical_count": 0,
                "target_nodes": {}, "risk_matches": {}}

    sorted_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
    total_risks  = len(sorted_risks)
    risk_levels  = {}

    for idx, (r_id, s) in enumerate(sorted_risks):
        percentile = (idx + 1) / total_risks
        if percentile <= 0.05:
            risk_levels[r_id] = ("최상위 위험", "#ef4444")
        elif percentile <= 0.20:
            risk_levels[r_id] = ("상위 위험", "#f97316")
        elif percentile <= 0.50:
            risk_levels[r_id] = ("중위험", "#eab308")
        else:
            risk_levels[r_id] = ("저위험", "#22c55e")

    critical_count = sum(1 for l, _ in risk_levels.values() if l == "최상위 위험")

    return {
        "sorted_risks":  sorted_risks,
        "risk_levels":   risk_levels,
        "critical_count": critical_count,
        "target_nodes":  target_nodes,
        "risk_matches":  risk_matches,
    }
```

- [ ] **Step 5: Write services/graph_builder.py**

```python
# backend/services/graph_builder.py
from .data_loader import load_data

def build_graph_json(target_nodes, sorted_risks, risk_levels, risk_matches, top_n=10, strategy_n=2):
    """
    Returns { nodes: [...], edges: [...] } for vis-network.
    Replaces pyvis Network() + save_graph() in app.py lines 389-421.
    """
    data = load_data()
    df_risk  = data["risk"]
    df_strat = data["strategy"]
    df_rels  = data["rels"]

    nodes = []
    edges = []

    # Condition nodes
    for t_id, (t_label, t_color) in target_nodes.items():
        nodes.append({"id": t_id, label": "Condition", "title": t_label,
                       "color": t_color, "size": 35})

    # Risk nodes (top_n)
    for r_id, score in sorted_risks[:top_n]:
        r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
        level_text, level_color = risk_levels.get(r_id, ("중위험", "#eab308"))
        is_critical = level_text == "최상위 위험"

        nodes.append({
            "id": r_id,
            "label": "Critical Risk" if is_critical else "Risk",
            "title": r_desc,
            "color": level_color,
            "size": 45 if is_critical else 25,
        })

        for t_id, (t_label, _) in target_nodes.items():
            if t_label in risk_matches.get(r_id, []):
                edges.append({
                    "from": t_id, "to": r_id,
                    "title": "RELATES_TO",
                    "width": 4 if is_critical else 1,
                    "color": "#94a3b8",
                })

        if is_critical:
            strat_ids = df_rels[
                (df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')
            ][':END_ID'].tolist()
            for s_id in strat_ids[:strategy_n]:
                s_row = df_strat[df_strat['id:ID'] == s_id]
                if s_row.empty:
                    continue
                s_label = s_row['action'].values[0]
                nodes.append({
                    "id": s_id,
                    "label": "Strategy",
                    "title": s_label,
                    "color": "#10b981",
                    "size": 20,
                })
                edges.append({
                    "from": r_id, "to": s_id,
                    "title": "MITIGATED",
                    "color": "#6ee7b7",
                })

    return {"nodes": nodes, "edges": edges}
```

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat(backend): extract Python logic from app.py into backend/services"
```

---

### Task 2: Create FastAPI Router — Nodes endpoint

**Files:**
- Create: `backend/routers/nodes.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write routers/nodes.py**

```python
# backend/routers/nodes.py
from fastapi import APIRouter
from .data_loader import load_data
from .risk_scoring import natural_sort_key

router = APIRouter(prefix="/nodes", tags=["nodes"])

@router.get("/{node_type}")
def get_nodes(node_type: str):
    """
    node_type: ground | method | equipment | risk | process | location | strategy
    Returns list of { id, name, label } sorted by natural sort.
    """
    key_map = {
        "ground":     "condition_name",
        "method":     "method_name",
        "equipment":  "equip_name",
        "risk":       "description",
        "process":    "name",
        "location":   "loc_name",
        "strategy":   "action",
    }
    name_key = key_map.get(node_type)
    if not name_key:
        return {"error": f"Unknown node type: {node_type}"}, 400

    data = load_data()
    df = data.get(node_type)
    if df is None:
        return {"error": f"No such node type: {node_type}"}, 404

    rows = (
        df.dropna(subset=[name_key])
        .sort_values(by=name_key, key=natural_sort_key)
        .to_dict(orient="records")
    )
    return {"nodes": rows, "type": node_type}
```

- [ ] **Step 2: Write main.py**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import nodes

app = FastAPI(title="Tunnel Smart Advisor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nodes.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Install and smoke test**

```powershell
pip install fastapi "uvicorn[standard]" pandas
cd backend
uvicorn main:app --reload --port 8000
# Then: Invoke-WebRequest http://localhost:8000/health -Method GET | ConvertFrom-Json
```

Expected: `{"status":"ok"}`

- [ ] **Step 4: Commit**

```bash
git add backend/main.py backend/routers/
git commit -m "feat(api): FastAPI app with /nodes/{type} endpoint"
```

---

### Task 3: Create FastAPI Router — Score endpoint

**Files:**
- Create: `backend/routers/score.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write routers/score.py**

```python
# backend/routers/score.py
from fastapi import APIRouter
from pydantic import BaseModel
from .risk_scoring import score_risks
from .graph_builder import build_graph_json

router = APIRouter(prefix="/score", tags=["risk"])

class ScoreRequest(BaseModel):
    process:   str | None = None
    ground:    str | None = None
    location:  str | None = None
    method:    str | None = None
    equipment: str | None = None
    query:     str = ""

@router.post("/")
def score(request: ScoreRequest):
    result = score_risks(
        selection={
            "process":  request.process,
            "ground":   request.ground,
            "location": request.location,
            "method":   request.method,
            "equipment": request.equipment,
        },
        user_query=request.query,
    )

    sorted_risks    = result["sorted_risks"]
    risk_levels     = result["risk_levels"]
    critical_count  = result["critical_count"]
    target_nodes    = result["target_nodes"]
    risk_matches    = result["risk_matches"]

    if not sorted_risks:
        return {
            "total_risks": 0, "critical_count": 0, "max_score": 0,
            "risks": [], "graph": {"nodes": [], "edges": []}
        }

    max_score = sorted_risks[0][1]

    # Build risk list (top 15, matching original app.py line 329)
    data = score_risks.__module__  # not needed — use imported data
    from .data_loader import load_data
    df_risk  = load_data()["risk"]
    df_strat = load_data()["strategy"]
    df_rels  = load_data()["rels"]

    risks_out = []
    for r_id, score in sorted_risks[:15]:
        r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
        level_text, level_color = risk_levels[r_id]
        matched_tags = " | ".join(risk_matches[r_id])

        # Strategies
        strat_ids = df_rels[
            (df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')
        ][':END_ID'].tolist()
        strategies = df_strat[df_strat['id:ID'].isin(strat_ids)]['action'].tolist()

        risks_out.append({
            "id":         r_id,
            "description": r_desc,
            "score":      round(score, 1),
            "level":      level_text,
            "color":      level_color,
            "matched":    matched_tags,
            "strategies": strategies,
        })

    graph = build_graph_json(target_nodes, sorted_risks, risk_levels, risk_matches)

    return {
        "total_risks":   len(sorted_risks),
        "critical_count": critical_count,
        "max_score":     round(max_score, 1),
        "risks":         risks_out,
        "graph":         graph,
    }
```

- [ ] **Step 2: Update main.py to include score router**

```python
# in backend/main.py, add:
from .routers import nodes, score
app.include_router(score.router)
```

- [ ] **Step 3: Smoke test**

```powershell
# With uvicorn running:
$body = @{
    process = "1. 터널 본坑 외벽 결정화 그라우팅"
    ground  = "파쇄대"
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8000/score/ -Method POST -Body $body -ContentType "application/json"
```

Expected: JSON with `total_risks`, `critical_count`, `risks[]`, `graph`

- [ ] **Step 4: Commit**

```bash
git add backend/routers/score.py backend/main.py
git commit -m "feat(api): POST /score endpoint returns risk results and graph JSON"
```

---

## PHASE 2: React/Vite 프론트엔드 스캐폴딩

### Task 4: Scaffold Vite React project

**Files:**
- Create: `frontend/` (via Vite)

- [ ] **Step 1: Scaffold Vite React TypeScript project**

```powershell
cd tunnel-smart-advisor
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install @tanstack/react-query react-graph-vis
```

- [ ] **Step 2: Add TanStack Query provider in main.tsx**

```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

root.render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
);
```

- [ ] **Step 3: Define types in src/types/index.ts**

```typescript
// src/types/index.ts
export interface RiskNode {
  id: string;
  description: string;
  score: number;
  level: string;
  color: string;
  matched: string;
  strategies: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  title: string;
  color: string;
  size: number;
}

export interface GraphEdge {
  from: string;
  to: string;
  title: string;
  color: string;
  width?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ScoreResponse {
  total_risks: number;
  critical_count: number;
  max_score: number;
  risks: RiskNode[];
  graph: GraphData;
}

export interface NodeItem {
  "id:ID": string;
  [key: string]: string;
}
```

- [ ] **Step 4: Create API hooks in src/api/queries.ts**

```typescript
// src/api/queries.ts
import { useQuery } from "@tanstack/react-query";
import type { ScoreResponse, NodeItem } from "../types";

const API_BASE = "http://localhost:8000";

export function useNodeList(type: string) {
  return useQuery({
    queryKey: ["nodes", type],
    queryFn: async (): Promise<{ nodes: NodeItem[] }> => {
      const res = await fetch(`${API_BASE}/nodes/${type}`);
      if (!res.ok) throw new Error(res.statusText);
      return res.json();
    },
    staleTime: 5 * 60 * 1000,  // CSV data rarely changes
  });
}

export function useRiskScore(body: Record<string, string | null>) {
  return useQuery({
    queryKey: ["score", body],
    queryFn: async (): Promise<ScoreResponse> => {
      const res = await fetch(`${API_BASE}/score/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(res.statusText);
      return res.json();
    },
    enabled: false,  // triggered manually
  });
}
```

- [ ] **Step 5: Build FilterPanel component — src/components/FilterPanel.tsx**

```typescript
// src/components/FilterPanel.tsx
import { useNodeList } from "../api/queries";

interface Props {
  values: Record<string, string | null>;
  onChange: (key: string, value: string | null) => void;
  onSearch: () => void;
}

const TYPES = ["process", "ground", "location", "method", "equipment"] as const;
const LABELS: Record<string, string> = {
  process: "1. 공종", ground: "2. 지반",
  location: "3. 위치", method: "4. 공법", equipment: "5. 장비",
};

export default function FilterPanel({ values, onChange, onSearch }: Props) {
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      {TYPES.map((type) => {
        const { data } = useNodeList(type);
        const options = data?.nodes ?? [];
        const nameKey = type === "process" ? "name"
          : type === "ground" ? "condition_name"
          : type === "equipment" ? "equip_name"
          : type === "method" ? "method_name"
          : "loc_name";

        return (
          <select
            key={type}
            value={values[type] ?? ""}
            onChange={(e) => onChange(type, e.target.value || null)}
          >
            <option value="">[상관없음/전체]</option>
            {options.map((n) => (
              <option key={n["id:ID"]} value={String(n[nameKey])}>
                {String(n[nameKey])}
              </option>
            ))}
          </select>
        );
      })}
      <button onClick={onSearch}>🚀 GO (분석 실행)</button>
    </div>
  );
}
```

- [ ] **Step 6: Build RiskDashboard + RiskCard — src/components/RiskDashboard.tsx**

```typescript
// src/components/RiskDashboard.tsx
import type { ScoreResponse } from "../types";

interface Props { data: ScoreResponse | null; }

export function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={cardStyle}>
      <div style={{ color: "#64748b", fontSize: "0.85rem" }}>{label}</div>
      <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{value}</div>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  background: "white", border: "1px solid #e2e8f0",
  borderRadius: 12, padding: "1rem",
  boxShadow: "0 4px 6px -1px rgba(0,0,0,0.05)",
};

export default function RiskDashboard({ data }: Props) {
  if (!data) return <div>👈 좌측 패널에서 현장 조건을 세팅하세요.</div>;
  return (
    <div>
      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <MetricCard label="총 식별된 위험 요소" value={`${data.total_risks} 건`} />
        <MetricCard label="최상위 핵심 위험" value={`${data.critical_count} 건`} />
        <MetricCard label="최고 위험도 스코어" value={`${data.max_score} 점`} />
      </div>
      {data.risks.map((risk) => (
        <div key={risk.id} style={{
          display: "flex", gap: 12, marginBottom: 12,
          borderLeft: `6px solid ${risk.color}`,
          background: "white", borderRadius: 8, padding: 16,
          boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>
              [{risk.level}] {risk.description}
            </div>
            <div style={{ color: "#64748b", fontSize: "0.85rem" }}>
              매칭 근거: {risk.matched}
            </div>
            {risk.strategies.length > 0 && (
              <div style={{ marginTop: 8, fontSize: "0.85rem" }}>
                <strong>🛠️ 대응전략:</strong>
                <ul>{risk.strategies.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}
          </div>
          <div style={{ textAlign: "center", padding: "8px 16px",
            border: `2px solid ${risk.color}`, borderRadius: 8 }}>
            <div style={{ fontSize: "0.7rem", color: risk.color, fontWeight: 800 }}>
              RISK SCORE
            </div>
            <div style={{ fontSize: "1.4rem", color: risk.color, fontWeight: 900 }}>
              {risk.score.toLocaleString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 7: Build KnowledgeGraph — src/components/KnowledgeGraph.tsx**

```typescript
// src/components/KnowledgeGraph.tsx
import Graph from "react-graph-vis";
import type { GraphData } from "../types";

interface Props { data: GraphData | null; }

export default function KnowledgeGraph({ data }: Props) {
  if (!data || data.nodes.length === 0) {
    return <div style={{ height: 520, display: "flex", alignItems: "center",
      justifyContent: "center", color: "#94a3b8" }}>
      조건을 선택하면 지식 그래프가 здесь 나타납니다.
    </div>;
  }

  const options = {
    nodes: { shape: "dot", font: { color: "#0f172a" } },
    edges: { width: 2 },
    physics: { repulsion: { nodeDistance: 150 }, springLength: 200 },
    height: "500px",
    width: "100%",
  };

  return <Graph graph={data} options={options} />;
}
```

- [ ] **Step 8: Write App.tsx — src/App.tsx**

```typescript
// src/App.tsx
import { useState } from "react";
import { useRiskScore } from "./api/queries";
import FilterPanel from "./components/FilterPanel";
import RiskDashboard from "./components/RiskDashboard";
import KnowledgeGraph from "./components/KnowledgeGraph";

const empty = { process: null, ground: null, location: null, method: null, equipment: null };

export default function App() {
  const [filters, setFilters] = useState<Record<string, string | null>>(empty);
  const [query, setQuery] = useState("");
  const scoreQuery = useRiskScore({ ...filters, query });

  const handleSearch = () => scoreQuery.refetch();

  return (
    <div style={{ fontFamily: "'Pretendard', sans-serif", padding: "1rem", maxWidth: 1400, margin: "0 auto" }}>
      <div style={{ fontSize: "2.2rem", fontWeight: 800, color: "#0f172a", marginBottom: 4 }}>
        Tunnel Engineering Smart Advisor
      </div>
      <div style={{ color: "#64748b", marginBottom: "1.5rem" }}>
        AI-Powered Risk Intelligence & Knowledge Graph
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <FilterPanel
          values={filters}
          onChange={(key, val) => setFilters(prev => ({ ...prev, [key]: val }))}
          onSearch={handleSearch}
        />
      </div>
      <div style={{ margin: "1rem 0" }}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="현장 상황을 자유롭게 입력하세요..."
          rows={3}
          style={{ width: "100%", padding: "0.5rem", borderRadius: 8, border: "1px solid #e2e8f0" }}
        />
      </div>

      <hr style={{ margin: "1rem 0" }} />

      {scoreQuery.data && (
        <RiskDashboard data={scoreQuery.data} />
      )}
      {scoreQuery.data?.graph && (
        <>
          <div style={{ margin: "2rem 0", fontWeight: 700, fontSize: "1.1rem" }}>
            🕸️ Knowledge Graph Topology
          </div>
          <KnowledgeGraph data={scoreQuery.data.graph} />
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 9: Add Pretendard font — update index.html**

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css" />
```

- [ ] **Step 10: Run dev server and smoke test**

```powershell
cd frontend
npm run dev -- --host 0.0.0.0 --port 2000
# Verify: http://localhost:2000 loads without errors
# Select dropdowns → click GO → risk results appear → graph renders
```

- [ ] **Step 11: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): React/Vite SPA with FilterPanel, RiskDashboard, KnowledgeGraph"
```

---

## PHASE 3: 통합 및 검증

### Task 5: Update requirements.txt and AGENTS.md

**Files:**
- Modify: `requirements.txt`
- Modify: `AGENTS.md`

- [ ] **Step 1: Update requirements.txt**

```
streamlit
pandas
pyvis
fastapi
uvicorn[standard]
```

- [ ] **Step 2: Update AGENTS.md**

Add new sections:
- Backend entry: `backend/main.py` — `uvicorn backend.main:app`
- Frontend dev: `npm run dev` in `frontend/`
- Combined dev: Run both backend (port 8000) and frontend (port 2000) simultaneously
- Updated file structure reflecting `backend/` and `frontend/` directories

- [ ] **Step 3: Commit**

```bash
git add requirements.txt AGENTS.md
git commit -m "chore: add FastAPI deps, update AGENTS.md for new architecture"
```

---

### Task 6: Final verification

- [ ] **Step 1: Start backend**

```powershell
cd tunnel-smart-advisor
uvicorn backend.main:app --reload --port 8000
```

- [ ] **Step 2: Start frontend**

```powershell
cd frontend
npm run dev -- --port 2000
```

- [ ] **Step 3: Manual smoke test**
1. Load http://localhost:2000 — app loads with title
2. Select "파쇄대" in ground dropdown
3. Enter "도심지 갱구부 굴착" in text area
4. Click GO
5. Verify: metrics appear (total risks, critical count), risk cards render, graph renders with nodes

- [ ] **Step 4: Compare with original Streamlit output**
- Run `streamlit run app.py` side-by-side — verify risk scores and graph topology match

---

## Effort Summary

| Phase | Tasks | Estimated Time |
|-------|-------|---------------|
| Phase 1 — Python 로직 분리 | Tasks 1–3 | 2–3 hours |
| Phase 2 — React/Vite 스캐폴딩 | Tasks 4 | 1–2 hours |
| Phase 3 — 통합 검증 | Tasks 5–6 | 30 min |
| **Total** | | **3.5 – 5.5 hours** |

**Notes:**
- Task 1 (`risk_scoring.py`) is the most critical — port all filtering/soring logic exactly from `app.py` lines 173–297.
- Task 3 (`score.py`) must return the same risk order, percentile classification, and strategy list as the original.
- `react-graph-vis` is unmaintained but vis-network itself is stable; swap for `vis-network` directly via vanilla JS integration if issues arise.
- CSV encoding is `utf-8-sig` — pandas handles this automatically.
