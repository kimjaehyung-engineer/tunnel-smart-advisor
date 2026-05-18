import json

import pytest
import pandas as pd

from scripts.tools.validate_ontology import assert_allowed_relation_types, assert_lesson_relations_valid, assert_numeric_columns, assert_ontology_version_metadata, assert_required_values, assert_strategy_targets_exist


def test_ontology_version_metadata_requires_source_hash(tmp_path) -> None:
    version_path = tmp_path / "ontology_version.json"
    version_path.write_text(
        json.dumps({
            "source_file": "source.xlsx",
            "source_file_hash": "missing",
            "source_file_mtime": "2026-05-18T00:00:00+00:00",
            "ontology_build_at": "2026-05-18T00:00:00+00:00",
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="source_file_hash"):
        assert_ontology_version_metadata(version_path)


def test_ontology_version_metadata_accepts_sha256_hash(tmp_path) -> None:
    version_path = tmp_path / "ontology_version.json"
    version_path.write_text(
        json.dumps({
            "source_file": "source.xlsx",
            "source_file_hash": "a" * 64,
            "source_file_mtime": "2026-05-18T00:00:00+00:00",
            "ontology_build_at": "2026-05-18T00:00:00+00:00",
        }),
        encoding="utf-8",
    )

    assert_ontology_version_metadata(version_path)


def test_relation_type_validation_rejects_unknown_type() -> None:
    rels = pd.DataFrame({":START_ID": ["Proc_1"], ":END_ID": ["Risk_001"], ":TYPE": ["TYPO_REL"]})

    with pytest.raises(ValueError, match="TYPO_REL"):
        assert_allowed_relation_types(rels)


def test_relation_type_validation_accepts_canonical_types() -> None:
    rels = pd.DataFrame({":START_ID": ["Proc_1", "Risk_001"], ":END_ID": ["Risk_001", "Strategy_001"], ":TYPE": ["ENCOUNTERS", "MITIGATED_BY"]})

    assert_allowed_relation_types(rels)


def test_required_source_metadata_rejects_blank_values() -> None:
    risks = pd.DataFrame({"source_project": [""], "source_version": ["source.xlsx"]})

    with pytest.raises(ValueError, match="risk.source_project"):
        assert_required_values("risk", risks)


def test_required_source_metadata_accepts_populated_values() -> None:
    risks = pd.DataFrame({"source_project": ["평택 브레인시티 1단계"], "source_version": ["source.xlsx"]})
    strategies = pd.DataFrame({"source_project": ["평택 브레인시티 1단계"], "target_risk": ["Risk_001"], "expected_effect": ["진입로 단절 리스크 완화"]})

    assert_required_values("risk", risks)
    assert_required_values("strategy", strategies)


def test_required_strategy_metadata_rejects_blank_target_risk() -> None:
    strategies = pd.DataFrame({"source_project": ["평택 브레인시티 1단계"], "target_risk": [""], "expected_effect": ["진입로 단절 리스크 완화"]})

    with pytest.raises(ValueError, match="strategy.target_risk"):
        assert_required_values("strategy", strategies)


def test_numeric_score_validation_rejects_non_numeric_values() -> None:
    risks = pd.DataFrame({
        "likelihood": ["high"],
        "impact_score": [3],
        "frequency": [1],
        "recency": [1],
        "confidence": [0.5],
        "expert_weight": [1],
    })

    with pytest.raises(ValueError, match="risk.likelihood"):
        assert_numeric_columns("risk", risks)


def test_numeric_score_validation_accepts_numeric_values() -> None:
    risks = pd.DataFrame({
        "likelihood": [1.0],
        "impact_score": [3],
        "frequency": [1],
        "recency": [1],
        "confidence": [0.5],
        "expert_weight": [1],
    })

    assert_numeric_columns("risk", risks)


def test_numeric_score_validation_rejects_out_of_range_values() -> None:
    risks = pd.DataFrame({
        "likelihood": [6.0],
        "impact_score": [3],
        "frequency": [1],
        "recency": [1],
        "confidence": [0.5],
        "expert_weight": [1],
    })

    with pytest.raises(ValueError, match="above 5.0"):
        assert_numeric_columns("risk", risks)


def test_numeric_score_validation_rejects_negative_weights() -> None:
    risks = pd.DataFrame({
        "likelihood": [1.0],
        "impact_score": [3],
        "frequency": [-1],
        "recency": [1],
        "confidence": [0.5],
        "expert_weight": [1],
    })

    with pytest.raises(ValueError, match="below 0.0"):
        assert_numeric_columns("risk", risks)


def test_strategy_target_validation_rejects_unknown_risk() -> None:
    strategies = pd.DataFrame({"target_risk": ["Risk_DOES_NOT_EXIST"]})
    risks = pd.DataFrame({"id:ID": ["Risk_001"]})

    with pytest.raises(ValueError, match="Risk_DOES_NOT_EXIST"):
        assert_strategy_targets_exist(strategies, risks)


def test_strategy_target_validation_accepts_existing_risk() -> None:
    strategies = pd.DataFrame({"target_risk": ["Risk_001"]})
    risks = pd.DataFrame({"id:ID": ["Risk_001"]})

    assert_strategy_targets_exist(strategies, risks)


def test_lesson_relation_validation_rejects_unknown_lesson() -> None:
    lesson_rels = pd.DataFrame({":START_ID": ["Risk_1"], ":END_ID": ["Lesson_DOES_NOT_EXIST"], ":TYPE": ["LEARNED_AS"]})
    lessons = pd.DataFrame({"id:ID": ["Lesson_1"]})
    risks = pd.DataFrame({"id:ID": ["Risk_001"]})

    with pytest.raises(ValueError, match="Lesson_DOES_NOT_EXIST"):
        assert_lesson_relations_valid(lesson_rels, lessons, risks)


def test_lesson_relation_validation_accepts_risk_aliases() -> None:
    lesson_rels = pd.DataFrame({":START_ID": ["Risk_1"], ":END_ID": ["Lesson_1"], ":TYPE": ["LEARNED_AS"]})
    lessons = pd.DataFrame({"id:ID": ["Lesson_1"]})
    risks = pd.DataFrame({"id:ID": ["Risk_001"]})

    assert_lesson_relations_valid(lesson_rels, lessons, risks)
