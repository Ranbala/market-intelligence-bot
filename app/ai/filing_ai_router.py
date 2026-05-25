import json
from loguru import logger

from ai.cerebras_filing_analyzer import (
    analyze_filing_with_cerebras
)

from ai.groq_filing_analyzer import (
    analyze_filing_with_groq
)

from ai.gemini_filing_analyzer import (
    analyze_filing_with_gemini
)


# =========================================================
# MAIN ROUTER
# =========================================================

def analyze_filing_with_llm(text):

    cerebras_error = None
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
            text
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
            text
        )

    except Exception as e:

        groq_error = e

        logger.error(
            f"GROQ Failed: {e}"
        )

    # =====================================================
    # TRY GEMINI
    # =====================================================

    try:

        logger.info(
            "🌌 Trying Gemini..."
        )

        return analyze_filing_with_gemini(
            text
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

    text_lower = text.lower()

    if "financial results" in text_lower:
        fallback_importance = 9
        fallback_sentiment = "Positive"

    if "dividend" in text_lower:
        fallback_importance = max(
            fallback_importance,
            8
        )

    if "acquisition" in text_lower:
        fallback_importance = max(
            fallback_importance,
            9
        )
        fallback_sentiment = "Positive"

    if "board meeting" in text_lower:
        fallback_importance = max(
            fallback_importance,
            7
        )

    if "qip" in text_lower:
        fallback_importance = max(
            fallback_importance,
            8
        )

    if "cirp" in text_lower:
        fallback_importance = max(
            fallback_importance,
            9
        )
        fallback_sentiment = "Negative"

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
        "key_event": "Corporate Filing"
    }