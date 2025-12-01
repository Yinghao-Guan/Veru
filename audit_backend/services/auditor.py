import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def verify_content_consistency(user_claim: str, real_abstract: str) -> dict:
    """
    Layer 2 Audit: 检查 AI 生成的总结是否与真实摘要一致。
    """
    # 如果没有摘要，无法进行第二层审计
    if not real_abstract or len(real_abstract) < 20:
        return {
            "status": "UNVERIFIED",
            "confidence": 0.5,
            "reason": "文献存在，但数据库缺少摘要，无法自动验证内容一致性。"
        }

    model = genai.GenerativeModel('gemini-2.0-flash')

    # === 升级版 Prompt ===
    prompt = f"""
    You are an expert academic auditor.

    Task:
    Compare the "User's Claim" about a paper against the "Actual Abstract".
    Determine if the User's Claim is a valid description of the paper.

    User's Claim (what the user SAYS the paper is about):
    "{user_claim}"

    Actual Abstract (ground truth):
    "{real_abstract}"

    CRITICAL INSTRUCTIONS:
    1. **Language Barrier**: The User's Claim might be in a different language (e.g., Chinese). You MUST conceptually translate it to English before comparing.
    2. **Meta-Descriptions**: The user might describe the *function* of the paper (e.g., "This is a review of basic emotion theory" or "Discusses evidence"). If the abstract *contains* that theory or evidence, this is a MATCH. 
    3. **Generalization**: The user claim is often a high-level summary. If it captures the *gist* or *main topic* of the abstract, mark it as REAL. Do not be pedantic about specific keywords missing.

    Decision Logic:
    - **REAL**: The claim accurately describes the paper's topic, conclusion, or nature (even if simplified or translated).
    - **MISMATCH**: The claim describes a DIFFERENT topic entirely (e.g., Claim says "cooking", Abstract says "robotics").
    - **SUSPICIOUS**: The claim invents specific data (e.g., "p < 0.05") that is NOT in the abstract.

    Output JSON:
    {{
        "status": "REAL" | "MISMATCH" | "SUSPICIOUS",
        "confidence": 0.0 to 1.0,
        "reason": "Explain your reasoning in one sentence."
    }}
    """

    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        result = json.loads(response.text)
        return result
    except Exception as e:
        return {
            "status": "ERROR",
            "confidence": 0.0,
            "reason": f"Audit Error: {str(e)}"
        }