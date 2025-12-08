from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import uvicorn
import re
import asyncio

# 引入限流库
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import Services
from services.llm_extractor import extract_citations_from_text
from services.openalex import search_paper_on_openalex
from services.google_search import verify_with_google_search
from services.auditor import verify_content_consistency
from services.semantic_scholar import search_paper_on_semantic_scholar

# 初始化限流器 (基于请求者的 IP 地址)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Veru Audit Engine")

# 将限流器挂载到 App
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 配置
origins = [
    "http://localhost:3000",
    "https://veru.app",
    "https://www.veru.app",
    "https://truvio.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    # 限制最大长度为 5,000 字符
    text: str = Field(..., max_length=5000, description="Input text to audit")

    @validator('text')
    def prevent_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v


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


# 将单条引用的处理逻辑提取为一个独立的异步函数
async def process_single_citation(cit) -> AuditResult:
    print(f"--- Auditing: {cit.title} ---")

    # 1. OpenAlex 查询 (await)
    oa_result = await search_paper_on_openalex(cit.title, cit.author)

    best_result = oa_result
    source_name = "OpenAlex"

    # 检查年份
    cit_year = get_clean_year(cit.year)
    oa_year = get_clean_year(oa_result.get("year"))
    is_oa_year_match = (cit_year == oa_year) if (cit_year and oa_year) else True

    # 2. 竞优逻辑
    if not oa_result["found"] or (oa_result["found"] and not is_oa_year_match):
        # Semantic Scholar 查询 (await)
        s2_result = await search_paper_on_semantic_scholar(cit.title, cit.author)

        if s2_result["found"]:
            s2_year = get_clean_year(s2_result.get("year"))
            is_s2_year_match = (cit_year == s2_year) if (cit_year and s2_year) else True

            if not oa_result["found"]:
                best_result = s2_result
                source_name = "Semantic Scholar"
            elif not is_oa_year_match and is_s2_year_match:
                best_result = s2_result
                source_name = "Semantic Scholar"

    # 3. 执行审计
    if best_result["found"]:
        # Content Check (await)
        consistency_check = await verify_content_consistency(
            user_claim=cit.summary_intent + " " + " ".join(cit.specific_claims),
            real_abstract=best_result.get("abstract", "")
        )

        final_status = consistency_check.get("status", "REAL")
        explanation = consistency_check.get("reason", "Verification passed.")

        db_year = get_clean_year(best_result.get("year"))
        if final_status == "REAL" and len(cit_year) == 4 and len(db_year) == 4:
            if cit_year != db_year:
                if int(db_year) > int(cit_year):
                    explanation += f" (Note: Database lists a later version from {db_year})."
                else:
                    final_status = "MINOR_ERROR"
                    explanation += f" Note: Year mismatch (Cited: {cit_year}, DB: {db_year})."

        return AuditResult(
            citation_text=cit.raw_text,
            status=final_status,
            source=source_name,
            confidence=consistency_check.get("confidence", 1.0),
            metadata=best_result,
            message=f"Citation found. Content Audit: {final_status} - {explanation}"
        )

    else:
        # 4. Google Search 兜底 (await)
        gs_result = await verify_with_google_search(cit.title, cit.author, cit.summary_intent)

        status_map = {"REAL": "REAL", "FAKE": "FAKE", "MISMATCH": "MISMATCH", "UNVERIFIED": "UNVERIFIED"}
        g_status = status_map.get(gs_result.get("verdict"), "UNVERIFIED")

        return AuditResult(
            citation_text=cit.raw_text,
            status=g_status,
            source="Google Search",
            confidence=gs_result.get("confidence", 0.0),
            metadata={"reason": gs_result.get("reason"), "info": gs_result.get("actual_paper_info")},
            message=f"Not found in academic databases. Google Search verdict: {g_status} - {gs_result.get('reason')}"
        )


# 主接口
@app.post("/api/audit", response_model=List[AuditResult])
@limiter.limit("10/minute")
async def audit_citations(request: Request, body: AuditRequest):
    # 提取引用
    citations = extract_citations_from_text(body.text)

    # 安全熔断
    MAX_CITATIONS = 10
    if len(citations) > MAX_CITATIONS:
        citations = citations[:MAX_CITATIONS]
        print(f"⚠️ Truncated citations to {MAX_CITATIONS} for safety.")

    # 并发执行所有引用的核查任务
    # 使用 asyncio.gather 同时启动所有任务
    results = await asyncio.gather(*[process_single_citation(cit) for cit in citations])

    return results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)