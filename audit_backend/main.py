from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# 引入服务
from services.llm_extractor import extract_citations_from_text
from services.openalex import search_paper_on_openalex
from services.auditor import verify_content_consistency
# from services.perplexity import verify_with_perplexity_fallback  <-- 删除这行
from services.google_search import verify_with_google_search  # <-- 新增这行

app = FastAPI(title="Realibuddy Audit Engine")

# 允许跨域
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


@app.post("/api/audit", response_model=List[AuditResult])
def audit_citations(request: AuditRequest):
    # Phase 1: 提取
    citations = extract_citations_from_text(request.text)

    results = []

    # Phase 2 & 3: 循环审计
    for cit in citations:
        print(f"--- 审计文献: {cit.title} ---")

        # === 路径 A: 查 OpenAlex ===
        oa_result = search_paper_on_openalex(cit.title, cit.author)

        if oa_result["found"]:
            print(f"✅ OpenAlex 找到文献 (ID: {oa_result['id']})")

            # === Phase 3: 内容一致性核查 (Layer 2 Audit) ===
            print("正在进行内容比对...")
            consistency_check = verify_content_consistency(
                user_claim=cit.summary_intent + " " + " ".join(cit.specific_claims),
                real_abstract=oa_result.get("abstract", "")
            )

            final_status = consistency_check.get("status", "REAL")
            explanation = consistency_check.get("reason", "验证通过")

            result = AuditResult(
                citation_text=cit.raw_text,
                status=final_status,
                source="OpenAlex",
                confidence=consistency_check.get("confidence", 1.0),
                metadata=oa_result,
                message=f"文献存在。内容核查: {final_status} - {explanation}"
            )

        else:
            # === 路径 B: Google Search (Gemini) 兜底 ===
            # 原来的 Perplexity 逻辑替换为 Google Search
            print("❌ OpenAlex 未找到，切换 Google Search...")

            gs_result = verify_with_google_search(
                cit.title,
                cit.author,
                cit.summary_intent
            )

            # 映射状态
            status_map = {
                "REAL": "REAL",
                "FAKE": "FAKE",
                "MISMATCH": "MISMATCH",  # Google Search 也可以返回 MISMATCH
                "UNVERIFIED": "UNVERIFIED"
            }

            g_status = status_map.get(gs_result.get("verdict"), "UNVERIFIED")

            result = AuditResult(
                citation_text=cit.raw_text,
                status=g_status,
                source="Google Search",  # 来源变了
                confidence=gs_result.get("confidence", 0.0),
                metadata={"reason": gs_result.get("reason"), "info": gs_result.get("actual_paper_info")},
                message=f"数据库未收录。Google 搜索判定: {g_status} - {gs_result.get('reason')}"
            )

        results.append(result)

    return results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)