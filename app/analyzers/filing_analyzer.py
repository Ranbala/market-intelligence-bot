from textwrap import shorten


def analyze_filing(filing):

    symbol = filing.get("symbol", "")
    company = filing.get("sm_name", "")
    desc = filing.get("desc", "")
    details = filing.get("attchmntText", "")
    time = filing.get("an_dt", "")

    text = f"{desc} {details}".lower()

    # =====================================================
    # SENTIMENT
    # =====================================================

    sentiment = "Neutral"

    positive_keywords = [
        "dividend",
        "approval",
        "acquisition",
        "investment",
        "order",
        "profit",
        "growth",
        "expansion",
        "buyback",
        "bonus",
    ]

    negative_keywords = [
        "fraud",
        "default",
        "bankruptcy",
        "resignation",
        "loss",
        "decline",
        "insolvency",
    ]

    if any(word in text for word in positive_keywords):
        sentiment = "Positive"

    if any(word in text for word in negative_keywords):
        sentiment = "Negative"

    # =====================================================
    # IMPORTANCE SCORE
    # =====================================================

    importance_score = 5

    if any(word in text for word in [
        "acquisition",
        "merger",
        "stake",
        "buyback",
        "fraud",
        "default",
        "bankruptcy",
        "insolvency",
        "large order",
        "major order",
        "fund raise",
        "preferential",
    ]):
        importance_score = 9

    elif any(word in text for word in [
        "financial results",
        "dividend",
        "bonus",
        "split",
        "approval",
        "expansion",
    ]):
        importance_score = 7

    elif any(word in text for word in [
        "record date",
        "analyst",
        "conference call",
        "general updates",
    ]):
        importance_score = 3

    # =====================================================
    # EASY ENGLISH INTERPRETATION
    # =====================================================

    meaning = ""

    if "dividend" in text:
        meaning = (
            "The company is rewarding shareholders "
            "by distributing profits."
        )

    elif "approval" in text:
        meaning = (
            "The company received an important approval "
            "which may support future business growth."
        )

    elif "financial results" in text:
        meaning = (
            "The company announced its latest quarterly "
            "or yearly financial performance."
        )

    elif "acquisition" in text:
        meaning = (
            "The company is expanding its business "
            "by acquiring stakes or assets."
        )

    elif "order" in text:
        meaning = (
            "The company received a business order "
            "which may improve revenue."
        )

    else:
        meaning = shorten(details, width=160)

    # =====================================================
    # MARKET IMPACT
    # =====================================================

    impact = ""

    if sentiment == "Positive":
        impact = (
            "This may attract buying interest if market "
            "participants view the development positively."
        )

    elif sentiment == "Negative":
        impact = (
            "This may create selling pressure if investors "
            "react negatively."
        )

    else:
        impact = (
            "Market reaction may depend on further details "
            "and overall sentiment."
        )

    # =====================================================
    # FINAL STRUCTURE
    # =====================================================

    return {
    "symbol": symbol,
    "company": company,
    "event": desc,
    "sentiment": sentiment,
    "importance": importance_score,
    "meaning": meaning,
    "impact": impact,
    "time": time,
}