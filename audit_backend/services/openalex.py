import requests
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
    # 移除标点符号，提高纯文本匹配度
    s1 = re.sub(r'[^\w\s]', '', str1.lower())
    s2 = re.sub(r'[^\w\s]', '', str2.lower())
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def fetch_from_openalex(params: dict) -> list:
    try:
        response = requests.get("https://api.openalex.org/works", params=params, timeout=20)
        if response.status_code == 200:
            return response.json().get("results", [])
    except:
        pass
    return []


def search_paper_on_openalex(title: str, author: Optional[str] = None) -> Dict[str, Any]:
    clean_title = title.replace('"', '').replace("'", "").replace("“", "").replace("”", "").strip()
    if len(clean_title) < 3:
        return {"found": False, "reason": "Title is too short"}

    # 策略 1: 宽泛搜索
    results = fetch_from_openalex({
        "search": clean_title,
        "per_page": 20,  # 抓更多结果，增加抓到原版的概率
        "mailto": "audit_test@realibuddy.com"
    })

    # 策略 2: 如果标题长且没结果，尝试精确过滤
    if not results and len(clean_title.split()) > 2:
        results = fetch_from_openalex({
            "filter": f"title.search:{clean_title}",
            "per_page": 20,
            "mailto": "audit_test@realibuddy.com"
        })

    if not results:
        return {"found": False, "reason": "No matches found in OpenAlex"}

    # === 关键改进：分层排序逻辑 (Tiered Sorting) ===
    candidates = []

    for paper in results:
        paper_authors = [a["author"]["display_name"] for a in paper.get("authorships", [])]
        paper_title = paper.get("title", "") or ""

        is_auth_match = check_author_match(author, paper_authors)
        title_sim = get_similarity_score(clean_title, paper_title)

        candidates.append({
            "paper": paper,
            "score": title_sim,
            "is_auth_match": is_auth_match,
            "citations": paper.get("cited_by_count", 0)
        })

    # Tier 1: 完美候选人 (标题极其相似 + 作者匹配)
    # 在这个梯队里，我们完全只看引用数，谁引用多谁就是原版
    tier_1 = [c for c in candidates if c['score'] > 0.85 and c['is_auth_match']]

    if tier_1:
        # 绝对引用数优先！
        tier_1.sort(key=lambda x: x['citations'], reverse=True)
        best_candidate = tier_1[0]
    else:
        # Tier 2: 混战模式 (作者不匹配或标题不太像)
        # 此时需要权衡相似度和引用数
        def fallback_sort_key(x):
            score = x['score']
            if x['is_auth_match']: score += 0.5  # 作者匹配加分
            # 引用数只是辅助加分
            if x['citations'] > 1000: score += 0.2
            return score

        candidates.sort(key=fallback_sort_key, reverse=True)
        best_candidate = candidates[0]

    # 阈值检查
    if best_candidate['score'] < 0.6:
        return {"found": False, "reason": f"Low similarity match ({best_candidate['score']:.2f})"}

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