from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "터널표준체크리스트"

NODE_FILES = {
    "ground":     DATA_DIR / "nodes_ground.csv",
    "method":     DATA_DIR / "nodes_method.csv",
    "equipment":  DATA_DIR / "nodes_equipment.csv",
    "risk":       DATA_DIR / "nodes_risk.csv",
    "process":    DATA_DIR / "nodes_process.csv",
    "location":   DATA_DIR / "nodes_location.csv",
    "strategy":   DATA_DIR / "nodes_strategy.csv",
}
RELS_FILE = DATA_DIR / "rels_total.csv"