LOW_VALUE_KEYWORDS = [
    "newspaper publication",
    "analyst",
    "conference call",
    "investor meet",
    "record date",
    "corrigendum",
    "postal ballot",
    "esop",
    "grant of options",

    # new additions
    "investor presentation",
    "earnings call",
    "analyst meet",
    "schedule of analysts",
    "institutional investors meet",
    "clarification",
    "audio recording",
    "transcript",
    "presentation",
    "investor interaction",
]

HIGH_IMPACT_KEYWORDS = [

    # acquisitions / expansion
    "acquisition",
    "stake",
    "merger",
    "investment",
    "joint venture",
    "order win",
    "new order",
    "contract",

    # financials
    "financial results",
    "outcome of board meeting",
    "dividend",
    "buyback",
    "bonus",
    "split",

    # approvals
    "approval",
    "rbi approval",
    "nod",
    "license",

    # fundraising
    "qip",
    "preferential",
    "fund raise",

    # operations
    "capacity expansion",
    "new plant",
    "commercial production",

    # leadership
    "ceo",
    "md",
    "chairman",

    # distress
    "default",
    "fraud",
    "insolvency",
    "bankruptcy",
    "resignation"
]


def filter_important_filings(filings):

    important = []

    for item in filings:

        text = (
            str(item.get("desc", "")) + " " +
            str(item.get("attchmntText", ""))
        ).lower()

        # ==========================================
        # SKIP LOW VALUE FILINGS
        # ==========================================
        if any(keyword in text for keyword in LOW_VALUE_KEYWORDS):
            continue
        
        # ==========================================
        # KEEP ONLY HIGH IMPACT FILINGS
        # ==========================================
        if any(keyword in text for keyword in HIGH_IMPACT_KEYWORDS):
            important.append(item)

    return important