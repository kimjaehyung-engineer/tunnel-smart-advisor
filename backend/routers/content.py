from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from ..services.data_loader import load_data
from ..services.history_store import shared_report_ids
from ..services.metrics import metrics
from ..services.ontology_version import load_ontology_version
from ..services.risk_scoring import natural_sort_key

router = APIRouter(tags=["content"])


def safe_str(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    return "" if text == "nan" else text


def safe_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def list_contains(values: object, target: str) -> bool:
    return isinstance(values, list) and any(str(value) == target for value in values)


def id_name_lookup() -> dict[str, str]:
    data = load_data()
    lookups = [
        ("process", "name"),
        ("ground", "condition_name"),
        ("location", "loc_name"),
        ("method", "method_name"),
        ("equipment", "equip_name"),
        ("strategy", "action"),
        ("risk", "description"),
        ("lesson", "content"),
    ]
    names: dict[str, str] = {}
    for key, name_col in lookups:
        for _, row in data[key].iterrows():
            node_id = safe_str(row.get("id:ID"))
            node_name = safe_str(row.get(name_col))
            if node_id and node_name:
                names[node_id] = node_name
    return names


def relation_counts_by_risk() -> Counter[str]:
    rels = load_data()["rels"]
    counts: Counter[str] = Counter()
    for _, row in rels.iterrows():
        end_id = safe_str(row.get(":END_ID"))
        start_id = safe_str(row.get(":START_ID"))
        if end_id.startswith("Risk_"):
            counts[end_id] += 1
        if start_id.startswith("Risk_"):
            counts[start_id] += 1
    return counts


def impact_distribution() -> list[dict[str, int | str]]:
    data = load_data()
    rels = data["rels"]
    impacts = data["impact"]
    impact_names = {
        safe_str(row.get("id:ID")): safe_str(row.get("impact_type"))
        for _, row in impacts.iterrows()
    }
    counts: Counter[str] = Counter()
    for _, row in rels[rels[":TYPE"] == "AFFECTS"].iterrows():
        impact_id = safe_str(row.get(":END_ID"))
        label = impact_names.get(impact_id)
        if label:
            counts[label] += 1
    colors = ["#EF4444", "#F97316", "#F59E0B", "#3B82F6", "#10B981", "#8B5CF6"]
    return [
        {"label": label, "value": count, "color": colors[index % len(colors)]}
        for index, (label, count) in enumerate(counts.most_common(6))
    ]


def lookup_values(frame, ids: list[str], id_column: str, value_column: str) -> list[dict[str, str]]:
    if not ids or value_column not in frame.columns:
        return []
    values: list[dict[str, str]] = []
    for node_id in ids:
        matches = frame[frame[id_column] == node_id]
        if matches.empty:
            continue
        label = safe_str(matches.iloc[0].get(value_column))
        if label:
            values.append({"id": node_id, "label": label})
    return values


def lookup_labels(frame, ids: list[str], id_column: str, value_column: str) -> list[str]:
    return [item["label"] for item in lookup_values(frame, ids, id_column, value_column)]


def related_ids(rels, node_id: str, rel_type: str, *, direction: str = "out") -> list[str]:
    if direction == "in":
        matches = rels[(rels[":END_ID"] == node_id) & (rels[":TYPE"] == rel_type)]
        return [safe_str(value) for value in matches[":START_ID"].tolist()]
    matches = rels[(rels[":START_ID"] == node_id) & (rels[":TYPE"] == rel_type)]
    return [safe_str(value) for value in matches[":END_ID"].tolist()]


def risk_id_aliases(risk_id: str) -> list[str]:
    aliases = [risk_id]
    prefix = "Risk_"
    if risk_id.startswith(prefix):
        suffix = risk_id.removeprefix(prefix)
        if suffix.isdigit():
            aliases.append(f"{prefix}{int(suffix)}")
            aliases.append(f"{prefix}{int(suffix):03d}")
    return list(dict.fromkeys(aliases))


def related_lesson_ids(data: Mapping[str, pd.DataFrame], risk_id: str) -> list[str]:
    lesson_rels = data.get("lesson_rels")
    if lesson_rels is None:
        return []
    risk_aliases = risk_id_aliases(risk_id)
    matches = lesson_rels[
        (lesson_rels[":START_ID"].isin(risk_aliases))
        & (lesson_rels[":TYPE"] == "LEARNED_AS")
    ]
    return [safe_str(value) for value in matches[":END_ID"].tolist()]


def graph_node(node_id: str, label: str, title: str, color: str, size: int = 18) -> dict[str, object]:
    return {"id": node_id, "label": label, "title": title, "color": color, "size": size}


def graph_edges(from_id: str, to_items: list[dict[str, str]], relation: str, color: str) -> list[dict[str, object]]:
    return [
        {"from": from_id, "to": item["id"], "title": relation, "color": color}
        for item in to_items
    ]


def build_library_detail_graph(
    risk_id: str,
    title: str,
    related_conditions: dict[str, list[dict[str, str]]],
    strategies: list[dict[str, str]],
    impacts: list[dict[str, str]],
    standards: list[dict[str, str]],
    roles: list[dict[str, str]],
    lessons: list[dict[str, str]],
) -> dict[str, list[dict[str, object]]]:
    nodes = [graph_node(risk_id, "Risk", title, "#EF4444", 28)]
    edges: list[dict[str, object]] = []
    condition_labels = {
        "process": "Process",
        "ground": "Ground",
        "location": "Location",
        "method": "Method",
        "equipment": "Equipment",
    }
    for condition_type, items in related_conditions.items():
        if condition_type == "impact":
            continue
        for item in items:
            nodes.append(graph_node(item["id"], condition_labels.get(condition_type, "Condition"), item["label"], "#3B82F6"))
            edges.append({"from": item["id"], "to": risk_id, "title": condition_type.upper(), "color": "#93C5FD"})

    for item in strategies:
        nodes.append(graph_node(item["id"], "Strategy", item["label"], "#10B981"))
    for item in impacts:
        nodes.append(graph_node(item["id"], "Impact", item["label"], "#F97316"))
    for item in standards:
        nodes.append(graph_node(item["id"], "Standard", item["label"], "#8B5CF6"))
    for item in roles:
        nodes.append(graph_node(item["id"], "Role", item["label"], "#0EA5E9"))
    for item in lessons:
        nodes.append(graph_node(item["id"], "LessonLearned", item["label"], "#F59E0B"))

    edges.extend(graph_edges(risk_id, strategies, "MITIGATED_BY", "#6EE7B7"))
    edges.extend(graph_edges(risk_id, impacts, "AFFECTS", "#FDBA74"))
    edges.extend(graph_edges(risk_id, lessons, "LEARNED_AS", "#FCD34D"))
    for strategy in strategies:
        edges.extend(graph_edges(strategy["id"], standards, "BASED_ON", "#C4B5FD"))
        edges.extend(graph_edges(strategy["id"], roles, "ASSIGNED_TO", "#7DD3FC"))

    unique_nodes = list({str(node["id"]): node for node in nodes}.values())
    return {"nodes": unique_nodes, "edges": edges}


def age_days(iso_timestamp: str) -> int | None:
    if not iso_timestamp or iso_timestamp == "missing":
        return None
    try:
        timestamp = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)
    return max(0, delta.days)


def build_operational_status(total_risks: int, critical_count: int) -> list[dict[str, str]]:
    version = load_ontology_version()
    source_age = age_days(version.get("source_file_mtime", ""))
    build_age = age_days(version.get("ontology_build_at", ""))
    metrics_snapshot = metrics.snapshot()
    error_count = safe_int(metrics_snapshot.get("error_count", 0))
    data_failures = safe_int(metrics_snapshot.get("data_load_failure_count", 0))
    shared_count = len(shared_report_ids())

    data_value = "원천 확인 필요" if source_age is None else f"{source_age}일 전"
    build_value = "빌드 확인 필요" if build_age is None else f"{build_age}일 전"
    error_value = "정상" if error_count == 0 and data_failures == 0 else f"오류 {error_count}건 / 데이터 실패 {data_failures}건"
    error_status = "ok" if error_count == 0 and data_failures == 0 else "warning"
    error_color = "#10B981" if error_status == "ok" else "#F59E0B"

    return [
        {
            "label": "총 리스크 수",
            "value": f"{total_risks}건",
            "status": "ok",
            "description": "현재 온톨로지 Risk 노드 기준",
            "color": "#3B82F6",
        },
        {
            "label": "최상위 위험 수",
            "value": f"{critical_count}건",
            "status": "watch" if critical_count else "ok",
            "description": "대시보드 연결도 기준 상위 위험 후보",
            "color": "#EF4444" if critical_count else "#10B981",
        },
        {
            "label": "데이터 최신성",
            "value": data_value,
            "status": "unknown" if source_age is None else "ok",
            "description": f"원천 파일: {version.get('source_file', 'unknown')}",
            "color": "#8B5CF6",
        },
        {
            "label": "최근 데이터 업데이트",
            "value": build_value,
            "status": "unknown" if build_age is None else "ok",
            "description": "ontology_build_at 기준",
            "color": "#0EA5E9",
        },
        {
            "label": "시스템 오류 상태",
            "value": error_value,
            "status": error_status,
            "description": f"누적 요청 {metrics_snapshot.get('request_count', 0)}건 기준",
            "color": error_color,
        },
        {
            "label": "리포트 공유 현황",
            "value": f"{shared_count}건",
            "status": "ok",
            "description": "공유 상태가 켜진 리포트 수",
            "color": "#10B981",
        },
    ]


@router.get("/dashboard/summary")
def dashboard_summary():
    data = load_data()
    risks = data["risk"]
    strategies = data["strategy"]
    rels = data["rels"]
    degree_counts = relation_counts_by_risk()

    risk_summaries: list[dict[str, str | int]] = []
    for _, row in risks.iterrows():
        risk_id = safe_str(row.get("id:ID"))
        risk_summaries.append({
            "id": risk_id,
            "title": safe_str(row.get("description")),
            "project": safe_str(row.get("source_project")),
            "score": degree_counts.get(risk_id, 0),
        })

    sorted_risks = sorted(
        risk_summaries,
        key=lambda item: (-safe_int(item["score"]), natural_sort_key(str(item["title"]))),
    )

    total = len(sorted_risks)
    high = max(1, int(total * 0.2)) if total else 0
    medium = max(1, int(total * 0.3)) if total else 0
    low = max(0, total - high - medium)

    project_count = int(risks["source_project"].nunique()) if "source_project" in risks else 0
    relation_count = len(rels)
    impact_items = impact_distribution()
    operational_status = build_operational_status(total, high)

    notifications = [
        {
            "title": "위험 지식 데이터가 로드되었습니다.",
            "desc": f"위험 {total}건, 대응전략 {len(strategies)}건을 백엔드 CSV에서 불러왔습니다.",
            "time": "실시간",
            "color": "#3B82F6",
        },
        {
            "title": "관계 그래프 데이터가 준비되었습니다.",
            "desc": f"총 {relation_count}개의 온톨로지 관계를 분석에 활용합니다.",
            "time": "실시간",
            "color": "#10B981",
        },
    ]

    return {
        "kpis": [
            {"label": "전체 위험 지식", "value": f"{total}건", "subValue": f"프로젝트 {project_count}개", "accentColor": "#3B82F6"},
            {"label": "상위 연결 위험", "value": f"{high}건", "subValue": "관계 수 기준", "accentColor": "#EF4444"},
            {"label": "중간 연결 위험", "value": f"{medium}건", "subValue": "관계 수 기준", "accentColor": "#F59E0B"},
            {"label": "대응전략", "value": f"{len(strategies)}건", "subValue": "MITIGATED_BY", "accentColor": "#10B981"},
            {"label": "영향 유형", "value": f"{len(impact_items)}종", "subValue": "AFFECTS", "accentColor": "#8B5CF6"},
        ],
        "distribution": [
            {"label": "상위 연결", "value": high, "color": "#EF4444"},
            {"label": "중간 연결", "value": medium, "color": "#F59E0B"},
            {"label": "기타", "value": low, "color": "#10B981"},
        ],
        "trend": [item["score"] for item in sorted_risks[:6]],
        "impactDistribution": impact_items,
        "operationalStatus": operational_status,
        "recentAnalyses": sorted_risks[:5],
        "notifications": notifications,
    }


@router.get("/library/items")
def library_items(
    query: str = Query(default="", max_length=200),
    category: str = Query(default="전체", max_length=80),
    tag: str = Query(default="전체", max_length=120),
    relation_type: str = Query(default="전체", max_length=80),
):
    data = load_data()
    risks = data["risk"]
    rels = data["rels"]
    names = id_name_lookup()
    degree_counts = relation_counts_by_risk()

    categories: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    relation_counts: Counter[str] = Counter()
    items: list[dict[str, object]] = []

    for _, row in risks.iterrows():
        risk_id = safe_str(row.get("id:ID"))
        related_rows = rels[rels[":END_ID"] == risk_id]
        outgoing_rows = rels[rels[":START_ID"] == risk_id]
        lesson_ids = related_lesson_ids(data, risk_id)
        tags: list[str] = []
        relation_types: list[str] = []
        category = "위험"

        for _, rel in related_rows.iterrows():
            start_id = safe_str(rel.get(":START_ID"))
            rel_type = safe_str(rel.get(":TYPE"))
            if rel_type:
                relation_types.append(rel_type)
            if start_id and start_id in names:
                tags.append(names[start_id])
            if rel_type == "ENCOUNTERS":
                category = "공종"
            elif rel_type == "TRIGGER" and category == "위험":
                category = "지반"
            elif rel_type == "OCCURS_AT" and category == "위험":
                category = "위치"
            elif rel_type == "ASSOCIATED_WITH" and category == "위험":
                category = "공법"

        for _, rel in outgoing_rows.iterrows():
            rel_type = safe_str(rel.get(":TYPE"))
            end_id = safe_str(rel.get(":END_ID"))
            if rel_type:
                relation_types.append(rel_type)
            if end_id and end_id in names:
                tags.append(names[end_id])

        if lesson_ids:
            relation_types.append("LEARNED_AS")
            tags.extend(lookup_labels(data["lesson"], lesson_ids, "id:ID", "content"))

        unique_tags = sorted(set(tags), key=natural_sort_key)[:5]
        unique_relation_types = sorted(set(relation_types), key=natural_sort_key)
        for tag_label in unique_tags:
            tag_counts[tag_label] += 1
        for rel_type in unique_relation_types:
            relation_counts[rel_type] += 1
        categories[category] += 1

        strategy_ids = related_ids(rels, risk_id, "MITIGATED_BY")
        impact_ids = related_ids(rels, risk_id, "AFFECTS")
        standard_ids: list[str] = []
        role_ids: list[str] = []
        for strategy_id in strategy_ids:
            standard_ids.extend(related_ids(rels, strategy_id, "BASED_ON"))
            role_ids.extend(related_ids(rels, strategy_id, "ASSIGNED_TO"))
        strategy_labels = lookup_labels(data["strategy"], strategy_ids, "id:ID", "action")
        standard_labels = lookup_labels(data["standard"], standard_ids, "id:ID", "doc_name")
        role_labels = lookup_labels(data["role"], role_ids, "id:ID", "role_name")
        impact_labels = lookup_labels(data["impact"], impact_ids, "id:ID", "impact_type")
        search_text = " ".join([
            safe_str(row.get("description")),
            safe_str(row.get("source_project")),
            safe_str(row.get("source_ll")),
            safe_str(row.get("cause")),
            safe_str(row.get("impact_text")),
            safe_str(row.get("impact")),
            *unique_tags,
            *unique_relation_types,
            *strategy_labels,
            *standard_labels,
            *role_labels,
            *impact_labels,
            *lookup_labels(data["lesson"], lesson_ids, "id:ID", "content"),
        ]).lower()

        items.append({
            "id": risk_id,
            "title": safe_str(row.get("description")),
            "category": category,
            "tags": unique_tags,
            "relationTypes": unique_relation_types,
            "project": safe_str(row.get("source_project")),
            "relationCount": degree_counts.get(risk_id, 0),
            "searchText": search_text,
        })

    keyword = query.strip().lower()
    selected_category = category.strip() or "전체"
    selected_tag = tag.strip() or "전체"
    selected_relation_type = relation_type.strip() or "전체"
    filtered_items = [
        item for item in items
        if (
            not keyword
            or keyword in str(item["searchText"])
        )
        and (selected_category == "전체" or item["category"] == selected_category)
        and (selected_tag == "전체" or list_contains(item["tags"], selected_tag))
        and (selected_relation_type == "전체" or list_contains(item["relationTypes"], selected_relation_type))
    ]

    for item in filtered_items:
        item.pop("searchText", None)

    filtered_items = sorted(filtered_items, key=lambda item: (-safe_int(item["relationCount"]), natural_sort_key(str(item["title"]))))

    return {
        "items": filtered_items,
        "categories": [{"label": "전체", "count": len(items)}] + [
            {"label": label, "count": count}
            for label, count in sorted(categories.items(), key=lambda pair: natural_sort_key(pair[0]))
        ],
        "popularTags": [
            {"label": label, "count": count}
            for label, count in tag_counts.most_common(10)
        ],
        "relationTypes": [{"label": "전체", "count": len(items)}] + [
            {"label": label, "count": count}
            for label, count in sorted(relation_counts.items(), key=lambda pair: natural_sort_key(pair[0]))
        ],
        "filters": {"query": query, "category": selected_category, "tag": selected_tag, "relation_type": selected_relation_type},
    }


@router.get("/library/items/{risk_id}")
def library_item_detail(risk_id: str):
    data = load_data()
    risks = data["risk"]
    rels = data["rels"]
    risk_rows = risks[risks["id:ID"] == risk_id]
    if risk_rows.empty:
        raise HTTPException(status_code=404, detail="Library item not found")

    risk_row = risk_rows.iloc[0]
    process_ids = related_ids(rels, risk_id, "ENCOUNTERS", direction="in")
    ground_ids = related_ids(rels, risk_id, "TRIGGER", direction="in")
    location_ids = related_ids(rels, risk_id, "OCCURS_AT", direction="in")
    method_ids = related_ids(rels, risk_id, "ASSOCIATED_WITH", direction="in")
    equipment_ids = related_ids(rels, risk_id, "USES_EQUIPMENT", direction="in")
    strategy_ids = related_ids(rels, risk_id, "MITIGATED_BY")
    impact_ids = related_ids(rels, risk_id, "AFFECTS")
    lesson_ids = related_lesson_ids(data, risk_id)

    role_ids: list[str] = []
    standard_ids: list[str] = []
    for strategy_id in strategy_ids:
        role_ids.extend(related_ids(rels, strategy_id, "ASSIGNED_TO"))
        standard_ids.extend(related_ids(rels, strategy_id, "BASED_ON"))

    def unique(ids: list[str]) -> list[str]:
        return list(dict.fromkeys([node_id for node_id in ids if node_id]))

    related_conditions = {
        "process": lookup_values(data["process"], unique(process_ids), "id:ID", "name"),
        "ground": lookup_values(data["ground"], unique(ground_ids), "id:ID", "condition_name"),
        "location": lookup_values(data["location"], unique(location_ids), "id:ID", "loc_name"),
        "method": lookup_values(data["method"], unique(method_ids), "id:ID", "method_name"),
        "equipment": lookup_values(data["equipment"], unique(equipment_ids), "id:ID", "equip_name"),
        "impact": lookup_values(data["impact"], unique(impact_ids), "id:ID", "impact_type"),
    }
    strategies = lookup_values(data["strategy"], unique(strategy_ids), "id:ID", "action")
    impacts = lookup_values(data["impact"], unique(impact_ids), "id:ID", "impact_type")
    roles = lookup_values(data["role"], unique(role_ids), "id:ID", "role_name")
    standards = lookup_values(data["standard"], unique(standard_ids), "id:ID", "doc_name")
    lessons = lookup_values(data["lesson"], unique(lesson_ids), "id:ID", "content")
    title = safe_str(risk_row.get("description"))

    return {
        "id": risk_id,
        "title": title,
        "project": safe_str(risk_row.get("source_project")),
        "sourceVersion": safe_str(risk_row.get("source_version")),
        "sourceLL": safe_str(risk_row.get("source_ll")),
        "cause": safe_str(risk_row.get("cause")),
        "impactText": safe_str(risk_row.get("impact_text")),
        "relationCount": relation_counts_by_risk().get(risk_id, 0),
        "relatedConditions": related_conditions,
        "strategies": strategies,
        "impacts": impacts,
        "roles": roles,
        "standards": standards,
        "lessons": lessons,
        "graph": build_library_detail_graph(risk_id, title, related_conditions, strategies, impacts, standards, roles, lessons),
    }
