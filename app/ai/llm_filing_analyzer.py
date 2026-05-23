import json
from openai import OpenAI
from loguru import logger
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI()


def analyze_filing_with_llm(text):

    try:

        prompt = f"""
You are a stock market filing analyst.

Analyze this NSE/BSE corporate filing carefully.

Return ONLY valid JSON.

Required JSON format:

{{
    "summary_points": [
        "point 1",
        "point 2"
    ],
    "sentiment": "Positive/Negative/Neutral",
    "importance": 1,
    "market_impact": "short impact",
    "key_event": "main event type"
}}

Rules:
- Importance should be between 1 to 10
- Keep summary points very short
- Focus only on market moving information
- Ignore compliance boilerplate text
- Ignore generic legal wording

Corporate Filing:
{text[:12000]}
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content

        parsed = json.loads(content)

        return parsed

    except Exception as e:

        logger.error(
            f"LLM Filing Analysis Failed: {e}"
        )

        raise e