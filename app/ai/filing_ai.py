from textwrap import shorten

SIGNAL_PATTERNS = {

    "dividend": {
        "keywords": [
            "dividend",
            "interim dividend",
            "final dividend"
        ],
        "message": "Company announced dividend for shareholders.",
        "sentiment": "Positive",
        "importance": 6
    },

    "audit_clean": {
        "keywords": [
            "unmodified opinion",
            "clean audit",
            "auditors provided"
        ],
        "message": "Auditors provided clean audit opinion.",
        "sentiment": "Positive",
        "importance": 5
    },

    "expansion": {
        "keywords": [
            "expansion",
            "capacity expansion",
            "new plant",
            "increase capacity"
        ],
        "message": "Company announced business expansion plans.",
        "sentiment": "Positive",
        "importance": 8
    },

    "investment": {
        "keywords": [
            "investment",
            "capex",
            "capital expenditure"
        ],
        "message": "Company plans major investment/capex.",
        "sentiment": "Positive",
        "importance": 8
    },

    "order": {
        "keywords": [
            "order",
            "contract",
            "work order"
        ],
        "message": "Company received business order/contracts.",
        "sentiment": "Positive",
        "importance": 7
    },

    "resignation": {
        "keywords": [
            "resignation",
            "stepped down",
            "ceased to be"
        ],
        "message": "Management/KMP resignation detected.",
        "sentiment": "Negative",
        "importance": 7
    },

    "loss": {
        "keywords": [
            "net loss",
            "decline in profit",
            "loss"
        ],
        "message": "Possible weak financial performance detected.",
        "sentiment": "Negative",
        "importance": 8
    },

    "management_appointment": {
        "keywords": [
    "appointment of managing director",
    "appointed as chief executive officer",
    "appointed as ceo",
    "chief financial officer",
    "whole-time director",
    "executive director"
],
        "message": "Important management/director appointment detected.",
        "sentiment": "Positive",
        "importance": 6
    },

    "fundraising": {
        "keywords": [
            "qip",
            "rights issue",
            "preferential issue",
            "fund raise",
            "warrant"
        ],
        "message": "Company plans fundraising activity.",
        "sentiment": "Neutral",
        "importance": 8
    },

    "acquisition": {
        "keywords": [
            "acquisition",
            "stake purchase",
            "acquire",
            "merger"
        ],
        "message": "Company announced acquisition/investment activity.",
        "sentiment": "Positive",
        "importance": 9
    },

    "capacity": {
        "keywords": [
            "increase capacity",
            "capacity enhancement",
            "production capacity"
        ],
        "message": "Company expanding operational capacity.",
        "sentiment": "Positive",
        "importance": 8
    },

    "debt": {
        "keywords": [
            "default",
            "debt",
            "insolvency",
            "nclt"
        ],
        "message": "Potential financial/debt-related stress detected.",
        "sentiment": "Negative",
        "importance": 10
    }
}


def ai_summarize_event(
    symbol,
    company,
    combined_text
):

    text = combined_text.lower()

    summary_points = []

    sentiment = "Neutral"

    detected_importance = 0

    # ==========================================
    # SIGNAL ENGINE
    # ==========================================

    for signal_name, config in SIGNAL_PATTERNS.items():

        keywords = config["keywords"]

        if any(keyword in text for keyword in keywords):
            summary_points.append(
                config["message"]
                )

            signal_sentiment = config["sentiment"]

            if signal_sentiment == "Negative":
                sentiment = "Negative"

            elif (
                signal_sentiment == "Positive"
                and sentiment != "Negative"
            ):
                sentiment = "Positive"

            detected_importance = max(
                detected_importance,
                config["importance"]
            )

    # ==========================================
    # FINAL AI STYLE RESPONSE
    # ==========================================

    if not summary_points:

        summary_points.append(
            shorten(combined_text, width=300)
        )

    return {
        "symbol": symbol,
        "company": company,
        "sentiment": sentiment,
        "summary": summary_points
    }