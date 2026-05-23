from ai.llm_filing_analyzer import (
    analyze_filing_with_llm as analyze_with_openai
)

from ai.groq_filing_analyzer import (
    analyze_filing_with_groq
)

from ai.gemini_filing_analyzer import (
    analyze_filing_with_gemini
)

from analyzers.filing_analyzer import (
    analyze_filing
)


def fallback_rule_based(text):

    return {
        "summary_points": [
            "Fallback rule-based analysis used."
        ],
        "sentiment": "Neutral",
        "importance": 5
    }


def analyze_filing_with_llm(text):

    # OpenAI
    try:

        print("\n🤖 Trying OpenAI...")

        return analyze_with_openai(text)

    except Exception as e:

        print(f"\n⚠️ OpenAI Failed: {e}")

    # GROQ
    try:

        print("\n⚡ Trying GROQ...")

        return analyze_filing_with_groq(text)

    except Exception as e:

        print(f"\n⚠️ GROQ Failed: {e}")

    # Gemini
    try:

        print("\n🌌 Trying Gemini...")

        return analyze_filing_with_gemini(text)

    except Exception as e:

        print(f"\n⚠️ Gemini Failed: {e}")

    # Final fallback
    print("\n🛟 Falling back to rule-based engine...")

    return fallback_rule_based(text)