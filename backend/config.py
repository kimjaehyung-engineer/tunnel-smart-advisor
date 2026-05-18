import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
DEFAULT_DATA_DIR = BASE_DIR / "data" / "tunnel_checklist"
DEFAULT_DB_PATH = BASE_DIR / "data" / "runtime" / "tunnel_history.sqlite3"
DEFAULT_DEV_CORS_ORIGINS = ["http://127.0.0.1:2000"]
DEFAULT_SOURCE_EXCEL = DEFAULT_DATA_DIR / "터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx"
DEFAULT_PROJECT_NODES = BASE_DIR / "data" / "processed" / "nodes_project.csv"
DEFAULT_LESSON_NODES = BASE_DIR / "data" / "neo4j_import" / "nodes_lesson.csv"
DEFAULT_LESSON_RELS = BASE_DIR / "data" / "neo4j_import" / "rels.csv"


def resolve_repo_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


def parse_cors_origins(value: str | None, environment: str = "development") -> list[str]:
    if not value:
        if environment.lower() == "production":
            raise RuntimeError("TUNNEL_CORS_ORIGINS must be set in production")
        return DEFAULT_DEV_CORS_ORIGINS
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    if environment.lower() == "production":
        if not origins:
            raise RuntimeError("TUNNEL_CORS_ORIGINS must not be empty in production")
        if "*" in origins:
            raise RuntimeError("Wildcard CORS origins are not allowed in production")
    return origins or DEFAULT_DEV_CORS_ORIGINS


ENVIRONMENT = os.getenv("TUNNEL_ENV", "development")
DATA_DIR = resolve_repo_path(os.getenv("TUNNEL_DATA_DIR"), DEFAULT_DATA_DIR)
DB_PATH = resolve_repo_path(os.getenv("TUNNEL_DB_PATH"), DEFAULT_DB_PATH)
SOURCE_EXCEL_PATH = resolve_repo_path(os.getenv("TUNNEL_SOURCE_EXCEL"), DEFAULT_SOURCE_EXCEL)
ONTOLOGY_VERSION_FILE = DATA_DIR / "ontology_version.json"
CORS_ORIGINS = parse_cors_origins(os.getenv("TUNNEL_CORS_ORIGINS"), ENVIRONMENT)
LOG_LEVEL = os.getenv("TUNNEL_LOG_LEVEL", "INFO")
PROJECT_NODE_FILE = DATA_DIR / "nodes_project.csv" if (DATA_DIR / "nodes_project.csv").exists() else DEFAULT_PROJECT_NODES
LESSON_NODE_FILE = DATA_DIR / "nodes_lesson.csv" if (DATA_DIR / "nodes_lesson.csv").exists() else DEFAULT_LESSON_NODES
LESSON_RELS_FILE = DATA_DIR / "rels_lesson.csv" if (DATA_DIR / "rels_lesson.csv").exists() else DEFAULT_LESSON_RELS

NODE_FILES = {
    "ground":     DATA_DIR / "nodes_ground.csv",
    "method":     DATA_DIR / "nodes_method.csv",
    "equipment":  DATA_DIR / "nodes_equipment.csv",
    "risk":       DATA_DIR / "nodes_risk.csv",
    "process":    DATA_DIR / "nodes_process.csv",
    "location":   DATA_DIR / "nodes_location.csv",
    "strategy":   DATA_DIR / "nodes_strategy.csv",
    "role":       DATA_DIR / "nodes_role.csv",
    "standard":   DATA_DIR / "nodes_standard.csv",
    "impact":     DATA_DIR / "nodes_impact.csv",
    "project":    PROJECT_NODE_FILE,
    "lesson":     LESSON_NODE_FILE,
}
RELS_FILE = DATA_DIR / "rels_total.csv"
