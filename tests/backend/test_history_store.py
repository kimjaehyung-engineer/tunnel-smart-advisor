from pathlib import Path

from backend.services.history_store import get_analysis, list_analyses, save_analysis


def test_save_list_and_get_analysis_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "history.sqlite3"
    selection = {
        "process": None,
        "ground": "파쇄대",
        "location": None,
        "method": None,
        "equipment": None,
    }
    result = {
        "total_risks": 1,
        "critical_count": 1,
        "max_score": 10.0,
        "risks": [{"description": "지하수 유입 위험"}],
        "graph": {"nodes": [], "edges": []},
    }

    saved = save_analysis(selection, "지하수", result, db_path=db_path)
    items = list_analyses(db_path=db_path)
    detail = get_analysis(saved["id"], db_path=db_path)

    assert saved["id"] > 0
    assert len(items) == 1
    assert items[0]["top_risk"] == "지하수 유입 위험"
    assert detail is not None
    assert detail["result"]["total_risks"] == 1
