from pathlib import Path
from io import BytesIO
import json
from zipfile import ZipFile

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import comparison_report_store, history_store, notification_store
from backend.services.risk_scoring import MODEL_VERSION


client = TestClient(app)


def use_temp_history_db(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr(history_store, "DB_PATH", db_path)
    monkeypatch.setattr(notification_store, "DB_PATH", db_path)
    history_store.init_history_store()
    comparison_report_store.init_comparison_report_store()
    notification_store.init_notification_store()


def test_reports_list_uses_saved_analysis_history(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)
    score_response = client.post("/score/", json={"query": "지하수"})
    history_id = score_response.json()["history_id"]

    response = client.get("/reports")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total"] == 1
    assert body["items"][0]["history_id"] == history_id
    assert body["items"][0]["format"] == "HTML"
    assert body["items"][0]["data_version"]["source_file"]
    assert body["items"][0]["model_version"] == MODEL_VERSION
    assert body["items"][0]["download_url"] == f"/reports/{history_id}.html"
    assert body["items"][0]["pdf_url"] == f"/reports/{history_id}.pdf"
    assert body["items"][0]["package_url"] == f"/reports/{history_id}.zip"


def test_report_html_download_returns_saved_snapshot(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)
    score_response = client.post("/score/", json={"query": "파쇄대"})
    history_id = score_response.json()["history_id"]

    response = client.get(f"/reports/{history_id}.html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "터널 위험 분석 리포트" in response.text
    assert "파쇄대" in response.text
    assert "데이터 버전" in response.text
    assert "모델 버전" in response.text
    assert "위험군 모델" in response.text
    assert "위험군 경계" in response.text
    assert MODEL_VERSION in response.text
    assert "점수 산정 근거" in response.text
    assert "대응전략" in response.text
    assert "관계 요약" in response.text
    assert "관련 기준 조항" in response.text
    assert "담당 주체" in response.text
    assert "작성일" in response.text


def test_report_html_returns_404_for_unknown_history(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    response = client.get("/reports/999999.html")

    assert response.status_code == 404


def test_report_pdf_download_returns_valid_pdf(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)
    score_response = client.post("/score/", json={"query": "지하수"})
    history_id = score_response.json()["history_id"]

    response = client.get(f"/reports/{history_id}.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-1.4")
    assert b"Model version:" in response.content
    assert b"Banding model:" in response.content
    assert b"Score rationale:" in response.content
    assert b"Strategies:" in response.content
    assert b"Relationship summary:" in response.content
    assert b"Standards:" in response.content
    assert b"Roles:" in response.content
    assert f"tunnel-report-{history_id}.pdf" in response.headers["content-disposition"]


def test_report_pdf_returns_404_for_unknown_history(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    response = client.get("/reports/999999.pdf")

    assert response.status_code == 404


def test_report_package_download_contains_html_pdf_and_metadata(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)
    score_response = client.post("/score/", json={"query": "지하수"})
    history_id = score_response.json()["history_id"]

    response = client.get(f"/reports/{history_id}.zip")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        assert f"tunnel-report-{history_id}.html" in names
        assert f"tunnel-report-{history_id}.pdf" in names
        assert "metadata.json" in names
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
    assert metadata["history_id"] == history_id
    assert metadata["query"] == "지하수"


def test_report_package_returns_404_for_unknown_history(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    response = client.get("/reports/999999.zip")

    assert response.status_code == 404


def test_report_share_state_is_persisted(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)
    score_response = client.post("/score/", json={"query": "지하수"})
    history_id = score_response.json()["history_id"]

    share_response = client.post(f"/reports/{history_id}/share", json={"shared": True})
    list_response = client.get("/reports")

    assert share_response.status_code == 200
    assert share_response.json()["shared"] is True
    assert share_response.json()["share_url"] == f"/reports/shared/{history_id}.html"
    assert list_response.status_code == 200
    assert list_response.json()["summary"]["shared"] == 1
    assert list_response.json()["items"][0]["shared"] is True
    assert list_response.json()["items"][0]["share_url"] == f"/reports/shared/{history_id}.html"


def test_shared_report_link_requires_shared_state(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)
    score_response = client.post("/score/", json={"query": "지하수"})
    history_id = score_response.json()["history_id"]

    inactive_response = client.get(f"/reports/shared/{history_id}.html")
    share_response = client.post(f"/reports/{history_id}/share", json={"shared": True})
    active_response = client.get(f"/reports/shared/{history_id}.html")

    assert inactive_response.status_code == 404
    assert share_response.status_code == 200
    assert active_response.status_code == 200
    assert "터널 위험 분석 리포트" in active_response.text


def test_report_share_returns_404_for_unknown_history(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    response = client.post("/reports/999999/share", json={"shared": True})

    assert response.status_code == 404


def test_comparison_report_is_listed_and_downloadable(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)
    create_response = client.post(
        "/compare/design-change/reports",
        json={
            "before": {"query": "기존 조건"},
            "after": {"ground": "파쇄대", "query": "변경 조건"},
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    report_id = created["id"]
    assert created["report_type"] == "comparison"
    assert created["download_url"] == f"/reports/compare/{report_id}.html"

    list_response = client.get("/reports", params={"query": "설계변경"})
    html_response = client.get(f"/reports/compare/{report_id}.html")
    pdf_response = client.get(f"/reports/compare/{report_id}.pdf")
    package_response = client.get(f"/reports/compare/{report_id}.zip")

    assert list_response.status_code == 200
    assert any(item["report_type"] == "comparison" and item["history_id"] == report_id for item in list_response.json()["items"])
    assert html_response.status_code == 200
    assert "설계변경 비교 리포트" in html_response.text
    assert "변경 전 조건" in html_response.text
    assert "변경 후 조건" in html_response.text
    assert "신규 발생 가능 리스크" in html_response.text
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF-1.4")
    assert package_response.status_code == 200
    with ZipFile(BytesIO(package_response.content)) as archive:
        names = set(archive.namelist())
        assert f"tunnel-comparison-report-{report_id}.html" in names
        assert f"tunnel-comparison-report-{report_id}.pdf" in names
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
    assert metadata["report_type"] == "comparison"
