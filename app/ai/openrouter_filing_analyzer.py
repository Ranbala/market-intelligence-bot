import os
import json
import re
import time

import requests
from dotenv import (
    find_dotenv,
    load_dotenv
)


load_dotenv(
    find_dotenv()
)

# =========================================================
# OPENROUTER SETUP
# =========================================================

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS = [
    "deepseek/deepseek-v4-flash:free",
    "openai/gpt-oss-20b:free",
    "z-ai/glm-4.5-air:free",
    "nvidia/nemotron-3-super:free",
]


class OpenRouterRateLimitError(Exception):
    pass


def build_openrouter_error(response):

    try:
        error_json = response.json().get(
            "error",
            {}
        )
        message = error_json.get(
            "message",
            "OpenRouter request failed"
        )
        metadata = error_json.get(
            "metadata",
            {}
        )
        raw_message = metadata.get(
            "raw",
            ""
        )
        provider_name = metadata.get(
            "provider_name",
            ""
        )

        error_parts = [
            f"OpenRouter HTTP {response.status_code}",
            message,
        ]

        if provider_name:
            error_parts.append(
                f"provider={provider_name}"
            )

        if raw_message:
            error_parts.append(
                raw_message
            )

        return " | ".join(error_parts)

    except Exception:
        return (
            f"OpenRouter HTTP {response.status_code}: "
            f"{response.text[:300]}"
        )


# =========================================================
# ANALYZER
# =========================================================

def analyze_filing_with_openrouter(text, structured_context=None):

    api_key = (
        os.getenv("OPEN_ROUTER_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )

    if not api_key:
        raise Exception(
            "OpenRouter API key missing. Add OPEN_ROUTER_API_KEY "
            "to .env, or use OPENROUTER_API_KEY as an alias."
        )

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

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-OpenRouter-Title": "Market Intelligence Bot",
    }

    last_error = None

    for model in OPENROUTER_MODELS:

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 4000
        }

        for attempt in range(2):
            try:
                response = requests.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=(10, 90)
                )

                if response.status_code == 429:
                    raise OpenRouterRateLimitError(
                        build_openrouter_error(response)
                    )

                if response.status_code >= 400:
                    raise Exception(
                        build_openrouter_error(response)
                    )

                response_json = response.json()
                result = (
                    response_json
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )

                json_match = re.search(
                    r"\{.*\}",
                    result,
                    re.DOTALL
                )

                if json_match:
                    cleaned_json = json_match.group(0)
                    return json.loads(cleaned_json)

                raise Exception(
                    "No valid JSON returned from OpenRouter"
                )

            except OpenRouterRateLimitError as e:
                last_error = e
                print(
                    "OpenRouter model rate-limited, "
                    f"trying next model | model={model} | {e}"
                )
                break

            except Exception as e:
                last_error = e
                print(
                    f"OpenRouter model failed | model={model} | "
                    f"attempt={attempt + 1} | {e}"
                )
                time.sleep(2)

    raise last_error
