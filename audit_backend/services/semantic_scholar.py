import requests
import difflib
from typing import Optional, Dict, Any


def search_paper_on_semantic_scholar(title: str, author: Optional[str] = None) -> Dict[str, Any]:
    """
    在 Semantic Scholar 中搜索论文。
    """
    if not title or len(title) < 3:
        return {"found": False, "reason": "Title too short"}

    # 使用 Graph API 的 search endpoint
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    # 限制返回字段：title, authors, year, abstract, openAccessPdf, citationCount
    params = {
        "query": title,
        "limit": 5,
        "fields": "title,authors,year,abstract,openAccessPdf,citationCount,url,externalIds"
    }

    try:
        response = requests.get(url, params=params, timeout=20)

        if response.status_code != 200:
            return {"found": False, "reason": f"S2 API Error {response.status_code}"}

        data = response.json()
        results = data.get("data", [])

        if not results:
            return {"found": False, "reason": "Not found in Semantic Scholar"}

        # --- 筛选逻辑 ---
        # 复用 OpenAlex 的筛选思路：优先匹配作者
        best_match = None

        clean_title = title.lower().replace('"', '').replace("'", "").strip()

        for paper in results:
            paper_authors = [a["name"] for a in paper.get("authors", [])]
            paper_title = paper.get("title", "") or ""

            # 作者匹配
            author_match = False
            if author:
                q_parts = set(author.lower().replace(",", "").split())
                for db_author in paper_authors:
                    db_parts = set(db_author.lower().replace(",", "").split())
                    if q_parts.intersection(db_parts):
                        author_match = True
                        break
            else:
                author_match = True  # 没提供作者就当匹配

            # 标题相似度
            title_sim = difflib.SequenceMatcher(None, clean_title, paper_title.lower()).ratio()

            # 判定：作者匹配且标题相似度 > 0.6，或者标题极度相似 > 0.9
            if (author_match and title_sim > 0.6) or (title_sim > 0.9):
                best_match = paper
                break

        if not best_match:
            return {"found": False, "reason": "Found candidates but details mismatch"}

        # 提取数据
        return {
            "found": True,
            "title": best_match.get("title"),
            "year": str(best_match.get("year", "")),
            "authors": [a["name"] for a in best_match.get("authors", [])[:3]],
            "abstract": best_match.get("abstract", ""),
            "oa_url": best_match.get("openAccessPdf", {}).get("url") if best_match.get(
                "openAccessPdf") else best_match.get("url"),
            "cited_by_count": best_match.get("citationCount", 0),
            "source": "Semantic Scholar"
        }

    except Exception as e:
        print(f"[Semantic Scholar Error] {e}")
        return {"found": False, "reason": str(e)}