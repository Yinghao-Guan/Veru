import os
import json
import re
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional, Union
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class CitationData(BaseModel):
    id: int
    raw_text: str
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[str] = None  # 虽然这里定义是 str，但我们在下面代码里会强制转换
    summary_intent: str
    specific_claims: List[str] = []


def extract_citations_from_text(text: str) -> List[CitationData]:
    print(f"\n[Debug] 正在让 Gemini 提取文本: {text[:50]}...")
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    You are a forensic text auditor. 
    Analyze the text and extract ALL academic papers mentioned.

    CRITICAL INSTRUCTION - ANTI-HALLUCINATION:
    1. Extract the summary and claims EXACTLY AS WRITTEN in the text.
    2. DO NOT correct the text using your internal knowledge. 
    3. If the text says "ResNet is used for cooking spaghetti", you MUST extract "cooking spaghetti" as the summary.
    4. Your job is to capture the User's potential lies/errors verbatim.

    For each paper mentioned:
    1. raw_text: The specific substring.
    2. title: Extract the likely title.
    3. author: Extract the likely author.
    4. year: Extract year if mentioned, else null.
    5. summary_intent: What does the TEXT claim this paper is about? (Verbatim extraction).
    6. specific_claims: Extract specific facts/methodologies attributed to this paper.

    Output ONLY valid JSON list:
    [
        {{
            "id": 1,
            "raw_text": "...",
            "title": "...",
            "author": "...",
            "year": "2023", 
            "summary_intent": "...",
            "specific_claims": []
        }}
    ]

    Input Text:
    {text}
    """

    try:
        response = model.generate_content(prompt)
        raw_content = response.text

        # 清洗逻辑
        clean_json = raw_content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        results = []
        for idx, item in enumerate(data):
            item['id'] = idx + 1

            # 容错处理
            if not item.get('raw_text'):
                item['raw_text'] = item.get('title', 'Unknown Reference')
            if 'specific_claims' not in item or item['specific_claims'] is None:
                item['specific_claims'] = []

            # === 关键修复：类型强制转换 ===
            # 无论 Gemini 返回的是 int 1992 还是 str "1992"，都转成 str
            if 'year' in item and item['year'] is not None:
                item['year'] = str(item['year'])

            results.append(CitationData(**item))

        print(f"[Debug] 成功提取到 {len(results)} 条引用")
        return results

    except Exception as e:
        print(f"[ERROR] 提取失败: {e}")
        return []