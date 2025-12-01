import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


def verify_with_google_search(title: str, author: str, claim_summary: str) -> dict:
    """
    使用 REST API 直接调用 Gemini 2.0 Flash + Google Search。
    包含：碎片拼接 + 智能 JSON 提取 (解决重复输出问题)。
    """

    # ⬇️⬇️⬇️ 关键修正：确保这里是纯净的 URL 字符串，没有 [] 或 () ⬇️⬇️⬇️
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    # ⬆️⬆️⬆️ 关键修正 ⬆️⬆️⬆️

    prompt = f"""
    You are an academic auditor. Your goal is to verify if a specific paper exists using Google Search.

    Target Paper:
    - Title: "{title}"
    - Author: "{author}"

    User's Summary of the paper:
    "{claim_summary}"

    INSTRUCTIONS:
    1. Use Google Search to find this paper.
    2. If you cannot find a paper with this SPECIFIC title and author, mark it as FAKE.
    3. If you find it, compare the real abstract/content with the User's Summary.

    Output JSON format:
    {{
        "verdict": "REAL" | "FAKE" | "MISMATCH",
        "confidence": 0.0 to 1.0,
        "reason": "Brief explanation citing what you found on Google.",
        "actual_paper_info": "Title and Author if found, else null"
    }}

    IMPORTANT: 
    - You MUST output valid JSON.
    - Do not output markdown code blocks (```json), just the raw JSON string.
    """

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "tools": [
            {"google_search": {}}
        ],
        "generationConfig": {
            "response_mime_type": "application/json"
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"[Google Search API Error] Status: {response.status_code}")
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
        if finish_reason == 'SAFETY':
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "reason": "Content blocked by safety filters.",
                "actual_paper_info": None
            }

        # === 核心解析逻辑 ===
        try:
            parts = candidate['content']['parts']
            # 1. 拼接碎片
            raw_text = "".join([part.get('text', '') for part in parts])

            # 清洗 Markdown 标记
            text_content = re.sub(r'^```[a-z]*', '', raw_text.strip(), flags=re.MULTILINE | re.IGNORECASE)
            text_content = re.sub(r'```$', '', text_content.strip(), flags=re.MULTILINE)
            text_content = text_content.strip()

            # 2. 智能截取第一个 JSON 对象
            start_idx = text_content.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found (missing '{')")

            decoder = json.JSONDecoder()
            parsed_json, _ = decoder.raw_decode(text_content, idx=start_idx)

            return parsed_json

        except Exception as e:
            print(
                f"[Google Search Parse Error] Failed to parse. Raw Text: {raw_text if 'raw_text' in locals() else 'Unknown'}")
            return {
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "reason": f"Failed to parse AI response: {str(e)}",
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