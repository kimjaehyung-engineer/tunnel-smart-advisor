import re
from typing import TypedDict


class StandardEvidence(TypedDict):
    code: str
    name: str
    version: str
    source_url: str
    section_path: list[str]
    section_label: str
    text: str
    confidence: str


class StandardSummary(TypedDict):
    code: str
    name: str
    version: str
    source_url: str
    clause_count: int


class StandardRevalidationItem(TypedDict):
    id: str
    doc_name: str
    status: str
    verified_code: str
    candidate_codes: list[str]
    message: str


STANDARD_EVIDENCE: list[StandardEvidence] = [
    {
        "code": "KCS 27 30 00",
        "name": "터널 지보재 시공",
        "version": "2023",
        "source_url": "https://kcsc.re.kr/OpenApi/CodeViewer/KCS/273000",
        "section_path": ["3. 시공", "3.1 시공조건확인", "3.1.1 지보재 일반"],
        "section_label": "(4)",
        "text": "터널지보재는 강지보재, 숏크리트, 철망, 록볼트, 콘크리트라이닝 등으로 구성되며 필요에 따라 조합시켜 적합한 방법으로 적절한 시기와 순서에 따라 시공하여야 한다.",
        "confidence": "KCSC MCP 원문 직접 근거",
    },
    {
        "code": "KCS 27 30 00",
        "name": "터널 지보재 시공",
        "version": "2023",
        "source_url": "https://kcsc.re.kr/OpenApi/CodeViewer/KCS/273000",
        "section_path": ["1. 일반사항", "1.1 적용범위"],
        "section_label": "(1)",
        "text": "이 기준은 터널지보재로 사용되는 강지보재, 숏크리트, 록볼트의 시공 및 천단 또는 막장안정을 위한 보조공법 등의 공사에 적용한다.",
        "confidence": "KCSC MCP 원문 직접 근거",
    },
    {
        "code": "KDS 27 30 00",
        "name": "터널 지보재",
        "version": "2023",
        "source_url": "https://kcsc.re.kr/OpenApi/CodeViewer/KDS/273000",
        "section_path": ["4. 설계", "4.2 강지보재", "4.2.1 강지보재의 설계"],
        "section_label": "(1)",
        "text": "강지보재는 취약한 지반조건에서 터널굴착 초기의 안정성을 확보하기 위한 지보재 중의 하나로서, 산정된 작용하중을 부담할 수 있도록 사용강재 치수, 설치간격을 결정함과 동시에 숏크리트와 일체가 되어 지보기능을 유리하게 발휘할 수 있도록 설계하여야 한다.",
        "confidence": "KCSC MCP 원문 직접 근거",
    },
    {
        "code": "KCS 27 50 05",
        "name": "터널 배수 및 방수 공사",
        "version": "2023",
        "source_url": "https://kcsc.re.kr/OpenApi/CodeViewer/KCS/275005",
        "section_path": ["3. 시공", "3.3 시공기준"],
        "section_label": "(7)",
        "text": "비배수형 방수형식 터널에서는 콘크리트라이닝의 시공이음부에 지수판을 설치하여야 하며, 배수형 방수형식 터널의 경우에도 필요시 지수판을 설치할 수 있다.",
        "confidence": "KCSC MCP 원문 직접 근거",
    },
    {
        "code": "KCS 27 50 05",
        "name": "터널 배수 및 방수 공사",
        "version": "2023",
        "source_url": "https://kcsc.re.kr/OpenApi/CodeViewer/KCS/275005",
        "section_path": ["1. 일반사항", "1.5 시스템 설명"],
        "section_label": "(5)",
        "text": "외부 배수형 방수형식은 현장타설 라이닝 외부를 방수막으로 둘러싸고 터널 외부에 별도의 배수로를 설치하여 터널로 흘러들어오는 지하수를 집수하여 외부로 배수하는 형식이다.",
        "confidence": "KCSC MCP 원문 직접 근거",
    },
]


STANDARD_QUERY_ALIASES: dict[str, set[str]] = {
    "기준": {"KCS", "KDS", "터널", "지보", "배수", "방수"},
    "지침": {"KDS", "설계", "터널", "지보"},
    "표준": {"KCS", "시공", "터널", "지보", "배수", "방수"},
}


def search_evidence(query: str = "", limit: int = 10) -> list[StandardEvidence]:
    terms = {term for term in query.replace(",", " ").split() if term}
    expanded_terms = set(terms)
    for term in terms:
        expanded_terms.update(STANDARD_QUERY_ALIASES.get(term, set()))
    if not expanded_terms:
        return STANDARD_EVIDENCE[:limit]

    ranked: list[tuple[int, StandardEvidence]] = []
    for item in STANDARD_EVIDENCE:
        haystack = " ".join([
            item["code"],
            item["name"],
            " ".join(item["section_path"]),
            item["text"],
        ]).lower()
        score = sum(1 for term in expanded_terms if term.lower() in haystack)
        if score > 0:
            ranked.append((score, item))

    ranked.sort(key=lambda pair: (-pair[0], pair[1]["code"], pair[1]["section_label"]))
    return [item for _, item in ranked[:limit]]


def list_standards(query: str = "", limit: int = 20) -> list[StandardSummary]:
    clauses = search_evidence(query=query, limit=len(STANDARD_EVIDENCE)) if query.strip() else STANDARD_EVIDENCE
    summaries: dict[str, StandardSummary] = {}
    for item in clauses:
        summary = summaries.setdefault(item["code"], {
            "code": item["code"],
            "name": item["name"],
            "version": item["version"],
            "source_url": item["source_url"],
            "clause_count": 0,
        })
        summary["clause_count"] += 1
    return sorted(summaries.values(), key=lambda item: item["code"])[:limit]


def search_clauses(query: str = "", code: str = "", limit: int = 10) -> list[StandardEvidence]:
    clauses = search_evidence(query=query, limit=len(STANDARD_EVIDENCE)) if query.strip() else STANDARD_EVIDENCE
    normalized_code = code.strip().upper()
    if normalized_code:
        clauses = [item for item in clauses if item["code"].upper() == normalized_code]
    return clauses[:limit]


def verify_standard_code(code: str) -> dict[str, object]:
    normalized_code = normalize_standard_code(code)
    matches = [item for item in STANDARD_EVIDENCE if item["code"].upper() == normalized_code]
    if not matches:
        return {"code": normalized_code, "is_valid": False, "standard": None, "clause_count": 0}
    first = matches[0]
    return {
        "code": normalized_code,
        "is_valid": True,
        "standard": {
            "code": first["code"],
            "name": first["name"],
            "version": first["version"],
            "source_url": first["source_url"],
        },
        "clause_count": len(matches),
    }


def normalize_standard_code(code: str) -> str:
    return " ".join(code.upper().replace("-", " ").split())


def extract_standard_code(text: str) -> str:
    match = re.search(r"\b(KCS|KDS)[-\s]*(\d{2})[-\s]*(\d{2})[-\s]*(\d{2})\b", text.upper())
    if not match:
        return ""
    return f"{match.group(1)} {match.group(2)} {match.group(3)} {match.group(4)}"


def revalidate_standard_nodes(nodes: list[dict[str, object]]) -> dict[str, object]:
    items: list[StandardRevalidationItem] = []
    for node in nodes:
        node_id = str(node.get("id:ID", ""))
        doc_name = str(node.get("doc_name", ""))
        extracted_code = extract_standard_code(doc_name)
        if extracted_code:
            verification = verify_standard_code(extracted_code)
            is_valid = bool(verification["is_valid"])
            items.append({
                "id": node_id,
                "doc_name": doc_name,
                "status": "verified_code" if is_valid else "unknown_code",
                "verified_code": extracted_code if is_valid else "",
                "candidate_codes": [extracted_code] if is_valid else [],
                "message": "Seed evidence contains this standard code." if is_valid else "No seeded evidence currently matches this standard code.",
            })
            continue

        candidates = list_standards(query=doc_name, limit=5) if doc_name else []
        candidate_codes = [candidate["code"] for candidate in candidates]
        items.append({
            "id": node_id,
            "doc_name": doc_name,
            "status": "matched_candidates" if candidate_codes else "unknown",
            "verified_code": "",
            "candidate_codes": candidate_codes,
            "message": "Matched seeded standards by keyword alias; exact code is not stored on the ontology node." if candidate_codes else "No seeded standards matched this ontology node.",
        })

    verified_count = sum(1 for item in items if item["status"] == "verified_code")
    candidate_count = sum(1 for item in items if item["status"] == "matched_candidates")
    unknown_count = sum(1 for item in items if item["status"] in {"unknown", "unknown_code"})
    return {
        "total": len(items),
        "verified_count": verified_count,
        "candidate_count": candidate_count,
        "unknown_count": unknown_count,
        "items": items,
        "source": "KCSC Standards MCP seed evidence",
    }
