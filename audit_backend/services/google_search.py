import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


async def verify_with_google_search(title: str, author: str, claim_summary: str) -> dict:
    """
    使用 Gemini 2.0 Flash + Google Search 进行全网核查。
    优化点：使用 JSON Schema 强制结构化输出。
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    # Prompt 可以更加专注于“思考逻辑”，而不用操心“格式”
    prompt = f"""
    You are an academic auditor. Verify if this specific paper exists using Google Search.

    Target Paper:
    - Title: "{title}"
    - Author: "{author}"

    User's Claim/Summary:
    "{claim_summary}"

    INSTRUCTIONS:
    1. Use Google Search to find this paper.
    2. If you cannot find a paper with this SPECIFIC title and author, verdict is "FAKE".
    3. If found, compare the real abstract with the User's Claim.
       - If the claim completely misrepresents the content (e.g. wrong topic), verdict is "MISMATCH".
       - If accurate, verdict is "REAL".
    4. Provide a confidence score (0.0 - 1.0).
    """

    # 定义严格的 JSON Schema
    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "verdict": {
                    "type": "STRING",
                    "enum": ["REAL", "FAKE", "MISMATCH", "UNVERIFIED"]
                },
                "confidence": {
                    "type": "NUMBER"
                },
                "reason": {
                    "type": "STRING"
                },
                "actual_paper_info": {
                    "type": "STRING",
                    "nullable": True
                }
            },
            "required": ["verdict", "confidence", "reason"]
        }
    }

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "tools": [
            {"google_search": {}}
        ],
        "generationConfig": generation_config,
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        # 使用异步请求
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"[Google Search API Error] Status: {response.status_code} - {response.text}")
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "reason": f"API Error {response.status_code}",
                "actual_paper_info": None
            }

        result = response.json()

        if 'candidates' not in result or not result['candidates']:
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "reason": "No response candidates from AI",
                "actual_paper_info": None
            }

        candidate = result['candidates'][0]
        finish_reason = candidate.get('finishReason')

        # 安全过滤器拦截
        if finish_reason == 'SAFETY':
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "reason": "Content blocked by safety filters.",
                "actual_paper_info": None
            }

        # 解析
        try:
            parts = candidate['content']['parts']
            raw_text = "".join([part.get('text', '') for part in parts])

            # 因为指定了 response_schema，Gemini 保证返回的是合法的 JSON 字符串
            parsed_json = json.loads(raw_text)
            return parsed_json

        except json.JSONDecodeError as e:
            print(f"[Google Search Parse Error] JSON Decode Failed: {raw_text}")
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "reason": "Failed to parse AI response (JSON Error)",
                "actual_paper_info": None
            }

    except Exception as e:
        print(f"[Google Search Exception] {e}")
        return {
            "verdict": "UNVERIFIED",
            "confidence": 0.0,
            "reason": f"Internal Error: {str(e)}",
            "actual_paper_info": None
        }