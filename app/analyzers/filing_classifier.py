FILING_TYPE_KEYWORDS = {

    "earnings": [
        "financial results",
        "audited financial results",
        "unaudited financial results",
        "revenue from operations",
        "profit after tax",
        "ebitda",
        "quarter ended",
        "quarter and year ended",
        "audited results",
        "unaudited results",
        "cash flow",
        "eps"
    ],

    "open_offer": [
        "open offer",
        "substantial acquisition",
        "takeovers regulations",
        "expanded voting share capital",
        "public shareholders",
        "acquirer",
        "offer price",
        "change in control"
    ],

    "acquisition": [
        "acquisition",
        "acquire",
        "stake purchase",
        "purchase agreement",
        "subsidiary acquisition",
        "merger",
        "strategic investment"
    ],

    "order_win": [
        "order",
        "contract",
        "purchase order",
        "work order",
        "letter of award",
        "loi",
        "deal worth"
    ],

    "dividend": [
        "dividend",
        "record date",
        "interim dividend",
        "final dividend"
    ],

    "bonus": [
        "bonus issue",
        "bonus shares"
    ],

    "split": [
        "stock split",
        "face value split",
        "sub-division"
    ],

    "rights_issue": [
        "rights issue",
        "rights entitlement"
    ],

    "board_meeting": [
        "board meeting",
        "outcome of board meeting"
    ],

    "resignation": [
        "resignation",
        "ceased to be",
        "independent director"
    ]
}


def classify_filing(text):

    if not text:
        return {
            "filing_type": "unknown",
            "confidence": 0
        }

    text_lower = text.lower()

    filing_scores = {}

    for filing_type, keywords in FILING_TYPE_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in text_lower:
                score += 1

        filing_scores[filing_type] = score

    best_match = max(
        filing_scores,
        key=filing_scores.get
    )

    confidence = filing_scores[best_match]

    if confidence == 0:
        best_match = "unknown"

    return {
        "filing_type": best_match,
        "confidence": confidence,
        "all_scores": filing_scores
    }
