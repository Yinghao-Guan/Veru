import httpx
import difflib
import re
from typing import Optional, Dict, Any


def reconstruct_abstract(inverted_index: Dict[str, list]) -> str:
    if not inverted_index:
        return ""
    word_list = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_list.append((pos, word))
    word_list.sort(key=lambda x: x[0])
    return " ".join([w[1] for w in word_list])


def check_author_match(query_author: str, paper_authors: list) -> bool:
    if not query_author:
        return True

    q_parts = set(query_author.lower().replace(",", "").replace(".", "").split())
    q_parts.discard("et")
    q_parts.discard("al")

    for db_author in paper_authors:
        db_parts = set(db_author.lower().replace(",", "").replace(".", "").split())
        if q_parts.intersection(db_parts):
            return True
    return False


def get_similarity_score(str1: str, str2: str) -> float:
    s1 = re.sub(r'[^\w\s]', '', str1.lower())
    s2 = re.sub(r'[^\w\s]', '', str2.lower())
    return difflib.SequenceMatcher(None, s1, s2).ratio()


async def fetch_from_openalex(params: dict) -> list:
    try:
        # 使用异步上下文管理器
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://api.openalex.org/works", params=params)
            if response.status_code == 200:
                return response.json().get("results", [])
    except Exception as e:
        print(f"[OpenAlex Error] {e}")
        pass
    return []


async def search_paper_on_openalex(title: Optional[str], author: Optional[str] = None) -> Dict[str, Any]:
    # 如果 title 是 None，直接返回 False，防止崩溃
    if not title:
        return {"found": False, "reason": "No title extracted"}

    clean_title = title.replace('"', '').replace("'", "").replace("“", "").replace("”", "").strip()

    # 再次检查清洗后是否为空
    if len(clean_title) < 3:
        return {"found": False, "reason": "Title is too short"}

    # 策略 1: 宽泛搜索
    results = await fetch_from_openalex({
        "search": clean_title,
        "per_page": 20,
        "mailto": "audit_test@veru.app"
    })

    # 策略 2: 精准过滤
    if not results and len(clean_title.split()) > 2:
        results = await fetch_from_openalex({
            "filter": f"title.search:{clean_title}",
            "per_page": 20,
            "mailto": "audit_test@veru.app"
        })

    if not results:
        return {"found": False, "reason": "No matches found in OpenAlex"}

    # 评分逻辑
    candidates = []
    for paper in results:
        paper_authors = [a["author"]["display_name"] for a in paper.get("authorships", [])]
        paper_title = paper.get("title", "") or ""

        is_auth_match = check_author_match(author, paper_authors)
        title_sim = get_similarity_score(clean_title, paper_title)

        if author and not is_auth_match:
            title_sim *= 0.5

        normalized_score = title_sim
        citations = paper.get("cited_by_count", 0)

        if title_sim > 0.85:
            if citations > 1000:
                normalized_score += 2.0
            elif citations > 50:
                normalized_score += 1.0

        candidates.append({
            "paper": paper,
            "sort_key": normalized_score,
            "raw_score": title_sim
        })

    candidates.sort(key=lambda x: (x['sort_key'], x['paper'].get('cited_by_count', 0)), reverse=True)

    best_candidate = candidates[0]

    if best_candidate['raw_score'] < 0.6:
        return {"found": False, "reason": f"Low similarity match ({best_candidate['raw_score']:.2f})"}

    best_paper = best_candidate['paper']
    abstract_text = ""
    inverted_idx = best_paper.get("abstract_inverted_index")
    if inverted_idx:
        abstract_text = reconstruct_abstract(inverted_idx)

    return {
        "found": True,
        "title": best_paper.get("title"),
        "doi": best_paper.get("doi"),
        "year": str(best_paper.get("publication_year")),
        "authors": [a["author"]["display_name"] for a in best_paper.get("authorships", [])[:3]],
        "is_oa": best_paper.get("open_access", {}).get("is_oa", False),
        "oa_url": best_paper.get("open_access", {}).get("oa_url", None),
        "abstract": abstract_text,
        "cited_by_count": best_paper.get("cited_by_count", 0),
        "id": best_paper.get("id")
    }