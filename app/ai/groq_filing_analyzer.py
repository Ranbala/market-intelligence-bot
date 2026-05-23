import os
import json

from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

# =========================================================
# GROQ CLIENT
# =========================================================

groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

GROQ_MODEL = "openai/gpt-oss-20b"

# =========================================================
# GROQ ANALYZER
# =========================================================

def analyze_filing_with_groq(text):

    prompt = f"""
You are an expert Indian stock market filing analysis AI.

Analyze this NSE/BSE corporate filing and explain it in very simple Easy English majorly.

The reader is a normal retail investor, not a finance expert.

Focus on:
- what happened
- why it matters
- whether it is positive or negative
- possible market reaction
- risks if any

Avoid legal and corporate jargon.

Rate importance based on:
- probability of stock movement
- business impact
- future earnings impact
- market excitement potential

Also consider how Indian stock market traders and short-term investors may react emotionally to the news.

Even if fundamentals are mixed, events like:
- acquisitions
- expansion
- preferential allotments
- large business deals
- strategic partnerships

can create strong bullish market interest.

Importance score should reflect potential stock price movement, not just accounting impact.

Think like a smart Indian stock market trader.
If the filing can create hype, momentum, operator interest, speculative buying, rerating potential, or future growth expectations, sentiment and importance should reflect that.

Return ONLY valid JSON.

Do not add explanations.
Do not add markdown.
Do not add extra text.
Always include ALL fields:
- company_name
- summary_points
- sentiment
- importance
- market_impact
- key_event

importance must be between 1 and 10.

Format:
{{
    "company_name": "company full name",
    "summary_points": [
        "point1",
        "point2"
    ],
    "sentiment": "Positive/Negative/Neutral",
    "importance": 8,
    "market_impact": "short impact",
    "key_event": "main event"
}}

FILING:
{text[:12000]}
"""

    response = groq_client.responses.create(
        model=GROQ_MODEL,
        input=prompt
    )

    result = response.output_text

    json_match = re.search(
        r"\{.*\}",
        result,
        re.DOTALL
        )

    if json_match:
        cleaned_json = json_match.group(0)
        return json.loads(cleaned_json)

    raise Exception("No valid JSON returned from GROQ")