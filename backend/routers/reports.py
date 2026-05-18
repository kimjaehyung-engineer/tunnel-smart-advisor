from html import escape
from collections.abc import Sequence
from io import BytesIO
import json
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from ..services import comparison_report_store
from ..services import history_store
from ..services.notification_store import create_notification

router = APIRouter(prefix="/reports", tags=["reports"])


class ShareRequest(BaseModel):
    shared: bool


def as_int(value: object, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def as_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def report_title(item: dict[str, object]) -> str:
    query = str(item.get("query") or "자연어 없음")
    return f"터널 위험 분석 리포트 #{as_int(item.get('id'))} - {query}"


def comparison_report_title(item: dict[str, object]) -> str:
    return str(item.get("title") or f"설계변경 비교 리포트 #{as_int(item.get('id'))}")


def unique_strings(values: Sequence[object]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text != "nan" and text not in seen:
            seen.add(text)
            output.append(text)
    return output


def list_items(values: list[str], empty_text: str) -> str:
    if not values:
        return f"<li>{escape(empty_text)}</li>"
    return "".join(f"<li>{escape(value)}</li>" for value in values)


def collect_report_evidence(result: dict[str, object]) -> dict[str, list[str]]:
    risks = result.get("risks", [])
    graph = result.get("graph", {})
    nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    rationale: list[object] = []
    strategies: list[object] = []
    standards: list[object] = []
    roles: list[object] = []
    for risk in risks if isinstance(risks, list) else []:
        if not isinstance(risk, dict):
            continue
        strategies.extend(risk.get("strategies", []) if isinstance(risk.get("strategies"), list) else [])
        explanation = risk.get("score_explanation", {})
        if isinstance(explanation, dict):
            rationale.extend(explanation.get("rationale", []) if isinstance(explanation.get("rationale"), list) else [])
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        detail = node.get("detail", {})
        if isinstance(detail, dict):
            standards.extend(detail.get("standards", []) if isinstance(detail.get("standards"), list) else [])
            roles.extend(detail.get("roles", []) if isinstance(detail.get("roles"), list) else [])
    relation_summary = [
        f"{edge.get('from', '')} → {edge.get('to', '')} ({edge.get('title', '')})"
        for edge in edges[:12]
        if isinstance(edge, dict)
    ] if isinstance(edges, list) else []
    return {
        "rationale": unique_strings(rationale)[:10],
        "strategies": unique_strings(strategies)[:10],
        "standards": unique_strings(standards)[:10],
        "roles": unique_strings(roles)[:10],
        "relations": unique_strings(relation_summary)[:12],
    }


def to_report_item(item: dict[str, object], shared_ids: set[int] | None = None) -> dict[str, object]:
    report_id = as_int(item.get("id"))
    shared = report_id in shared_ids if shared_ids is not None else history_store.is_report_shared(report_id)
    result = item.get("result", {})
    data_version = item.get("data_version", {})
    model_version = str(item.get("model_version") or "unknown")
    if not data_version and isinstance(result, dict):
        data_version = result.get("data_version", {})
    if model_version == "unknown" and isinstance(result, dict):
        model_version = str(result.get("model_version") or "unknown")
    return {
        "id": report_id,
        "history_id": report_id,
        "title": report_title(item),
        "created_at": str(item["created_at"]),
        "top_risk": str(item.get("top_risk") or "매칭 위험 없음"),
        "total_risks": as_int(item.get("total_risks")),
        "critical_count": as_int(item.get("critical_count")),
        "max_score": as_float(item.get("max_score")),
        "format": "HTML",
        "download_url": f"/reports/{report_id}.html",
        "pdf_url": f"/reports/{report_id}.pdf",
        "package_url": f"/reports/{report_id}.zip",
        "shared": shared,
        "share_url": f"/reports/shared/{report_id}.html" if shared else "",
        "data_version": data_version,
        "model_version": model_version,
        "report_type": "analysis",
    }


def to_comparison_report_item(item: dict[str, object]) -> dict[str, object]:
    report_id = as_int(item.get("id"))
    result = item.get("result", {})
    before = result.get("before", {}) if isinstance(result, dict) else {}
    after = result.get("after", {}) if isinstance(result, dict) else {}
    total_risks = as_int(after.get("total_risks") if isinstance(after, dict) else 0)
    critical_count = as_int(after.get("critical_count") if isinstance(after, dict) else 0)
    max_score = as_float(after.get("max_score") if isinstance(after, dict) else 0.0)
    new_risks = result.get("new_risks", []) if isinstance(result, dict) else []
    increased_risks = result.get("increased_risks", []) if isinstance(result, dict) else []
    top_risk = "설계변경 비교"
    for risk_list in [new_risks, increased_risks]:
        if isinstance(risk_list, list) and risk_list and isinstance(risk_list[0], dict):
            top_risk = str(risk_list[0].get("description") or top_risk)
            break
    return {
        "id": f"comparison-{report_id}",
        "history_id": report_id,
        "title": comparison_report_title(item),
        "created_at": str(item["created_at"]),
        "top_risk": top_risk,
        "total_risks": total_risks,
        "critical_count": critical_count,
        "max_score": max_score,
        "format": "HTML",
        "download_url": f"/reports/compare/{report_id}.html",
        "pdf_url": f"/reports/compare/{report_id}.pdf",
        "package_url": f"/reports/compare/{report_id}.zip",
        "shared": False,
        "share_url": "",
        "data_version": item.get("data_version", {}),
        "model_version": str(item.get("model_version") or "unknown"),
        "report_type": "comparison",
    }


@router.get("")
def reports(query: str = "", limit: int = Query(default=50, ge=1, le=100)):
    shared_ids = history_store.shared_report_ids()
    analysis_items = [to_report_item(item, shared_ids) for item in history_store.list_analyses(query=query.strip(), limit=limit)]
    comparison_items = [to_comparison_report_item(item) for item in comparison_report_store.list_comparison_reports(query=query.strip(), limit=limit)]
    items = sorted(
        [*analysis_items, *comparison_items],
        key=lambda item: str(item.get("created_at", "")),
        reverse=True,
    )[:limit]
    return {
        "items": items,
        "summary": {
            "total": len(items),
            "shared": sum(1 for item in items if item["shared"]),
            "html": len(items),
        },
    }


def comparison_delta_rows(items: object, empty_text: str) -> str:
    if not isinstance(items, list) or not items:
        return f"<tr><td colspan='4'>{escape(empty_text)}</td></tr>"
    rows: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rows.append(
            f"<tr><td>{escape(str(item.get('description', '')))}</td>"
            f"<td>{escape(str(item.get('level', '')))}</td>"
            f"<td>{escape(str(item.get('score', '')))}</td>"
            f"<td>{escape(' / '.join(str(value) for value in item.get('matched', []) if value) if isinstance(item.get('matched'), list) else '')}</td></tr>"
        )
    return "".join(rows) if rows else f"<tr><td colspan='4'>{escape(empty_text)}</td></tr>"


def filters_table(filters: object) -> str:
    if not isinstance(filters, dict):
        return "<tr><td colspan='2'>조건 정보가 없습니다.</td></tr>"
    return "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(str(value or '-'))}</td></tr>"
        for key, value in filters.items()
    )


@router.get("/compare/{report_id}.html", response_class=HTMLResponse)
def comparison_report_html(report_id: int):
    report = comparison_report_store.get_comparison_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Comparison report not found")
    result = report.get("result", {})
    before_summary = result.get("before", {}) if isinstance(result, dict) else {}
    after_summary = result.get("after", {}) if isinstance(result, dict) else {}
    data_version = report.get("data_version", {})
    source_file = data_version.get("source_file", "unknown") if isinstance(data_version, dict) else "unknown"
    source_hash = data_version.get("source_file_hash", "unknown") if isinstance(data_version, dict) else "unknown"
    title = escape(comparison_report_title(report))
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="ko">
        <head>
          <meta charset="utf-8" />
          <title>{title}</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #0f172a; }}
            h1 {{ font-size: 24px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 18px 0; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; }}
            th {{ background: #f8fafc; }}
            .summary {{ display: flex; gap: 12px; margin: 20px 0; }}
            .metric {{ border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px 16px; }}
          </style>
        </head>
        <body>
          <h1>{title}</h1>
          <p>작성일: {escape(str(report.get('created_at', '')))}</p>
          <p>데이터 버전: {escape(str(source_file))} / {escape(str(source_hash)[:12])}</p>
          <p>모델 버전: {escape(str(report.get('model_version', 'unknown')))}</p>
          <div class="summary">
            <div class="metric">변경 전 위험: {escape(str(before_summary.get('total_risks', 0) if isinstance(before_summary, dict) else 0))}건</div>
            <div class="metric">변경 후 위험: {escape(str(after_summary.get('total_risks', 0) if isinstance(after_summary, dict) else 0))}건</div>
            <div class="metric">신규 위험: {escape(str(len(result.get('new_risks', [])) if isinstance(result, dict) and isinstance(result.get('new_risks'), list) else 0))}건</div>
          </div>
          <h2>변경 전 조건</h2>
          <table><tbody>{filters_table(report.get('before'))}</tbody></table>
          <h2>변경 후 조건</h2>
          <table><tbody>{filters_table(report.get('after'))}</tbody></table>
          <h2>신규 발생 가능 리스크</h2>
          <table><thead><tr><th>위험</th><th>등급</th><th>점수</th><th>매칭 조건</th></tr></thead><tbody>{comparison_delta_rows(result.get('new_risks') if isinstance(result, dict) else [], '신규 리스크가 없습니다.')}</tbody></table>
          <h2>감소 또는 제거된 리스크</h2>
          <table><thead><tr><th>위험</th><th>등급</th><th>점수</th><th>매칭 조건</th></tr></thead><tbody>{comparison_delta_rows(result.get('removed_risks') if isinstance(result, dict) else [], '감소/제거 리스크가 없습니다.')}</tbody></table>
          <h2>위험등급 상승 리스크</h2>
          <table><thead><tr><th>위험</th><th>등급</th><th>점수</th><th>매칭 조건</th></tr></thead><tbody>{comparison_delta_rows(result.get('increased_risks') if isinstance(result, dict) else [], '상승 리스크가 없습니다.')}</tbody></table>
          <h2>위험등급 하락 리스크</h2>
          <table><thead><tr><th>위험</th><th>등급</th><th>점수</th><th>매칭 조건</th></tr></thead><tbody>{comparison_delta_rows(result.get('decreased_risks') if isinstance(result, dict) else [], '하락 리스크가 없습니다.')}</tbody></table>
          <h2>추가 대응전략</h2>
          <ul>{list_items(result.get('additional_strategies', []) if isinstance(result, dict) and isinstance(result.get('additional_strategies'), list) else [], '추가 대응전략이 없습니다.')}</ul>
          <h2>관련 기준 근거</h2>
          <ul>{list_items(result.get('related_standards', []) if isinstance(result, dict) and isinstance(result.get('related_standards'), list) else [], '관련 기준 근거가 없습니다.')}</ul>
        </body>
        </html>
        """
    )


@router.get("/compare/{report_id}.pdf")
def comparison_report_pdf(report_id: int):
    report = comparison_report_store.get_comparison_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Comparison report not found")
    result = report.get("result", {})
    before_summary = result.get("before", {}) if isinstance(result, dict) else {}
    after_summary = result.get("after", {}) if isinstance(result, dict) else {}
    lines = [
        f"Tunnel Design Change Report #{report_id}",
        f"Created: {report.get('created_at', '')}",
        f"Model version: {report.get('model_version', 'unknown')}",
        f"Before risks: {before_summary.get('total_risks', 0) if isinstance(before_summary, dict) else 0}",
        f"After risks: {after_summary.get('total_risks', 0) if isinstance(after_summary, dict) else 0}",
        "New risks:",
    ]
    new_risks = result.get("new_risks", []) if isinstance(result, dict) else []
    for risk in new_risks[:20] if isinstance(new_risks, list) else []:
        if isinstance(risk, dict):
            lines.append(f"- {risk.get('description', '')} | score={risk.get('score', '')} | level={risk.get('level', '')}")
    lines.extend(["Strategies:", *[f"- {item}" for item in result.get("additional_strategies", [])[:8]]] if isinstance(result, dict) and isinstance(result.get("additional_strategies"), list) else ["Strategies:"])
    lines.extend(["Standards:", *[f"- {item}" for item in result.get("related_standards", [])[:8]]] if isinstance(result, dict) and isinstance(result.get("related_standards"), list) else ["Standards:"])
    return Response(
        content=build_pdf(lines),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="tunnel-comparison-report-{report_id}.pdf"'},
    )


@router.get("/compare/{report_id}.zip")
def comparison_report_package(report_id: int):
    report = comparison_report_store.get_comparison_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Comparison report not found")
    html = comparison_report_html(report_id).body
    pdf = comparison_report_pdf(report_id).body
    metadata = {
        "report_type": "comparison",
        "id": report_id,
        "title": comparison_report_title(report),
        "created_at": report.get("created_at"),
        "before": report.get("before"),
        "after": report.get("after"),
        "data_version": report.get("data_version"),
        "model_version": report.get("model_version"),
    }
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(f"tunnel-comparison-report-{report_id}.html", html)
        archive.writestr(f"tunnel-comparison-report-{report_id}.pdf", pdf)
        archive.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="tunnel-comparison-report-package-{report_id}.zip"'},
    )


@router.post("/{history_id}/share")
def update_report_share(history_id: int, request: ShareRequest):
    analysis = history_store.get_analysis(history_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Report source analysis not found")
    history_store.set_report_shared(history_id, request.shared)
    create_notification(
        "report",
        "리포트 공유 상태 변경",
        f"리포트 #{history_id} 공유 상태가 {'공유' if request.shared else '공유 해제'}로 변경되었습니다.",
    )
    return to_report_item(analysis)


@router.get("/shared/{history_id}.html", response_class=HTMLResponse)
def shared_report_html(history_id: int):
    if not history_store.is_report_shared(history_id):
        raise HTTPException(status_code=404, detail="Shared report link is not active")
    return report_html(history_id)


@router.get("/{history_id}.html", response_class=HTMLResponse)
def report_html(history_id: int):
    analysis = history_store.get_analysis(history_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Report source analysis not found")

    result = analysis.get("result", {})
    risks = result.get("risks", []) if isinstance(result, dict) else []
    evidence = collect_report_evidence(result) if isinstance(result, dict) else {"rationale": [], "strategies": [], "standards": [], "roles": [], "relations": []}
    data_version = result.get("data_version", {}) if isinstance(result, dict) else {}
    model_version = result.get("model_version", "unknown") if isinstance(result, dict) else "unknown"
    banding_method = result.get("banding_method", "unknown") if isinstance(result, dict) else "unknown"
    banding_model_version = result.get("banding_model_version", "unknown") if isinstance(result, dict) else "unknown"
    band_fallback_reason = result.get("band_fallback_reason", "") if isinstance(result, dict) else ""
    band_boundaries = result.get("band_boundaries", []) if isinstance(result, dict) else []
    source_file = data_version.get("source_file", "unknown") if isinstance(data_version, dict) else "unknown"
    source_hash = data_version.get("source_file_hash", "unknown") if isinstance(data_version, dict) else "unknown"
    build_at = data_version.get("ontology_build_at", "unknown") if isinstance(data_version, dict) else "unknown"
    risk_rows = "".join(
        f"<tr><td>{escape(str(risk.get('description', '')))}</td>"
        f"<td>{escape(str(risk.get('level', '')))}</td>"
        f"<td>{escape(str(risk.get('cluster_label') or risk.get('cluster_band', '-')))}</td>"
        f"<td>{escape(str(risk.get('score', '')))}</td></tr>"
        for risk in risks
        if isinstance(risk, dict)
    )
    if not risk_rows:
        risk_rows = "<tr><td colspan='4'>매칭된 위험이 없습니다.</td></tr>"

    boundary_items = [
        f"{boundary.get('from_band')} → {boundary.get('to_band')}: gap {boundary.get('gap')}"
        for boundary in band_boundaries
        if isinstance(boundary, dict)
    ] if isinstance(band_boundaries, list) else []

    filters = analysis.get("filters", {})
    filter_rows = "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(str(value or '-'))}</td></tr>"
        for key, value in filters.items()
    ) if isinstance(filters, dict) else ""

    title = escape(report_title(analysis))
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="ko">
        <head>
          <meta charset="utf-8" />
          <title>{title}</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #0f172a; }}
            h1 {{ font-size: 24px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 18px 0; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; }}
            th {{ background: #f8fafc; }}
            .summary {{ display: flex; gap: 12px; margin: 20px 0; }}
            .metric {{ border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px 16px; }}
          </style>
        </head>
        <body>
          <h1>{title}</h1>
          <p>작성일: {escape(str(analysis['created_at']))}</p>
          <p>검색어: {escape(str(analysis.get('query') or '자연어 없음'))}</p>
          <p>데이터 버전: {escape(str(source_file))} / {escape(str(source_hash)[:12])} / {escape(str(build_at))}</p>
          <p>모델 버전: {escape(str(model_version))}</p>
          <p>위험군 모델: {escape(str(banding_model_version))} / {escape(str(banding_method))} / {escape(str(band_fallback_reason or 'material_gaps'))}</p>
          <div class="summary">
            <div class="metric">총 위험: {escape(str(analysis.get('total_risks', 0)))}건</div>
            <div class="metric">Critical: {escape(str(analysis.get('critical_count', 0)))}건</div>
            <div class="metric">최고 점수: {escape(str(analysis.get('max_score', 0.0)))}</div>
          </div>
          <h2>분석 조건</h2>
          <table><tbody>{filter_rows}</tbody></table>
          <h2>주요 위험</h2>
          <table><thead><tr><th>위험</th><th>등급</th><th>위험군</th><th>점수</th></tr></thead><tbody>{risk_rows}</tbody></table>
          <h2>위험군 경계</h2>
          <ul>{list_items(boundary_items, '단일 위험군 또는 유의미한 점수 격차가 없습니다.')}</ul>
          <h2>점수 산정 근거</h2>
          <ul>{list_items(evidence['rationale'], '점수 산정 근거가 없습니다.')}</ul>
          <h2>대응전략</h2>
          <ul>{list_items(evidence['strategies'], '연결된 대응전략이 없습니다.')}</ul>
          <h2>관계 요약</h2>
          <ul>{list_items(evidence['relations'], '관계 요약이 없습니다.')}</ul>
          <h2>관련 기준 조항</h2>
          <ul>{list_items(evidence['standards'], '연결된 기준 근거가 없습니다.')}</ul>
          <h2>담당 주체</h2>
          <ul>{list_items(evidence['roles'], '연결된 담당 주체가 없습니다.')}</ul>
        </body>
        </html>
        """
    )


def pdf_escape(text: str) -> str:
    safe = text.encode("latin-1", errors="replace").decode("latin-1")
    return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 16 Tf", "50 790 Td", "18 TL"]
    for index, line in enumerate(lines[:80]):
        size = 16 if index == 0 else 10
        content_lines.append(f"/F1 {size} Tf")
        content_lines.append(f"({pdf_escape(line)}) Tj")
        content_lines.append("T*")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)


@router.get("/{history_id}.pdf")
def report_pdf(history_id: int):
    analysis = history_store.get_analysis(history_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Report source analysis not found")
    result = analysis.get("result", {})
    risks = result.get("risks", []) if isinstance(result, dict) else []
    evidence = collect_report_evidence(result) if isinstance(result, dict) else {"rationale": [], "strategies": [], "standards": [], "roles": [], "relations": []}
    data_version = result.get("data_version", {}) if isinstance(result, dict) else {}
    model_version = result.get("model_version", "unknown") if isinstance(result, dict) else "unknown"
    banding_method = result.get("banding_method", "unknown") if isinstance(result, dict) else "unknown"
    banding_model_version = result.get("banding_model_version", "unknown") if isinstance(result, dict) else "unknown"
    source_file = data_version.get("source_file", "unknown") if isinstance(data_version, dict) else "unknown"
    source_hash = data_version.get("source_file_hash", "unknown") if isinstance(data_version, dict) else "unknown"
    lines = [
        f"Tunnel Smart Advisor Report #{history_id}",
        f"Created from analysis: {analysis['created_at']}",
        f"Data version: {source_file} / {str(source_hash)[:12]}",
        f"Model version: {model_version}",
        f"Banding model: {banding_model_version} / {banding_method}",
        f"Query: {analysis.get('query') or 'No natural-language query'}",
        f"Total risks: {analysis.get('total_risks', 0)}",
        f"Critical risks: {analysis.get('critical_count', 0)}",
        f"Max score: {analysis.get('max_score', 0.0)}",
        "",
        "Top risks:",
    ]
    for risk in risks[:20]:
        if isinstance(risk, dict):
            lines.append(f"- {risk.get('description', '')} | score={risk.get('score', '')} | level={risk.get('level', '')} | band={risk.get('cluster_band', '-')}")
    if len(lines) == 8:
        lines.append("- No matched risks")
    lines.extend([
        "",
        "Score rationale:",
        *[f"- {item}" for item in evidence["rationale"][:4]],
        "Strategies:",
        *[f"- {item}" for item in evidence["strategies"][:4]],
        "Relationship summary:",
        *[f"- {item}" for item in evidence["relations"][:4]],
        "Standards:",
        *[f"- {item}" for item in evidence["standards"][:4]],
        "Roles:",
        *[f"- {item}" for item in evidence["roles"][:4]],
    ])
    return Response(
        content=build_pdf(lines),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="tunnel-report-{history_id}.pdf"'},
    )


@router.get("/{history_id}.zip")
def report_package(history_id: int):
    analysis = history_store.get_analysis(history_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Report source analysis not found")

    html = report_html(history_id).body
    pdf = report_pdf(history_id).body
    metadata = {
        "history_id": history_id,
        "title": report_title(analysis),
        "created_at": analysis.get("created_at"),
        "query": analysis.get("query"),
        "filters": analysis.get("filters"),
        "total_risks": analysis.get("total_risks"),
        "critical_count": analysis.get("critical_count"),
        "max_score": analysis.get("max_score"),
        "data_version": analysis.get("data_version"),
        "model_version": analysis.get("model_version"),
    }

    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(f"tunnel-report-{history_id}.html", html)
        archive.writestr(f"tunnel-report-{history_id}.pdf", pdf)
        archive.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="tunnel-report-package-{history_id}.zip"'},
    )
