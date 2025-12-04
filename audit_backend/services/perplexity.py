import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# --- 开发者开关 ---
# 如果没有 API Key，将其设为 True，系统会返回伪造的成功数据
MOCK_MODE = True


def verify_with_perplexity_fallback(title: str, author: str, claim_summary: str) -> dict:
    """
    当数据库查不到时，调用 Perplexity 进行全网验证。
    支持 Mock 模式以进行免费开发测试。
    """

    # Mock 模式 (开发专用)
    if MOCK_MODE or not PERPLEXITY_API_KEY:
        print(f"[Perplexity] ⚠️ MOCK MODE ACTIVATED: Simulating search for '{title}'...")
        time.sleep(1.5)  # 模拟网络延迟

        # 这里伪造一个"查到了"的结果，就像 Perplexity 真的工作了一样
        return {
            "verdict": "REAL",
            "confidence": 0.95,
            "reason": "(MOCKED) Perplexity found multiple sources confirming this paper exists and the summary is accurate.",
            "actual_paper_info": f"{title} by {author} (1999)"
        }

    # 真实 API 调用逻辑
    url = "https://api.perplexity.ai/chat/completions"

    system_prompt = """
    You are an academic auditor. You must verify if a specific academic paper exists.
    If it exists, check if the summary provided matches the paper's actual content.

    Output JSON format:
    {
        "verdict": "REAL" | "FAKE" | "HALLUCINATION",
        "confidence": 0.0 to 1.0,
        "reason": "Brief explanation",
        "actual_paper_info": "Title and Author if found, else null"
    }
    """

    user_prompt = f"""
    Verify this paper:
    Title: {title}
    Author: {author}

    The user claims the paper says: "{claim_summary}"

    Task:
    1. Search specifically for this paper.
    2. If found, does the content match the claim?
    3. If not found (or if title/author are mismatch), mark as FAKE/HALLUCINATION.
    """

    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "verdict": {"type": "string", "enum": ["REAL", "FAKE", "HALLUCINATION"]},
                        "confidence": {"type": "number"},
                        "reason": {"type": "string"},
                        "actual_paper_info": {"type": "string"}
                    },
                    "required": ["verdict", "confidence", "reason"]
                }
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            # 如果 API 报错（如 401），也可以在这里做一个 fallback，防止前端炸裂
            return {"verdict": "ERROR", "reason": f"API Error {response.text}"}

        result = response.json()
        content = result['choices'][0]['message']['content']
        return json.loads(content)

    except Exception as e:
        return {"verdict": "ERROR", "reason": str(e)}