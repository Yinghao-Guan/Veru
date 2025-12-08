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


async def search_paper_on_openalex(title: Optional[str], author: Optional[str] = None, year: Optional[str] = None,
                                   doi: Optional[str] = None) -> Dict[str, Any]:
    # --- 策略 0: DOI 精确查找 (最高优先级) ---
    if doi:
        # 清洗 DOI (去掉 https://doi.org/ 前缀)
        clean_doi = doi.replace("https://doi.org/", "").replace("doi:", "").strip()
        print(f"[OpenAlex] Searching by DOI: {clean_doi}")
        results = await fetch_from_openalex({"filter": f"doi:https://doi.org/{clean_doi}"})
        if results:
            best_paper = results[0]
            # 直接返回，无需评分
            return _format_result(best_paper, found=True)

    # --- 常规标题搜索 ---
    if not title:
        return {"found": False, "reason": "No title extracted"}

    clean_title = title.replace('"', '').replace("'", "").replace("“", "").replace("”", "").strip()
    if len(clean_title) < 3:
        return {"found": False, "reason": "Title is too short"}

    # 策略 1: 宽泛搜索
    results = await fetch_from_openalex({
        "search": clean_title,
        "per_page": 20,
        "mailto": "audit_test@realibuddy.com"
    })

    # 策略 2: 精准过滤 (如果宽泛搜索没结果)
    if not results and len(clean_title.split()) > 2:
        results = await fetch_from_openalex({
            "filter": f"title.search:{clean_title}",
            "per_page": 20,
            "mailto": "audit_test@realibuddy.com"
        })

    if not results:
        return {"found": False, "reason": "No matches found in OpenAlex"}

    # --- 智能评分逻辑 ---
    candidates = []
    target_year = int(year) if (year and year.isdigit()) else None

    for paper in results:
        paper_authors = [a["author"]["display_name"] for a in paper.get("authorships", [])]
        paper_title = paper.get("title", "") or ""
        paper_year = paper.get("publication_year")

        # 1. 基础分：标题相似度 (0.0 - 1.0)
        title_sim = get_similarity_score(clean_title, paper_title)

        # 2. 作者验证 (权重调整)
        is_auth_match = check_author_match(author, paper_authors)

        # 3. 年份验证 (允许 ±1 年误差)
        is_year_match = False
        if target_year and paper_year:
            if abs(target_year - paper_year) <= 1:
                is_year_match = True

        # --- 综合打分 ---
        final_score = title_sim

        # 惩罚：作者不对，分数打 6 折
        if author and not is_auth_match:
            final_score *= 0.6

        # 奖励：年份匹配，增加置信度
        if is_year_match:
            final_score += 0.15

            # 奖励：高引用数 (说明是重要论文，更可能是用户想引用的)
        citations = paper.get("cited_by_count", 0)
        if citations > 100:
            final_score += 0.05

        candidates.append({
            "paper": paper,
            "score": final_score,
            "raw_sim": title_sim
        })

    # 按分数降序排序
    candidates.sort(key=lambda x: x['score'], reverse=True)
    best_candidate = candidates[0]

    # 阈值判断：虽然我们要宽松，但如果原始标题相似度太低，依然算作失败
    # 除非作者和年份都完全匹配
    threshold = 0.6

    # 宽松特例：如果作者对且年份对，标题相似度只要 > 0.4 即可（应对标题简写）
    if author and year and check_author_match(author, [a["author"]["display_name"] for a in
                                                       best_candidate['paper'].get("authorships", [])]):
        if abs(int(year) - (best_candidate['paper'].get("publication_year") or 0)) <= 1:
            threshold = 0.4

    if best_candidate['score'] < threshold:
        return {"found": False, "reason": f"Low confidence match ({best_candidate['score']:.2f})"}

    return _format_result(best_candidate['paper'], found=True)


def _format_result(paper: dict, found: bool) -> dict:
    """辅助函数：格式化 OpenAlex 返回的数据"""
    abstract_text = ""
    inverted_idx = paper.get("abstract_inverted_index")
    if inverted_idx:
        abstract_text = reconstruct_abstract(inverted_idx)

    return {
        "found": found,
        "title": paper.get("title"),
        "doi": paper.get("doi"),
        "year": str(paper.get("publication_year")),
        "authors": [a["author"]["display_name"] for a in paper.get("authorships", [])[:3]],
        "is_oa": paper.get("open_access", {}).get("is_oa", False),
        "oa_url": paper.get("open_access", {}).get("oa_url", None),
        "abstract": abstract_text,
        "cited_by_count": paper.get("cited_by_count", 0),
        "id": paper.get("id")
    }