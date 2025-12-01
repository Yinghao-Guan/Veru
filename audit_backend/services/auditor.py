import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def verify_content_consistency(user_claim: str, real_abstract: str) -> dict:
    if not real_abstract or len(real_abstract) < 20:
        return {
            "status": "UNVERIFIED",
            "confidence": 0.5,
            "reason": "Paper exists, but abstract is missing in database."
        }

    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    You are an expert academic auditor.

    Task:
    Compare the "User's Claim" about a paper against the "Actual Abstract".
    Determine if the User's Claim is a valid description of the paper.

    User's Claim: "{user_claim}"
    Actual Abstract: "{real_abstract}"

    CRITICAL INSTRUCTIONS:
    1. **Terminology Mapping**: Users often use community nicknames (e.g., "Luong Attention") that may not appear in the abstract. 
       - If the abstract describes the *mechanism* (e.g., "global and local attention", "multiplicative scoring"), and the user uses the *author's name* (e.g., "Luong attention"), this is a MATCH.
    2. **Meta-Descriptions**: Claims like "Foundational paper on X" are REAL if the abstract introduces X.
    3. **Language**: Conceptually translate if languages differ.

    Decision Logic:
    - **REAL**: The claim accurately describes the paper's topic/contribution.
    - **MISMATCH**: The claim describes a completely different topic.
    - **SUSPICIOUS**: The claim invents specific fake data (e.g. "p < 0.001") not supported by the text.

    Output JSON:
    {{
        "status": "REAL" | "MISMATCH" | "SUSPICIOUS",
        "confidence": 0.0 to 1.0,
        "reason": "Brief explanation in English."
    }}
    """

    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        return {
            "status": "ERROR",
            "confidence": 0.0,
            "reason": f"Audit Error: {str(e)}"
        }