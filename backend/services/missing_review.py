from typing import TypedDict


class MissingReviewRecommendation(TypedDict):
    type: str
    title: str
    reason: str
    suggested_filter: dict[str, str]


GROUNDWATER_TERMS = ("지하수", "용수", "누수", "차수", "배수", "침하")
FRACTURED_GROUND_TERMS = ("파쇄", "단층", "연약", "복합지반", "고수압")
TUNNEL_METHOD_TERMS = ("NATM", "TBM", "쉴드", "터널")


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def recommend_missing_reviews(selection: dict[str, str | None], user_query: str = "") -> list[MissingReviewRecommendation]:
    """Return advisory review recommendations for condition combinations that often need extra checks."""
    ground = selection.get("ground") or ""
    method = selection.get("method") or ""
    impact = selection.get("impact") or ""
    combined_context = " ".join([ground, method, impact, user_query])

    recommendations: list[MissingReviewRecommendation] = []
    has_fractured_ground = contains_any(ground, FRACTURED_GROUND_TERMS)
    has_tunnel_method = contains_any(method, TUNNEL_METHOD_TERMS)
    already_covers_groundwater = contains_any(combined_context, GROUNDWATER_TERMS)

    if has_fractured_ground and has_tunnel_method and not already_covers_groundwater:
        recommendations.append({
            "type": "missing_condition",
            "title": "지하수·용수 유입 추가 검토 권고",
            "reason": "파쇄대/단층성 지반과 터널 굴착 공법 조합에서는 지하수 유입, 차수, 배수, 침하 영향을 함께 검토하는 것이 안전합니다.",
            "suggested_filter": {"query": "지하수 유입"},
        })

    return recommendations
