import pandas as pd
from pathlib import Path
from .config import NODE_FILES, RELS_FILE
from functools import lru_cache

@lru_cache(maxsize=1)
def load_data():
    """Load all 8 CSVs. Cached on first call. Matches original app.py lines 126-136."""
    return {
        "ground":    pd.read_csv(NODE_FILES["ground"]),
        "method":    pd.read_csv(NODE_FILES["method"]),
        "equipment": pd.read_csv(NODE_FILES["equipment"]),
        "risk":      pd.read_csv(NODE_FILES["risk"]),
        "process":   pd.read_csv(NODE_FILES["process"]),
        "location":  pd.read_csv(NODE_FILES["location"]),
        "strategy":  pd.read_csv(NODE_FILES["strategy"]),
        "rels":      pd.read_csv(RELS_FILE),
    }