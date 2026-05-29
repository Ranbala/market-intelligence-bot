import re


FINANCIAL_RESULT_POSITIVE_KEYWORDS = {
    "financial results": 12,
    "flnanclal results": 12,
    "statement or financial results": 12,
    "statement of flnanclal results": 12,
    "audited standalone financial results": 18,
    "unaudited standalone financial results": 18,
    "audited consolidated financial results": 20,
    "unaudited consolidated financial results": 20,
    "revenue from operations": 12,
    "revenue rrom operations": 12,
    "re'lenue rrom operations": 12,
    "revc¡uc": 10,
    "iìcr cnuc": 10,
    "profit/ (loss) after tax": 12,
    "profit / (loss) after tax": 12,
    "profit after tax": 10,
    "profit before tax": 8,
    "net profit for the period": 10,
    "net prom lor lhe period": 10,
    "nef profit": 10,
    "nel profit": 10,
    "profit/lloss": 8,
    "total income": 8,
    "fntnl ¡ncon": 8,
    "lì)trl income": 8,
    "finance costs": 6,
    "earnings per equity share": 8,
    "segment revenue": 10,
    "cash flow from operating": 9,
    "statement of cash flow": 8,
    "dividend": 6,
    "unmodified opinion": 8,
    "outcome of board meeting": 8,
    "notes": 4,
}


FINANCIAL_RESULT_NEGATIVE_KEYWORDS = {
    "independent auditor": 12,
    "auditor's responsibilities": 12,
    "auditors' responsibilities": 12,
    "annexure": 10,
    "companies auditor": 10,
    "caro": 10,
    "internal financial controls": 10,
    "section 143": 8,
    "audit procedures": 8,
    "proper books of account": 8,
    "true and fair view": 7,
    "reasonable assurance": 7,
}


IMPORTANT_NOTE_KEYWORDS = [
    "dividend",
    "debt",
    "default",
    "recovered",
    "bad debt",
    "bad debts",
    "exceptional",
    "unmodified opinion",
    "modified opinion",
    "qualified opinion",
    "resignation",
    "subsidiary",
    "associate",
    "joint venture",
    "material uncertainty",
    "going concern",
]


MAX_RESULT_PAGES = 10
MAX_NOTE_LINES = 12


def get_page_analysis_text(page):

    text = page.get("text", "") or ""
    layout_text = page.get("layout_text", "") or ""

    if not layout_text.strip():
        return text

    return (
        text.strip()
        + "\n\nLAYOUT TABLE TEXT:\n"
        + layout_text.strip()
    )


FINANCIAL_UNIT_PATTERNS = [
    {
        "unit": "crores",
        "display_unit": "Rs. crore",
        "scale": 10000000,
        "patterns": [
            r"rs\.?\s*in\s*crores?",
            r"in\s*rs\.?\s*crores?",
            r"rupees\s*in\s*crores?",
            r"inr\s*in\s*crores?",
            r"amount\s*in\s*crores?",
            r"figures\s*in\s*crores?",
            r"\bin\s*crores?\b",
        ],
    },
    {
        "unit": "lakhs",
        "display_unit": "Rs. lakh",
        "scale": 100000,
        "patterns": [
            r"rs\.?\s*in\s*lakhs?",
            r"rs\.?\s*in\s*lacs?",
            r"in\s*rs\.?\s*lakhs?",
            r"in\s*rs\.?\s*lacs?",
            r"rs\.?\s*_?\s*in\s*lakhs?",
            r"rs\.?\s*_?\s*in\s*lacs?",
            r"rupees\s*in\s*lakhs?",
            r"rupees\s*in\s*lacs?",
            r"inr\s*in\s*lakhs?",
            r"inr\s*in\s*lacs?",
            r"amount\s*in\s*lakhs?",
            r"amount\s*in\s*lacs?",
            r"figures\s*in\s*lakhs?",
            r"figures\s*in\s*lacs?",
            r"\bin\s*lakhs?\b",
            r"\bin\s*lacs?\b",
        ],
    },
    {
        "unit": "millions",
        "display_unit": "Rs. million",
        "scale": 1000000,
        "patterns": [
            r"rs\.?\s*in\s*millions?",
            r"in\s*rs\.?\s*millions?",
            r"rupees\s*in\s*millions?",
            r"inr\s*in\s*millions?",
            r"amount\s*in\s*millions?",
            r"figures\s*in\s*millions?",
            r"\bin\s*millions?\b",
        ],
    },
]


def score_financial_result_page(page_text):

    text_lower = (page_text or "").lower()

    positive_score = sum(
        score
        for keyword, score in FINANCIAL_RESULT_POSITIVE_KEYWORDS.items()
        if keyword in text_lower
    )

    negative_score = sum(
        score
        for keyword, score in FINANCIAL_RESULT_NEGATIVE_KEYWORDS.items()
        if keyword in text_lower
    )

    return positive_score - negative_score


def is_table_shaped_financial_result_page(page_text):

    text_lower = (page_text or "").lower()

    has_period_headers = (
        "quarter ended" in text_lower
        and "year ended" in text_lower
    )

    has_unit_line = any(
        marker in text_lower
        for marker in [
            "rs. in lakh",
            "rs in lakh",
            "rs. in lakhs",
            "rs in lakhs",
            "rs. in crore",
            "rs in crore",
            "rs. in million",
            "rs in million",
            "inr in million",
            "in lakhs",
            "in lacs",
        ]
    )

    has_result_row = any(
        marker in text_lower
        for marker in [
            "revenue from operations",
            "revenue rrom operations",
            "re'lenue rrom operations",
            "total income",
            "profit before tax",
            "net profit",
            "net prom",
            "earnings per equity share",
        ]
    )

    has_statement_title = any(
        marker in text_lower
        for marker in [
            "statement of financial results",
            "statement or financial results",
            "statement of flnanclal results",
            "statement or flnanclal results",
        ]
    )

    return (
        has_period_headers
        and has_unit_line
        and has_result_row
        and (
            has_statement_title
            or "particulars" in text_lower
        )
    )


def is_likely_financial_results_pdf(pages):

    if not pages:
        return False

    combined_text = "\n".join(
        get_page_analysis_text(page)
        for page in pages[:8]
    ).lower()

    if (
        "financial results" in combined_text
        and (
            "quarter ended" in combined_text
            or "year ended" in combined_text
            or "revenue from operations" in combined_text
        )
    ):
        return True

    for page in pages:
        page_text = get_page_analysis_text(page).lower()
        if (
            "revenue from operations" in page_text
            and "profit" in page_text
            and (
                "quarter ended" in page_text
                or "year ended" in page_text
            )
        ):
            return True

    return False


def select_financial_result_pages(pages):

    scored_pages = []

    for page in pages:

        score = score_financial_result_page(
            get_page_analysis_text(page)
        )

        if score <= 0 and not is_table_shaped_financial_result_page(
            get_page_analysis_text(page)
        ):
            continue

        if score <= 0:
            score = 15

        scored_pages.append({
            "page_no": page.get("page_no"),
            "score": score,
            "text": page.get("text", ""),
            "analysis_text": get_page_analysis_text(page),
        })

    scored_pages.sort(
        key=lambda page: (
            -page["score"],
            page["page_no"] or 0
        )
    )

    selected_pages = scored_pages[:MAX_RESULT_PAGES]

    selected_pages.sort(
        key=lambda page: page["page_no"] or 0
    )

    return selected_pages


def detect_financial_unit_from_text(text):

    best_candidate = None
    best_score = -1

    for line in (text or "").splitlines():

        clean_line = " ".join(
            line.strip().split()
        )

        if not clean_line:
            continue

        line_lower = clean_line.lower()

        for unit_config in FINANCIAL_UNIT_PATTERNS:

            for pattern in unit_config["patterns"]:

                if re.search(pattern, line_lower):
                    score = 1

                    if any(
                        marker in line_lower
                        for marker in [
                            "unless otherwise stated",
                            "except per share",
                            "except per share data",
                        ]
                    ):
                        score += 50

                    if re.search(
                        r"^\(?\s*(rs\.?|rupees|inr|in\s+rs\.?)",
                        line_lower
                    ):
                        score += 10

                    if any(
                        marker in line_lower
                        for marker in [
                            "financial results",
                            "statement of",
                            "particulars",
                        ]
                    ):
                        score += 5

                    candidate = {
                        "currency": "INR",
                        "unit": unit_config["unit"],
                        "display_unit": unit_config["display_unit"],
                        "scale": unit_config["scale"],
                        "source_line": clean_line,
                    }

                    if score > best_score:
                        best_candidate = candidate
                        best_score = score

                    break

    if best_candidate:
        return best_candidate

    return {
        "currency": "INR",
        "unit": "unknown",
        "display_unit": "reported units",
        "scale": None,
        "source_line": None,
    }


def detect_financial_unit_from_pages(pages):

    selected_pages = select_financial_result_pages(
        pages
    )

    selected_text = "\n".join(
        page.get("analysis_text", page.get("text", ""))
        for page in selected_pages
    )

    return detect_financial_unit_from_text(
        selected_text
    )


def extract_important_financial_notes(pages):

    important_lines = []
    seen_lines = set()

    for page in pages:

        for line in page.get("text", "").splitlines():

            clean_line = " ".join(
                line.strip().split()
            )

            if len(clean_line) < 25:
                continue

            line_lower = clean_line.lower()

            if clean_line in seen_lines:
                continue

            if any(
                keyword in line_lower
                for keyword in IMPORTANT_NOTE_KEYWORDS
            ):
                important_lines.append(
                    clean_line
                )
                seen_lines.add(clean_line)

            if len(important_lines) >= MAX_NOTE_LINES:
                return important_lines

    return important_lines


def extract_financial_result_text_from_pages(pages):

    if not pages:
        return ""

    selected_pages = select_financial_result_pages(
        pages
    )

    if not selected_pages:
        return ""

    final_sections = []

    for page in selected_pages:

        header = (
            f"--- PDF PAGE {page['page_no']} "
            f"| RESULT PAGE SCORE {page['score']} ---"
        )

        final_sections.append(
            f"{header}\n"
            f"{page.get('analysis_text', page['text']).strip()}"
        )

    important_notes = extract_important_financial_notes(
        selected_pages
    )

    if important_notes:
        final_sections.append(
            "IMPORTANT NOTES:\n"
            + "\n".join(
                f"- {note}"
                for note in important_notes
            )
        )

    return "\n\n".join(final_sections)
