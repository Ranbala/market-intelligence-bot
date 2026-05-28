import re


def normalize_whitespace(text):

    return " ".join(
        (text or "").split()
    )


def first_match(text, patterns, flags=re.IGNORECASE):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags
        )

        if match:
            return match.group(1).strip()

    return None


def extract_company_name(text):

    return first_match(
        text,
        [
            r"Board of Directors of\s+([A-Za-z0-9&.,' \-]+?Limited)",
            r"of\s+([A-Za-z0-9&.,' \-]+?Limited)\s+at its meeting",
            r"Target Company.*?([A-Za-z0-9&.,' \-]+?Limited)",
        ]
    )


def extract_purchaser(text):

    return first_match(
        text,
        [
            r"with\s+([A-Za-z0-9&.,' \-]+?Limited)\s+\(“Purchaser”\)",
            r"with\s+([A-Za-z0-9&.,' \-]+?Limited)\s+\(\"Purchaser\"\)",
            r"Details of the counterparties.*?([A-Za-z0-9&.,' \-]+?Limited)",
            r"Purchaser[^\n.]*?([A-Za-z0-9&.,' \-]+?Limited)",
        ]
    )


def extract_spa_date(text):

    return first_match(
        text,
        [
            r"Share Purchase Agreement dated\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"Date of entering into the agreement\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        ]
    )


def extract_price_per_share(text):

    return first_match(
        text,
        [
            r"INR\s*([0-9,.]+)\s*/-\s*\([^)]*\)\s*per equity share",
            r"INR\s*([0-9,.]+)\s*per Equity Share",
            r"₹\s*([0-9,.]+)\s*per Equity Share",
            r"price of\s+₹\s*([0-9,.]+)\s*per Equity Share",
        ]
    )


def extract_open_offer_pct(text):

    return first_match(
        text,
        [
            r"open offer.*?representing up to\s+([0-9.]+)%",
            r"open offer.*?up to\s+([0-9.]+)%[^.]{0,250}equity share capital",
            r"representing up to\s+([0-9.]+)%[^.]{0,250}total paid up equity share capital",
        ]
    )


def extract_initial_stake_pct(text):

    return first_match(
        text,
        [
            r"equivalent to\s+([0-9.]+)%\s+of the total paid up share capital",
            r"sell\s+[0-9,]+\s+fully paid up equity shares.*?equivalent to\s+([0-9.]+)%",
            r"acquisition of\s+([0-9.]+)%\s+by the Purchaser",
        ]
    )


def extract_total_stake_pct(text):

    return first_match(
        text,
        [
            r"up to\s+[0-9,]+\s+equity\s+shares\s+representing\s+([0-9.]+)%\s+of the paid-up equity share capital",
            r"sale and transfer of up to\s+[0-9,]+\s+equity\s+shares\s+representing\s+([0-9.]+)%",
        ]
    )


def extract_option_stake_pct(text):

    return first_match(
        text,
        [
            r"Balance Shares.*?being up to.*?which represent\s+([0-9.]+)%\s+of the equity share capital",
            r"comprising\s+([0-9.]+)%\s+of the issued and outstanding equity share capital[^.]{0,160}Balance Shares",
            r"Option Shares[^.]{0,220}?represent\s+([0-9.]+)%\s+of the equity share capital",
        ]
    )


def extract_share_count_near(text, marker):

    pattern = (
        r"([0-9]{1,3}(?:,[0-9]{2,3})+)\s+"
        r"(?:fully paid up\s+)?equity shares[^.]{0,180}"
        + marker
    )

    return first_match(
        text,
        [pattern]
    )


def contains_any(text, keywords):

    text_lower = text.lower()

    return any(
        keyword in text_lower
        for keyword in keywords
    )


def build_acquisition_ai_context(text, structured_context=None):

    structured_context = structured_context or {}
    clean_text = normalize_whitespace(text)

    company_name = (
        structured_context.get("company_name")
        or extract_company_name(clean_text)
        or "Unknown"
    )

    purchaser = (
        extract_purchaser(clean_text)
        or "Unknown"
    )

    spa_date = extract_spa_date(clean_text) or "Unknown"
    price_per_share = extract_price_per_share(clean_text)
    open_offer_pct = extract_open_offer_pct(clean_text)
    initial_stake_pct = extract_initial_stake_pct(clean_text)
    total_stake_pct = extract_total_stake_pct(clean_text)
    option_stake_pct = extract_option_stake_pct(clean_text)

    control_change = contains_any(
        clean_text,
        [
            "transfer of control",
            "acquire control",
            "change in control",
            "shall acquire control",
        ]
    )

    new_promoter = contains_any(
        clean_text,
        [
            "classified as part of the promoter",
            "categorized as a promoter",
            "promoter/promoter group",
        ]
    )

    open_offer_trigger = contains_any(
        clean_text,
        [
            "open offer",
            "takeover regulations",
            "substantial acquisition",
        ]
    )

    lines = [
        "NSE/BSE ACQUISITION / OPEN OFFER FILING - COMPACT AI CONTEXT",
        "",
        f"Company: {company_name}",
        f"Purchaser / acquirer: {purchaser}",
        f"SPA date: {spa_date}",
        "",
        "Extracted transaction fields:",
        f"- Initial stake sale: {initial_stake_pct or 'not found'}%",
        f"- Total possible SPA stake: {total_stake_pct or 'not found'}%",
        f"- Option / balance shares stake: {option_stake_pct or 'not found'}%",
        f"- Open offer size: {open_offer_pct or 'not found'}%",
        f"- Price per share: INR {price_per_share or 'not found'}",
        f"- Change of control: {control_change}",
        f"- Purchaser becomes promoter/promoter group: {new_promoter}",
        f"- Open offer / takeover trigger: {open_offer_trigger}",
        "",
        "Critical interpretation rules:",
        "- Do not confuse option/balance shares stake with open offer size.",
        "- Option/balance shares and open offer are separate transaction parts.",
        "- A large stake sale plus open offer plus change of control is highly market-sensitive in Indian markets.",
        "- If offer/acquisition price is disclosed, traders may compare it with market price and treat it as an open-offer/rerating trigger.",
        "- Promoter selling can look negative legally, but strategic acquisition/change of control/open offer is often bullish/speculative for short-term traders.",
        "- If control changes and an open offer is triggered, sentiment should usually be Positive unless deal price is below market price or negative conditions are disclosed.",
        "- Importance should usually be 8 to 10 for change-of-control/open-offer filings.",
        "",
        "Important evidence snippets:",
    ]

    for snippet in [
        "Share Purchase Agreement",
        "open offer",
        "transfer of control",
        "acquire control",
        "classified as part of the promoter",
        "INR 299",
    ]:

        match = re.search(
            r"(.{0,160}" + re.escape(snippet) + r".{0,220})",
            clean_text,
            re.IGNORECASE
        )

        if match:
            lines.append(
                f"- {match.group(1).strip()}"
            )

    return "\n".join(lines)
