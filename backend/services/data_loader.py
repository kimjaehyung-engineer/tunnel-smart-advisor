import pandas as pd
from ..config import LESSON_RELS_FILE, NODE_FILES, RELS_FILE
from functools import lru_cache


DataFrames = dict[str, pd.DataFrame]

@lru_cache(maxsize=1)
def load_data() -> DataFrames:
    """Load all ontology CSVs. Cached on first call for API requests."""
    return {
        "ground":    pd.read_csv(NODE_FILES["ground"]),
        "method":    pd.read_csv(NODE_FILES["method"]),
        "equipment": pd.read_csv(NODE_FILES["equipment"]),
        "risk":      pd.read_csv(NODE_FILES["risk"]),
        "process":   pd.read_csv(NODE_FILES["process"]),
        "location":  pd.read_csv(NODE_FILES["location"]),
        "strategy":  pd.read_csv(NODE_FILES["strategy"]),
        "role":      pd.read_csv(NODE_FILES["role"]),
        "standard":  pd.read_csv(NODE_FILES["standard"]),
        "impact":    pd.read_csv(NODE_FILES["impact"]),
        "project":   pd.read_csv(NODE_FILES["project"]),
        "lesson":    pd.read_csv(NODE_FILES["lesson"]),
        "rels":      pd.read_csv(RELS_FILE),
        "lesson_rels": pd.read_csv(LESSON_RELS_FILE),
    }


def data_row_counts(data: DataFrames | None = None) -> dict[str, int]:
    loaded_data = data if data is not None else load_data()
    return {key: len(frame) for key, frame in loaded_data.items()}


def reload_data() -> tuple[DataFrames, dict[str, int]]:
    """Clear the CSV cache and load fresh ontology data from disk."""
    load_data.cache_clear()
    data = load_data()
    return data, data_row_counts(data)
