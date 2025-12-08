import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


async def verify_content_consistency(user_claim: str, real_abstract: str) -> dict:
    """
    使用 Gemini 2.0 Flash 对比用户声称的内容与真实摘要。
    - 异步调用 (Async)
    - 强制 JSON Schema 输出 (Stability)
    - 增强针对“数据捏造”的检测逻辑 (Anti-Hallucination)
    """

    # 基础防守：如果没有摘要，无法验证
    if not real_abstract or len(real_abstract) < 20:
        return {
            "status": "UNVERIFIED",
            "confidence": 0.5,
            "reason": "Paper exists, but abstract is missing in database."
        }

    model = genai.GenerativeModel('gemini-2.0-flash')

    # Prompt 逻辑增强
    prompt = f"""
    You are a forensic academic auditor. 
    Your Task: Verify if the "User's Claim" is supported by the "Actual Abstract".

    User's Claim: "{user_claim}"
    Actual Abstract: "{real_abstract}"

    AUDIT RULES:
    1. **Topic Match**: Does the paper discuss the same core topic? If no -> "MISMATCH".
    2. **Data Integrity (CRITICAL)**: 
       - If the User's Claim includes specific metrics (e.g., "95% accuracy", "p < 0.05", "300 participants") that are NOT in the abstract, mark as "SUSPICIOUS".
       - Do not assume these numbers exist in the full text unless the abstract strongly implies them.
    3. **Terminology**: Allow for synonyms (e.g., "Global Attention" matching "Luong Attention" is OK).
    4. **Language**: Ignore language differences (e.g., Chinese claim vs English abstract is OK if meaning matches).

    VERDICT DEFINITIONS:
    - "REAL": The claim accurately reflects the abstract's content.
    - "MISMATCH": The paper is about a completely different topic (e.g., Biology paper cited for AI).
    - "SUSPICIOUS": The topic matches, but the user invented specific details/findings not present in the text (Hallucination of details).
    - "UNVERIFIED": Abstract is too short or ambiguous to judge.

    Provide a confidence score (0.0 - 1.0) and a brief reason.
    """

    # 使用 JSON Schema 替代纯文本 Prompt 约束
    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "status": {
                    "type": "STRING",
                    "enum": ["REAL", "MISMATCH", "SUSPICIOUS", "UNVERIFIED"]
                },
                "confidence": {
                    "type": "NUMBER"
                },
                "reason": {
                    "type": "STRING"
                }
            },
            "required": ["status", "confidence", "reason"]
        }
    }

    try:
        # 使用异步方法
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config
        )

        # 直接解析 JSON
        return json.loads(response.text)

    except Exception as e:
        print(f"[Auditor Error] {e}")
        return {
            "status": "ERROR",
            "confidence": 0.0,
            "reason": f"Audit Error: {str(e)}"
        }