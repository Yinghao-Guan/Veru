import os
import json
import re
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional, Union
from dotenv import load_dotenv
import time
import google.api_core.exceptions

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class CitationData(BaseModel):
    id: int
    raw_text: str
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[str] = None
    doi: Optional[str] = None
    summary_intent: str
    specific_claims: List[str] = []


def generate_with_retry(model, prompt):
    max_attempts = 2  # 1 次失败 + 1 次重试
    for attempt in range(max_attempts):
        try:
            return model.generate_content(prompt)

        except google.api_core.exceptions.ResourceExhausted:
            # 属于 Vertex AI 的 429 Resource Exhausted
            if attempt == max_attempts - 1:
                raise  # 最后一次失败 → 抛出

            wait = 2 ** attempt  # 第一次失败等待 1s
            print(f"[WARN] 429 Resource Exhausted. {wait}s 后重试第 {attempt + 2} 次调用...")
            time.sleep(wait)

        except Exception:
            raise  # 其他错误不属于可重试范围，直接抛出


def extract_citations_from_text(text: str) -> List[CitationData]:
    print(f"\n[Debug] 正在让 Gemini 提取文本: {text[:50]}...")
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
        You are a forensic text auditor. 
        Analyze the text and extract ALL academic papers mentioned.

        CRITICAL INSTRUCTION - ANTI-HALLUCINATION:
        1. Extract the summary and claims EXACTLY AS WRITTEN.
        2. DO NOT correct user errors.

        For each paper mentioned:
        1. raw_text: The specific substring.
        2. title: Extract the likely title.
        3. author: Extract the likely author.
        4. year: Extract year if mentioned (string), else null.
        5. doi: Extract DOI if explicitly mentioned (e.g. "10.1038/s41586..."), else null.  <--- [新增]
        6. summary_intent: What does the TEXT claim this paper is about?
        7. specific_claims: Extract specific facts attributed to this paper.

        Output ONLY valid JSON list:
        [
            {{
                "id": 1,
                "raw_text": "...",
                "title": "...",
                "author": "...",
                "year": "2023",
                "doi": "10.xxxx/...", 
                "summary_intent": "...",
                "specific_claims": []
            }}
        ]

        Input Text:
        {text}
    """

    try:
        response = generate_with_retry(model, prompt)
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

            # 类型强制转换 - 无论 Gemini 返回的是 int 1992 还是 str "1992"，都转成 str
            if 'year' in item and item['year'] is not None:
                item['year'] = str(item['year'])

            results.append(CitationData(**item))

        print(f"[Debug] 成功提取到 {len(results)} 条引用")
        return results

    except Exception as e:
        print(f"[ERROR] 提取失败: {e}")
        return []