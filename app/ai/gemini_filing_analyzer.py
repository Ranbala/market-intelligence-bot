import os
import json

import google.generativeai as genai

from loguru import logger


genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)


def analyze_filing_with_gemini(text):

    prompt = f"""
    You are an expert Indian stock market analyst.

    Analyze this NSE/BSE corporate filing and tell summary points in easy english.

    Return STRICT JSON only.

    Required JSON format:

    {{
        "summary_points": [
            "point1",
            "point2"
        ],
        "sentiment": "Positive/Negative/Neutral",
        "importance": 1-10,
        "market_impact": "Short market impact",
        "key_event": "Main event type"
    }}

    Filing Text:
    {text[:12000]}
    """

    response = model.generate_content(prompt)

    result = response.text

    return json.loads(result)