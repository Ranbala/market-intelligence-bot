import json
from loguru import logger

from ai.cerebras_filing_analyzer import (
    analyze_filing_with_cerebras
)

from ai.openrouter_filing_analyzer import (
    analyze_filing_with_openrouter
)

from ai.groq_filing_analyzer import (
    analyze_filing_with_groq
)

from ai.gemini_filing_analyzer import (
    analyze_filing_with_gemini
)

DEBUG_PRINT_AI_TEXT = False
DEBUG_PRINT_AI_SIZE = True


def estimate_tokens(text):

    return round(
        len(text or "") / 4
    )


# =========================================================
# MAIN ROUTER
# =========================================================

def analyze_filing_with_llm(text,structured_context=None):

    if DEBUG_PRINT_AI_SIZE:

        context_text = json.dumps(
            structured_context,
            default=str
        )

        logger.info(
            "AI input size | "
            f"text_chars={len(text or '')} | "
            f"text_est_tokens={estimate_tokens(text)} | "
            f"context_est_tokens={estimate_tokens(context_text)} | "
            f"total_est_tokens="
            f"{estimate_tokens(text) + estimate_tokens(context_text)}"
        )

    if DEBUG_PRINT_AI_TEXT:

        print("\n" + "="*100)
        #print("TEXT SENT TO AI")
        print("="*100)

        print(text[:30000])

    cerebras_error = None
    openrouter_error = None
    groq_error = None
    gemini_error = None

    # =====================================================
    # TRY CEREBRAS FIRST
    # =====================================================

    try:

        logger.info(
            "🧠 Trying Cerebras..."
        )

        return analyze_filing_with_cerebras(
            text,structured_context
        )

    except Exception as e:

        cerebras_error = e

        logger.error(
            f"Cerebras Failed: {e}"
        )

    # =====================================================
    # TRY GROQ
    # =====================================================

    try:

        logger.info(
            "⚡ Trying GROQ..."
        )

        return analyze_filing_with_groq(
            text,structured_context
        )

    except Exception as e:

        groq_error = e

        logger.error(
            f"GROQ Failed: {e}"
        )

    # =====================================================
    # TRY OPENROUTER
    # =====================================================

    try:

        logger.info(
            "🛰️ Trying OpenRouter..."
        )

        return analyze_filing_with_openrouter(
            text,structured_context
        )

    except Exception as e:

        openrouter_error = e

        logger.error(
            f"OpenRouter Failed: {e}"
        )

    # =====================================================
    # TRY GEMINI
    # =====================================================

    try:

        logger.info(
            "🌌 Trying Gemini..."
        )

        return analyze_filing_with_gemini(
            text,structured_context
        )

    except Exception as e:

        gemini_error = e

        logger.error(
            f"Gemini Failed: {e}"
        )

    # =====================================================
    # FINAL RULE-BASED FALLBACK
    # =====================================================

    logger.warning(
        "🛟 Falling back to rule-based engine..."
    )

    fallback_importance = 5
    fallback_sentiment = "Neutral"
    fallback_key_event = "Corporate Filing"

    text_lower = text.lower()
    structured_context = structured_context or {}
    filing_type = (
        structured_context
        .get("filing_type", {})
        .get("filing_type")
    )
    financial_metrics = structured_context.get(
        "financial_metrics",
        {}
    )

    if (
        filing_type == "earnings"
        or "financial results" in text_lower
    ):
        fallback_importance = 5
        fallback_sentiment = "Neutral"
        fallback_key_event = "Financial results filing"

        if financial_metrics:
            fallback_importance = 6

    if "dividend" in text_lower:
        fallback_importance = max(
            fallback_importance,
            8
        )
        fallback_sentiment = "Positive"
        fallback_key_event = "Dividend-related filing"

    if (
        filing_type in ["acquisition", "open_offer"]
        or "open offer" in text_lower
        or "change of control" in text_lower
        or "acquisition" in text_lower
    ):
        fallback_importance = max(
            fallback_importance,
            9
        )
        fallback_sentiment = "Positive"
        fallback_key_event = "Acquisition / open offer filing"

    if (
        "board meeting" in text_lower
        and filing_type not in ["earnings", "acquisition", "open_offer"]
    ):
        fallback_importance = max(
            fallback_importance,
            7
        )
        fallback_key_event = "Board meeting outcome"

    if "qip" in text_lower:
        fallback_importance = max(
            fallback_importance,
            8
        )
        fallback_sentiment = "Positive"
        fallback_key_event = "Fund raising filing"

    if "cirp" in text_lower:
        fallback_importance = max(
            fallback_importance,
            9
        )
        fallback_sentiment = "Negative"
        fallback_key_event = "CIRP / insolvency filing"

    return {
        "summary_points": [
            "Fallback rule-based analysis used."
        ],
        "sentiment": fallback_sentiment,
        "importance": fallback_importance,
        "market_impact": (
            "Important filing detected via "
            "rule-based engine."
        ),
        "key_event": fallback_key_event
    }
