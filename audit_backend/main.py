from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import re

# Import Services
from services.llm_extractor import extract_citations_from_text
from services.openalex import search_paper_on_openalex
from services.google_search import verify_with_google_search
from services.auditor import verify_content_consistency
from services.semantic_scholar import search_paper_on_semantic_scholar

app = FastAPI(title="Veru Audit Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditRequest(BaseModel):
    text: str


class AuditResult(BaseModel):
    citation_text: str
    status: str
    source: str
    metadata: dict
    message: str
    confidence: float


def get_clean_year(year_val):
    """Helper to extract 4-digit year string"""
    return "".join(filter(str.isdigit, str(year_val or "")))


@app.post("/api/audit", response_model=List[AuditResult])
def audit_citations(request: AuditRequest):
    citations = extract_citations_from_text(request.text)
    results = []

    for cit in citations:
        print(f"--- Auditing: {cit.title} ---")

        # 1. OpenAlex 查询
        oa_result = search_paper_on_openalex(cit.title, cit.author)

        # 初始化最佳结果为 OpenAlex
        best_result = oa_result
        source_name = "OpenAlex"

        # 检查 OpenAlex 的年份匹配情况
        cit_year = get_clean_year(cit.year)
        oa_year = get_clean_year(oa_result.get("year"))
        is_oa_year_match = (cit_year == oa_year) if (cit_year and oa_year) else True

        # === 关键改进：竞优逻辑 ===
        # 触发条件：OpenAlex 没找到，或者找到了但年份不对
        if not oa_result["found"] or (oa_result["found"] and not is_oa_year_match):
            print(
                f"⚠️ OpenAlex result imperfect (Found: {oa_result['found']}, Year Match: {is_oa_year_match}). Checking Semantic Scholar...")

            s2_result = search_paper_on_semantic_scholar(cit.title, cit.author)

            if s2_result["found"]:
                s2_year = get_clean_year(s2_result.get("year"))
                is_s2_year_match = (cit_year == s2_year) if (cit_year and s2_year) else True

                # 决策点 1: OpenAlex 没找到，S2 找到了 -> 用 S2
                if not oa_result["found"]:
                    print("✅ Using Semantic Scholar (OpenAlex missed)")
                    best_result = s2_result
                    source_name = "Semantic Scholar"

                # 决策点 2: 都有结果，但 OpenAlex 年份错，S2 年份对 -> 用 S2
                elif not is_oa_year_match and is_s2_year_match:
                    print(f"✅ Switching to Semantic Scholar (Better Year Match: {s2_year} vs OA {oa_year})")
                    best_result = s2_result
                    source_name = "Semantic Scholar"

                # 决策点 3: 都有结果，年份都错 -> 保持 OpenAlex (或者对比引用数，这里暂略)

        # 3. 执行审计 (使用最终选定的 best_result)
        if best_result["found"]:
            print(f"Checking content consistency (Source: {source_name})...")
            consistency_check = verify_content_consistency(
                user_claim=cit.summary_intent + " " + " ".join(cit.specific_claims),
                real_abstract=best_result.get("abstract", "")
            )

            final_status = consistency_check.get("status", "REAL")
            explanation = consistency_check.get("reason", "Verification passed.")

            # 再次检查年份 (针对最终选定的结果)
            db_year = get_clean_year(best_result.get("year"))

            if final_status == "REAL" and len(cit_year) == 4 and len(db_year) == 4:
                if cit_year != db_year:
                    if int(db_year) > int(cit_year):
                        explanation += f" (Note: Database lists a later version from {db_year}). Please double check."
                    else:
                        final_status = "MINOR_ERROR"
                        explanation += f" Note: Year mismatch (Cited: {cit_year}, DB: {db_year})."

            result = AuditResult(
                citation_text=cit.raw_text,
                status=final_status,
                source=source_name,
                confidence=consistency_check.get("confidence", 1.0),
                metadata=best_result,
                message=f"Citation found. Content Audit: {final_status} - {explanation}"
            )

        else:
            # 4. 最后的兜底：Google Search
            print("❌ Databases failed, switching to Google Search...")
            gs_result = verify_with_google_search(cit.title, cit.author, cit.summary_intent)

            status_map = {"REAL": "REAL", "FAKE": "FAKE", "MISMATCH": "MISMATCH", "UNVERIFIED": "UNVERIFIED"}
            g_status = status_map.get(gs_result.get("verdict"), "UNVERIFIED")

            result = AuditResult(
                citation_text=cit.raw_text,
                status=g_status,
                source="Google Search",
                confidence=gs_result.get("confidence", 0.0),
                metadata={"reason": gs_result.get("reason"), "info": gs_result.get("actual_paper_info")},
                message=f"Not found in academic databases. Google Search verdict: {g_status} - {gs_result.get('reason')}"
            )

        results.append(result)

    return results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)