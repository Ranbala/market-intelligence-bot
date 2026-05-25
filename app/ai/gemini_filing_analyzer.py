import os
import json
from google import genai
from openai import OpenAI

from loguru import logger

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

GEMINI_MODEL = "gemini-3.5-flash"


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
    {text[:6000]}
    """

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    result = response.text
    return json.loads(result)