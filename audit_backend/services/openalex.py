import requests
import difflib
from typing import Optional, Dict, Any


def reconstruct_abstract(inverted_index: Dict[str, list]) -> str:
    """OpenAlex 倒排索引转文本"""
    if not inverted_index:
        return ""
    word_list = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_list.append((pos, word))
    word_list.sort(key=lambda x: x[0])
    return " ".join([w[1] for w in word_list])


def check_author_match(query_author: str, paper_authors: list) -> bool:
    """检查作者是否匹配 (宽松模式)"""
    if not query_author:
        return True

    q_parts = set(query_author.lower().replace(",", "").replace(".", "").split())
    # 移除无意义的词
    q_parts.discard("et")
    q_parts.discard("al")

    for db_author in paper_authors:
        db_parts = set(db_author.lower().replace(",", "").replace(".", "").split())
        # 如果名字里有交集 (例如 "Ekman" 匹配 "Paul Ekman")
        if q_parts.intersection(db_parts):
            return True
    return False


def get_similarity_score(str1: str, str2: str) -> float:
    """计算两个标题的相似度 (0.0 - 1.0)"""
    return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def search_paper_on_openalex(title: str, author: Optional[str] = None) -> Dict[str, Any]:
    # 1. 预处理
    clean_title = title.replace('"', '').replace("'", "").replace("“", "").replace("”", "").strip()
    if len(clean_title) < 3:
        return {"found": False, "reason": "标题太短"}

    base_url = "https://api.openalex.org/works"
    params = {
        "search": clean_title,
        "per_page": 10,  # 抓取更多结果以便筛选
        "mailto": "audit_test@realibuddy.com"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code != 200:
            return {"found": False, "reason": f"API Error {response.status_code}"}

        data = response.json()
        raw_results = data.get("results", [])

        if not raw_results:
            return {"found": False, "reason": "未找到匹配文献"}

        # 2. 智能评分与排序
        scored_candidates = []

        for paper in raw_results:
            paper_authors = [a["author"]["display_name"] for a in paper.get("authorships", [])]
            paper_title = paper.get("title", "") or ""

            # 两个维度评分
            is_auth_match = check_author_match(author, paper_authors)
            title_sim = get_similarity_score(clean_title, paper_title)

            # 如果作者不匹配，我们要重罚相似度分 (防止书名一样但作者不同)
            # 但如果用户没提供作者，就不惩罚
            if author and not is_auth_match:
                title_sim = title_sim * 0.5

            scored_candidates.append({
                "paper": paper,
                "score": title_sim,
                "is_auth_match": is_auth_match
            })

        # 3. 排序策略：分数降序 -> 引用数降序
        scored_candidates.sort(key=lambda x: (x['score'], x['paper'].get('cited_by_count', 0)), reverse=True)

        best_candidate = scored_candidates[0]
        best_paper = best_candidate['paper']
        best_score = best_candidate['score']

        # 4. 阈值判定
        # 如果最相似的标题连 60% 的像都不到，那可能真不是这篇
        if best_score < 0.6:
            return {
                "found": False,
                "reason": f"找到最接近的文献是 '{best_paper.get('title')}'，但标题差异过大 (相似度 {best_score:.2f})，判定为未找到。"
            }

        # 5. 提取最终数据
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

    except Exception as e:
        print(f"OpenAlex Error: {e}")
        return {"found": False, "reason": str(e)}