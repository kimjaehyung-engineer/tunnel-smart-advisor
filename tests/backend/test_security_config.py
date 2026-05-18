import pytest

from backend.config import DEFAULT_DEV_CORS_ORIGINS, parse_cors_origins


def test_development_cors_defaults_to_local_frontend() -> None:
    assert parse_cors_origins(None, "development") == DEFAULT_DEV_CORS_ORIGINS


def test_production_requires_explicit_cors_origins() -> None:
    with pytest.raises(RuntimeError, match="must be set"):
        parse_cors_origins(None, "production")


def test_production_rejects_wildcard_cors_origin() -> None:
    with pytest.raises(RuntimeError, match="Wildcard"):
        parse_cors_origins("*", "production")


def test_cors_origin_list_is_trimmed() -> None:
    assert parse_cors_origins(" https://app.example.com,https://admin.example.com ", "production") == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
