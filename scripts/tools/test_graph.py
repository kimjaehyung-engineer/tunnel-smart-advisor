import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.graph_builder import build_graph_json
from backend.services.risk_scoring import score_risks


def main() -> None:
    result = score_risks(
        selection={
            "process": None,
            "ground": None,
            "location": None,
            "method": None,
            "equipment": None,
        },
        user_query="파쇄대 굴착",
    )
    graph = build_graph_json(
        result["target_nodes"],
        result["sorted_risks"],
        result["risk_levels"],
        result["risk_matches"],
    )
    print(f"Graph JSON built successfully: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")


if __name__ == "__main__":
    main()
