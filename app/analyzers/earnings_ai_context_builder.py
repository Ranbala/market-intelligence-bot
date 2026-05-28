PERIOD_DISPLAY_NAMES = {
    "quarter_current": "Current quarter",
    "quarter_previous": "Previous quarter",
    "quarter_previous_year": "Same quarter previous year",
    "year_current": "Current full year",
    "year_previous": "Previous full year",
}


METRIC_DISPLAY_NAMES = {
    "revenue": "Revenue from operations",
    "total_income": "Total income",
    "profit_before_tax": "Profit before tax",
    "profit_after_tax": "Profit after tax",
    "finance_cost": "Finance cost",
    "eps": "EPS",
    "ebitda": "EBITDA",
}


COMPANY_SUFFIX_KEYWORDS = [
    " limited",
    " ltd",
    " corporation",
]


COMPANY_EXCLUDE_KEYWORDS = [
    "national stock exchange",
    "bombay stock exchange",
    "bse ltd",
    "nse",
    "listing department",
    "regd office",
    "registered office",
    "cin",
]


def format_amount(value, unit):

    if value is None:
        return "N/A"

    unit_name = (
        unit or {}
    ).get(
        "display_unit",
        "reported units"
    )

    return f"{value} {unit_name}"


def format_growth(value):

    if value is None:
        return "N/A"

    sign = "+" if value > 0 else ""

    return f"{sign}{value}%"


def calculate_pct_change(current, previous):

    try:
        if current is None or previous in [None, 0]:
            return None

        return round(
            ((current - previous) / previous) * 100,
            2
        )

    except Exception:
        return None


def format_profit_change(current, previous):

    if current is None or previous is None:
        return None

    if current < 0 and previous < 0:
        if previous == 0:
            return None

        change = round(
            ((abs(previous) - abs(current)) / abs(previous)) * 100,
            2
        )
        label = (
            "loss narrowed"
            if change >= 0
            else "loss widened"
        )
        return f"{label} by {format_growth(abs(change))}"

    if current >= 0 and previous < 0:
        return "turned profitable from a loss"

    if current < 0 and previous >= 0:
        return "turned loss-making from profit"

    pct_change = calculate_pct_change(
        current,
        previous
    )

    if pct_change is None:
        return None

    return format_growth(pct_change)


def extract_company_name(smart_text):

    for line in (smart_text or "").splitlines():

        clean_line = " ".join(
            line.strip().split()
        )

        if len(clean_line) < 8:
            continue

        line_lower = clean_line.lower()

        if any(
            keyword in line_lower
            for keyword in COMPANY_EXCLUDE_KEYWORDS
        ):
            continue

        if any(
            keyword in line_lower
            for keyword in COMPANY_SUFFIX_KEYWORDS
        ):
            return clean_line.title()

    return "Unknown"


def format_metric_block(metric_name, metric_data, unit):

    if not metric_data:
        return ""

    if not metric_data.get("period_mapping_complete"):
        return (
            f"{METRIC_DISPLAY_NAMES.get(metric_name, metric_name)}: "
            "not reliable enough for period-wise extraction"
        )

    period_values = metric_data.get(
        "period_values",
        {}
    )

    metric_title = METRIC_DISPLAY_NAMES.get(
        metric_name,
        metric_name.replace("_", " ").title()
    )

    lines = [
        f"{metric_title}:"
    ]

    for period_key, period_name in PERIOD_DISPLAY_NAMES.items():

        if period_key not in period_values:
            continue

        lines.append(
            f"- {period_name}: "
            f"{format_amount(period_values[period_key], unit)}"
        )

    return "\n".join(lines)


def format_metric_comparison(metric_name, metric_data):

    if (
        not metric_data
        or not metric_data.get("period_mapping_complete")
    ):
        return ""

    period_values = metric_data.get(
        "period_values",
        {}
    )

    metric_title = METRIC_DISPLAY_NAMES.get(
        metric_name,
        metric_name.replace("_", " ").title()
    )

    current_quarter = period_values.get(
        "quarter_current"
    )
    previous_quarter = period_values.get(
        "quarter_previous"
    )
    previous_year_quarter = period_values.get(
        "quarter_previous_year"
    )
    current_year = period_values.get(
        "year_current"
    )
    previous_year = period_values.get(
        "year_previous"
    )

    comparison_lines = []

    if metric_name in [
        "profit_after_tax",
        "profit_before_tax",
    ]:
        qoq_change = format_profit_change(
            current_quarter,
            previous_quarter
        )
        quarter_yoy_change = format_profit_change(
            current_quarter,
            previous_year_quarter
        )
        full_year_yoy_change = format_profit_change(
            current_year,
            previous_year
        )
    else:
        qoq_pct = calculate_pct_change(
            current_quarter,
            previous_quarter
        )
        quarter_yoy_pct = calculate_pct_change(
            current_quarter,
            previous_year_quarter
        )
        full_year_yoy_pct = calculate_pct_change(
            current_year,
            previous_year
        )
        qoq_change = (
            format_growth(qoq_pct)
            if qoq_pct is not None
            else None
        )
        quarter_yoy_change = (
            format_growth(quarter_yoy_pct)
            if quarter_yoy_pct is not None
            else None
        )
        full_year_yoy_change = (
            format_growth(full_year_yoy_pct)
            if full_year_yoy_pct is not None
            else None
        )

    if qoq_change is not None:
        comparison_lines.append(
            f"- Latest quarter QoQ change: {qoq_change} "
            "(current quarter vs previous quarter)"
        )

    if quarter_yoy_change is not None:
        comparison_lines.append(
            f"- Latest quarter YoY change: {quarter_yoy_change} "
            "(current quarter vs same quarter previous year)"
        )

    if full_year_yoy_change is not None:
        comparison_lines.append(
            f"- Full-year YoY change: {full_year_yoy_change} "
            "(current full year vs previous full year)"
        )

    if not comparison_lines:
        return ""

    return "\n".join([
        f"{metric_title}:",
        *comparison_lines,
    ])


def extract_compact_notes(smart_text):

    note_lines = []
    capture_notes = False

    for line in (smart_text or "").splitlines():

        clean_line = " ".join(
            line.strip().split()
        )

        if not clean_line:
            continue

        if clean_line == "IMPORTANT NOTES:":
            capture_notes = True
            continue

        if capture_notes:
            clean_lower = clean_line.lower()

            if (
                "before tax" in clean_lower
                or "before fax" in clean_lower
                or "profit/ (loss)" in clean_lower
                or "profit/ (lins)" in clean_lower
            ):
                continue

            note_lines.append(clean_line)

    return note_lines[:8]


def build_earnings_ai_context(
    smart_text,
    structured_context
):

    structured_context = structured_context or {}

    financial_unit = structured_context.get(
        "financial_unit",
        {}
    )

    financial_metrics = structured_context.get(
        "financial_metrics",
        {}
    )

    financial_insights = structured_context.get(
        "financial_insights",
        {}
    )

    filing_type = structured_context.get(
        "filing_type",
        {}
    )

    company_name = (
        structured_context.get("company_name")
        or structured_context.get(
            "filing_analysis",
            {}
        ).get("company_name")
        or extract_company_name(smart_text)
    )

    lines = [
        "NSE/BSE EARNINGS / FINANCIAL RESULTS FILING - COMPACT AI CONTEXT",
        "",
        f"Company: {company_name}",
        f"Filing type: {filing_type.get('filing_type', 'earnings')}",
        (
            "Financial unit from PDF: "
            f"{financial_unit.get('display_unit', 'reported units')}"
        ),
        (
            "Unit source line: "
            f"{financial_unit.get('source_line') or 'not found'}"
        ),
        "",
        "Period labels:",
    ]

    for period_key, period_name in PERIOD_DISPLAY_NAMES.items():
        lines.append(
            f"- {period_key}: {period_name}"
        )

    lines.extend([
        "",
        "Extracted financial metrics:",
    ])

    for metric_name in [
        "revenue",
        "total_income",
        "profit_before_tax",
        "profit_after_tax",
        "finance_cost",
        "ebitda",
    ]:

        metric_block = format_metric_block(
            metric_name,
            financial_metrics.get(metric_name),
            financial_unit
        )

        if metric_block:
            lines.extend([
                "",
                metric_block,
            ])

    lines.extend([
        "",
        "Calculated insights:",
        (
            "- Full-year revenue YoY growth: "
            f"{format_growth(financial_insights.get('revenue_growth_pct'))}"
        ),
    ])

    if financial_insights.get("pat_loss_narrowed_pct") is not None:
        pat_loss_change = financial_insights.get(
            "pat_loss_narrowed_pct"
        )
        loss_label = (
            "narrowed"
            if pat_loss_change >= 0
            else "widened"
        )
        lines.append(
            f"- Full-year PAT loss {loss_label} YoY: "
            f"{format_growth(pat_loss_change)}"
        )
    elif financial_insights.get("pat_turnaround_from_loss"):
        lines.append(
            "- Full-year PAT turned profitable from a loss last year"
        )
    elif financial_insights.get("pat_declined_to_loss"):
        lines.append(
            "- Full-year PAT declined from profit to loss"
        )
    else:
        lines.append(
            "- Full-year PAT YoY growth: "
            f"{format_growth(financial_insights.get('pat_growth_pct'))}"
        )

    comparison_blocks = []

    for metric_name in [
        "revenue",
        "profit_after_tax",
        "profit_before_tax",
        "finance_cost",
        "ebitda",
    ]:

        comparison_block = format_metric_comparison(
            metric_name,
            financial_metrics.get(metric_name)
        )

        if comparison_block:
            comparison_blocks.append(
                comparison_block
            )

    if comparison_blocks:
        lines.extend([
            "",
            "Comparison guide for AI summary:",
            "Use these exact comparison meanings. Do not mix QoQ and YoY.",
        ])

        for comparison_block in comparison_blocks:
            lines.extend([
                "",
                comparison_block,
            ])

    compact_notes = extract_compact_notes(
        smart_text
    )

    if compact_notes:
        lines.extend([
            "",
            "Important notes from PDF:",
        ])

        lines.extend(
            compact_notes
        )

    lines.extend([
        "",
        "Interpretation instructions:",
        "- Use the financial unit above exactly.",
        "- Do not convert lakh/crore/million units.",
        "- Copy numeric amounts exactly as provided in this context.",
        "- Do not add Indian comma formatting or change digit grouping in amounts.",
        "- Do not confuse current quarter values with full-year values.",
        "- QoQ means quarter_current compared with quarter_previous.",
        "- Latest quarter YoY means quarter_current compared with quarter_previous_year.",
        "- Full-year YoY means year_current compared with year_previous.",
        "- Never call quarter_previous a year-ago value; it is only the previous quarter.",
        "- When comparing finance cost, say whether it is QoQ, latest-quarter YoY, or full-year YoY.",
        "- If a metric says not reliable enough for period-wise extraction, do not summarize that metric as a confirmed number.",
        "- Do not mention dividend unless the context explicitly says dividend declared, dividend not declared, or no dividend.",
        "- Do not mention EPS unless EPS is provided as a reliable extracted metric.",
        "- If full-year PAT is negative in both years, describe it as loss narrowed or loss widened, not PAT growth.",
        "- Use simple retail-investor language: result improved, result weakened, latest quarter profit/loss, full-year growth/decline, and likely short-term market reaction.",
        "- If current quarter PAT is negative but full-year PAT is positive, say latest quarter was loss-making but full year was profitable.",
        "- For a plain earnings filing with no order, acquisition, dividend, fund raise, or major corporate action, importance is usually 4 to 6.",
        "- Use importance 7 or higher only if there is a strong positive rerating trigger, major turnaround, large profit growth, or major corporate action.",
        "- If full-year PAT fell sharply, avoid high importance unless another major trigger is present.",
    ])

    return "\n".join(lines)
