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

def analyze_filing_with_groq(text,structured_context=None):

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

Use STRUCTURED EXTRACTED DATA as highest priority source.
Use SMART EXTRACTED FILING TEXT for additional context and understanding.

Financial-result rules:
- Use financial_unit.display_unit exactly for all extracted financial amounts.
- Do not assume crore, lakh, million, or any other unit if financial_unit is provided.
- Do not convert lakhs to crores or crores to lakhs unless explicitly asked.
- Copy numeric amounts exactly from STRUCTURED EXTRACTED DATA or compact context.
- Do not add Indian comma formatting or change digit grouping in amounts.
- If financial_unit.unit is unknown, write amounts as "in reported units".
- Treat period_values.year_current and period_values.year_previous as full-year numbers.
- Treat period_values.quarter_current as only the latest quarter, not the full year.
- Treat period_values.quarter_previous as the previous quarter only, not year-ago data.
- Treat period_values.quarter_previous_year as the same quarter in the previous year.
- QoQ comparison = quarter_current vs quarter_previous.
- Latest-quarter YoY comparison = quarter_current vs quarter_previous_year.
- Full-year YoY comparison = year_current vs year_previous.
- Never write "from a year ago" when using quarter_previous; use "from the previous quarter" instead.
- For finance cost, always state whether the comparison is QoQ, latest-quarter YoY, or full-year YoY.
- Do not say the company made a full-year loss if year_current profit_after_tax is positive.
- If quarter_current profit_after_tax is negative but year_current profit_after_tax is positive, say latest quarter was loss-making but full year was profitable.
- If full-year PAT is negative in both years, describe it as loss narrowed or loss widened, not PAT growth.
- When explaining growth, use financial_insights and clearly mention YoY/full-year when relevant.
- Do not mention dividend unless the extracted context explicitly says dividend declared, dividend not declared, or no dividend.
- Do not mention EPS unless EPS is provided as a reliable extracted metric.
- Write summary_points in very simple retail-investor language with concrete numbers first.
- For plain earnings filings with no order, acquisition, dividend, fund raise, or major corporate action, importance is usually 4 to 6.
- Use importance 7 or higher for earnings only when there is a strong rerating trigger, major turnaround, large profit growth, or major corporate action.

Acquisition/open-offer rules:
- If the filing mentions open offer, takeover regulations, large stake sale, acquirer/purchaser, or change of control, treat it as highly market-sensitive.
- Do not confuse option/balance shares stake with open offer size.
- If control changes and an open offer is triggered, sentiment should usually be Positive unless the deal price is below market price or negative conditions are disclosed.
- For Indian traders, strategic acquisition/change of control/open offer can create strong speculative buying and upper-circuit behavior.
- Importance should usually be 8 to 10 for change-of-control/open-offer filings.
- Promoter selling alone can be negative, but promoter selling to a strategic acquirer with open offer/change of control is usually a bullish/speculative market trigger.

STRUCTURED EXTRACTED DATA:
{json.dumps(structured_context, indent=2)}

SMART EXTRACTED FILING TEXT:
{text[:30000]}
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
