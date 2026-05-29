import re

from collections import defaultdict


FINANCIAL_METRIC_PATTERNS = {

    "revenue": [
        "total revenue from operation",
        "total revenue from operations",
        "revenue from operations",
        "revenue rrom operations",
        "re'lenue rrom operations",
        "revenue o operations",
        "rt venue from operations",
        "venue from operations",
        "revc¡uc",
        "revenue lir",
        "iìcr cnuc",
        "rìcr cnuc",
    ],

    "total_income": [
        "total income",
        "total tncome",
        "tol•i income",
        "tola i income",
        "fntnl ¡ncon",
        "lì)trl income",
        "trl income",
    ],

    "profit_before_tax": [
        "pront before tax",
        "profit before tax",
        "profit/lloss",
        "profit/fl.nssl",
        "profit/loss",
        "prqfit before",
        "pr fit before",
        "puofit before tax",
        "profit/ (loss) before tax",
        "profit/ (los) before tax",
        "profit/ (lins) before fax",
        "before fax",
        "profit before exceptional",
    ],

    "profit_after_tax": [
        "profit for the period",
        "profit for the period / year",
        "profit for the period/ year",
        "profit for the period/year",
        "profit/(loss) for the period",
        "profit / (loss) for the period",
        "profit/ (loss) for the period after taxes",
        "profit / (loss) for the period after taxes",
        "profit for the year",
        "net profit/(loss)",
        "net profit / (loss)",
        "profit/ (loss) after tax",
        "profit/ (los) after tax",
        "profit/ (lins) after tax",
        "profit/ (ss) for the year",
        "not profit after tax",
        "net prom lor lhe period",
        "net profit for the period",
        "nef profit",
        "nel profit",
        "profit/lloss",
        "profit/fl,oss",
        "profit/loss",
        "profit after tax",
        "net profit",
    ],

    "ebitda": [
        "ebitda",
    ],

    "eps": [
        "earnings per share",
        "basic eps",
        "diluted eps",
    ],

    "finance_cost": [
        "finance costs",
        "fln:jnce costs",
        "finance cost",
    ]
}


NUMBER_PATTERN = r"\d[\d,]*\.?\d*"
MAX_ROW_LOOKAHEAD_LINES = 18
MAX_VALUES_PER_METRIC_ROW = 5
MAX_RAW_VALUES_PER_METRIC_ROW = 12
FINANCIAL_RESULT_PERIOD_LABELS = [
    "quarter_current",
    "quarter_previous",
    "quarter_previous_year",
    "year_current",
    "year_previous",
]
ROW_BOUNDARY_KEYWORDS = [
    "other income",
    "total income",
    "employee benefits",
    "depreciation",
    "other expenses",
    "exceptional items",
    "total expenses",
    "net profit",
    "other comprehensive",
    "total comprehensive",
    "earnings per share",
    "other un-allocable",
    "other unallocable",
    "liabilities/provision",
    "operating profit",
    "interest income",
    "inierest income",
    "loss allowance",
    "profit/ (loss)",
    "profit/ (los)",
    "profit/ (lins)",
    "profit before tax",
    "puofit before tax",
    "less tax",
    "loss tax",
    "tax expense",
    "add profit",
    "total",
    "segment assets",
    "particulars",
    "asat",
    "as at",
]


# =========================================================
# CLEAN NUMBERS
# =========================================================


def normalize_ocr_number_line(line):

    line = line.replace("©", "(")

    def repair_ocr_numeric_token(match):

        token = match.group(0)

        if (
            not re.search(r"\d|[,◄&]", token)
            and not token.lower().startswith("ss,")
        ):
            return token

        # Very common OCR confusions inside table numbers only.
        if token.lower().startswith("ss,"):
            token = "58," + token[3:]

        replacements = {
            "S": "5",
            "s": "5",
            "I": "1",
            "l": "1",
            "◄": "4",
            "&": "8",
            "e": "6",
        }

        if any(
            char.isalpha()
            and char not in replacements
            for char in token
        ):
            return token

        repaired = "".join(
            replacements.get(char, char)
            for char in token
        )

        if re.search(r"\d", repaired):
            return repaired

        return token

    line = re.sub(
        r"(?<![A-Za-z])[A-Za-z\d,.\-◄&]{2,}(?![A-Za-z])",
        repair_ocr_numeric_token,
        line
    )
    line = re.sub(
        r"(\d[\d,]*)\s+\.(\d+)",
        r"\1.\2",
        line
    )
    # OCR sometimes reads decimal dots as hyphens:
    # "7,843-32" should be "7,843.32".
    line = re.sub(
        r"(?<=\d)-(?=\d{2}\b)",
        ".",
        line
    )
    # OCR sometimes reads Indian comma grouping as dots:
    # "37.851.52" should be "37,851.52".
    line = re.sub(
        r"(?<![\d,])(\d{1,3})\.(\d{3})\.(\d{1,2})(?!\d)",
        r"\1,\2.\3",
        line
    )
    # Same issue, but with the decimal part split by whitespace:
    # "15.682 47" should be "15,682.47".
    line = re.sub(
        r"(?<![\d,])(\d{1,3})\.(\d{3})\s+(\d{1,2})(?!\d)",
        r"\1,\2.\3",
        line
    )

    return line


def repair_decimal_token(token, decimal_present):

    if not decimal_present:
        return token

    if "." in token:
        return token

    is_negative = (
        token.startswith("(")
        and token.endswith(")")
    )
    clean_token = (
        token
        .replace("(", "")
        .replace(")", "")
    )

    if not clean_token:
        return token

    if "," in clean_token:
        comma_parts = clean_token.split(",")

        if not all(part.isdigit() for part in comma_parts):
            return token

        last_part = comma_parts[-1]

        if (
            len(comma_parts) == 3
            and len(comma_parts[0]) == 1
            and len(comma_parts[1]) == 3
            and len(comma_parts[2]) == 3
        ):
            repaired = (
                comma_parts[0]
                + comma_parts[1]
                + "."
                + comma_parts[2]
            )
        elif len(last_part) == 4:
            repaired = (
                "".join(comma_parts[:-1])
                + last_part[:3]
                + "."
                + last_part[3:]
            )
        elif len(last_part) >= 5:
            compact = "".join(comma_parts)
            repaired = (
                compact[:-2]
                + "."
                + compact[-2:]
            )
        else:
            return token
    else:
        if (
            not clean_token.isdigit()
            or len(clean_token) < 3
        ):
            return token

        repaired = (
            clean_token[:-2]
            + "."
            + clean_token[-2:]
        )

    return (
        f"({repaired})"
        if is_negative
        else repaired
    )


def normalize_financial_number(value):

    try:

        value = str(value).strip()

        if not value:
            return None

        value = value.replace("©", "(")

        is_negative = (
            value.startswith("(")
            and value.endswith(")")
        )

        unsigned_value = (
            value
            .replace("(", "")
            .replace(")", "")
        )

        if (
            "," in unsigned_value
            and "." not in unsigned_value
        ):
            comma_parts = unsigned_value.split(",")

            if (
                len(comma_parts) >= 2
                and len(comma_parts[-1]) == 2
                and all(
                    part.isdigit()
                    for part in comma_parts
                )
            ):
                value = (
                    "".join(comma_parts[:-1])
                    + "."
                    + comma_parts[-1]
                )
                if is_negative:
                    value = f"({value})"

        value = (
            value
            .replace(",", "")
            .replace("(", "")
            .replace(")", "")
        )

        number = float(value)

        if is_negative:
            number = -number

        return round(number, 2)

    except Exception:
        return None


# =========================================================
# EXTRACT NUMBERS FROM LINE
# =========================================================

def extract_numbers_from_line(line):

    line = normalize_ocr_number_line(line)

    matches = re.findall(
        r"\(?\d[\d,]*\.?\d*\)?",
        line
    )

    # =========================================================
    # DETECT DECIMAL PATTERN IN ROW
    # =========================================================

    decimal_present = any(
        "." in value
        for value in matches
    )

    cleaned_values = []

    for value in matches:

        original_value = value

        # =========================================================
        # OCR DECIMAL REPAIR
        # Only repair if row already contains decimals
        # =========================================================

        value = repair_decimal_token(
            value,
            decimal_present
        )
        # Skip percentage-only lines
        if "%" in line and len(matches) == 1:
            continue

        normalized = normalize_financial_number(
            value
        )

        if normalized is not None:
            cleaned_values.append(normalized)

    return cleaned_values


def extract_metric_value_tokens(line):

    line = normalize_ocr_number_line(line)

    token_matches = list(
        re.finditer(
            r"\(?\d[\d,]*\.?\d*\)?|(?<![\w/])-+(?![\w/])",
            line
        )
    )
    tokens = [
        match.group(0)
        for match in token_matches
    ]

    decimal_present = any(
        "." in token
        for token in tokens
        if not re.fullmatch(r"-+", token)
    )

    values = []

    for match in token_matches:

        token = match.group(0)

        if re.fullmatch(r"-+", token):
            previous_text = line[:match.start()].rstrip()
            next_text = line[match.end():].lstrip()

            if (
                previous_text
                and previous_text[-1].isalpha()
            ) or (
                next_text
                and next_text[0].isalpha()
            ):
                continue

            values.append(0.0)
            continue

        token = repair_decimal_token(
            token,
            decimal_present
        )

        normalized = normalize_financial_number(
            token
        )

        if normalized is not None:
            values.append(normalized)

    return values


def score_metric_row(metric_name, raw_line, numbers):

    if not numbers:
        return -100

    raw_lower = (raw_line or "").lower()

    score = len(numbers)

    if len(numbers) >= MAX_VALUES_PER_METRIC_ROW:
        score += 20

    if metric_name == "revenue":
        if (
            "total revenue from operations" in raw_lower
            or "total revenue from operation" in raw_lower
        ):
            score += 12
        elif (
            "revenue from operations" in raw_lower
            or "venue from operations" in raw_lower
        ):
            score += 5

    if metric_name == "profit_before_tax":
        if (
            "profit before tax" in raw_lower
            or "pront before tax" in raw_lower
        ):
            score += 8
        if "profit/ (loss)" in raw_lower:
            score += 4

    if metric_name == "profit_after_tax":
        if "attributable" in raw_lower:
            score -= 120
        if (
            (
                "net profit before" in raw_lower
                or "profit before" in raw_lower
                or re.search(
                    r"profit.{0,40}before",
                    raw_lower
                )
                or "adjustments to reconcile net profit" in raw_lower
            )
            and "after tax" not in raw_lower
            and "profit for the period" not in raw_lower
            and "profit/(loss) for the period" not in raw_lower
            and "profit / (loss) for the period" not in raw_lower
        ):
            score -= 150
        if "net profit" in raw_lower:
            score += 10
        if "net prom" in raw_lower:
            score += 10
        if "after tax" in raw_lower:
            score += 12
        if "profit for the period" in raw_lower:
            score += 8
        if "profit/ (loss) after tax" in raw_lower:
            score += 8
        if "profit for the year" in raw_lower:
            score += 5
        if (
            "net profit before" in raw_lower
            or "profit before share" in raw_lower
        ):
            score -= 40
        if (
            "return on" in raw_lower
            or "ratio" in raw_lower
            or "%" in raw_lower
        ):
            score -= 35

    if metric_name == "finance_cost":
        if "finance costs" in raw_lower:
            score += 8
        elif "fln:jnce costs" in raw_lower:
            score += 8
        elif "finance cost" in raw_lower:
            score += 5
        if (
            "profit before depreciation" in raw_lower
            or "finance income and tax" in raw_lower
        ):
            score -= 45

    if metric_name == "eps":
        if (
            "basic" in raw_lower
            or "b ~sic" in raw_lower
        ):
            score += 6
        if "diluted" in raw_lower:
            score -= 2

    noisy_patterns = [
        r"\b\d{1,2}\.0?\d\.20\d{2}\b",
        r"\b\d{1,2}\s+march\s+20\d{2}\b",
    ]

    if any(
        re.search(pattern, raw_lower)
        for pattern in noisy_patterns
    ):
        score -= 50

    if any(
        pattern in raw_lower
        for pattern in [
            "layout table text",
            "regd. office",
            "registered office",
            "telephone",
            "e-mail",
            "website",
            "cin:",
            "cscs",
            "hws]",
            "bott",
            "bolts",
            "—~",
        ]
    ):
        score -= 80

    if any(
        pattern in raw_lower
        for pattern in [
            "adjustments for",
            "adjustments to reconcile",
            "cash flow",
            "profit) / loss on sale",
            "(profit) / loss on sale",
            "gain on cancellation",
            "sundry creditors written",
            "slindry creditors written",
        ]
    ):
        score -= 80

    if (
        metric_name in [
            "revenue",
            "profit_before_tax",
            "profit_after_tax",
        ]
        and "segment" in raw_lower
    ):
        score -= 90

    if "cash flow" in raw_lower:
        score -= 35

    return score


def extract_numbers_for_row_completion(row_text):

    row_text = re.sub(
        r"[\(\[\{]?\s*\d+\s*[-+·]\s*\d+\s*[\)\]\}]?",
        " ",
        row_text
    )
    row_text = re.sub(
        r"[\(\[\{]\s*[ivx\d]+\s*[\)\]\}]",
        " ",
        row_text,
        flags=re.IGNORECASE
    )

    return extract_numbers_from_line(
        row_text
    )


def find_matched_keyword(line, keywords):

    line_lower = line.lower()

    matched_keywords = [
        keyword
        for keyword in keywords
        if keyword in line_lower
    ]

    if not matched_keywords:
        return None

    return max(
        matched_keywords,
        key=len
    )


def strip_metric_prefix(row_text, metric_name, matched_keyword):

    if not matched_keyword:
        return row_text

    row_lower = row_text.lower()
    keyword_index = row_lower.find(
        matched_keyword
    )

    if keyword_index < 0:
        return row_text

    value_text = row_text[
        keyword_index + len(matched_keyword):
    ]

    # Remove bracketed row formulas before OCR decimal repair so formulas
    # such as (11-12) are not rewritten as 11.12.
    value_text = re.sub(
        r"[\(\[\{]\s*\d+\s*[-+·]\s*\d+\s*[\)\]\}]",
        " ",
        value_text
    )
    value_text = re.sub(
        r"[\(\[\{]\s*[ivx\d]+\s*[\)\]\}]",
        " ",
        value_text,
        flags=re.IGNORECASE
    )

    value_text = normalize_ocr_number_line(
        value_text
    )

    # Remove row formulas like (1+2), (3-4), {5+6}, or 7·8.
    value_text = re.sub(
        r"[\(\[\{]?\s*\d+\s*[-+·]\s*\d+\s*[\)\]\}]?",
        " ",
        value_text
    )
    value_text = re.sub(
        r"[\(\[\{]\s*[ivxlj\d\s+·-]{2,}\s*[\)\]\}]",
        " ",
        value_text,
        flags=re.IGNORECASE
    )

    if metric_name == "eps":

        basic_index = re.search(
            r"\(\s*a\s*\)",
            value_text,
            flags=re.IGNORECASE
        )

        if basic_index:
            value_text = value_text[
                basic_index.start():
            ]
        else:
            basic_word_index = re.search(
                r"\bbasic\b",
                value_text,
                flags=re.IGNORECASE
            )

            if basic_word_index:
                value_text = value_text[
                    basic_word_index.start():
                ]

        value_text = re.sub(
            r"of\s+re\.?\s*\d+\s*/?-?\s*each",
            " ",
            value_text,
            flags=re.IGNORECASE
        )
        value_text = re.sub(
            r"of\s+rs[,.]?\s*\d+\s*/?-?\s*each",
            " ",
            value_text,
            flags=re.IGNORECASE
        )
        value_text = re.sub(
            r"face\s+value\s+re\.?\s*\d+",
            " ",
            value_text,
            flags=re.IGNORECASE
        )
        value_text = re.sub(
            r"\b(\d{1,3}),(\d{2})\b",
            r"\1.\2",
            value_text
        )

    return value_text


def trim_row_at_boundary(row_text, metric_name):

    row_lower = row_text.lower()

    boundaries_by_metric = {
        "revenue": [
            "other income",
            "otherincome",
            "wotherincome",
            "total income",
            "expenses",
        ],
        "total_income": [
            "expenses",
            "employee benefits",
            "finance costs",
            "profit before tax",
        ],
        "finance_cost": [
            "depreciation",
            "other expenses",
            "exceptional items",
            "total expenses",
        ],
        "profit_before_tax": [
            "tax expense",
            "net profit",
            "profit after tax",
            "other comprehensive",
        ],
        "profit_after_tax": [
            "other comprehensive",
            "total comprehensive",
            "earnings per share",
        ],
        "eps": [
            "notes",
            "see accompanying",
        ],
    }

    cut_index = None

    for boundary in boundaries_by_metric.get(
        metric_name,
        []
    ):
        index = row_lower.find(boundary)

        # OCR often reads the next row serial number immediately before
        # the row label, e.g. "88.00 2 |other income". Drop that serial too.
        if index > 0:
            prefix = row_text[:index]
            serial_match = re.search(
                r"(\s+\d+\s*[\|\[\]]?\s*)$",
                prefix
            )
            if serial_match:
                index = serial_match.start(1)

        if index > 0 and (
            cut_index is None
            or index < cut_index
        ):
            cut_index = index

    if cut_index is not None:
        return row_text[:cut_index]

    return row_text


def extract_metric_numbers(
    row_text,
    metric_name,
    matched_keyword
):

    value_text = strip_metric_prefix(
        row_text,
        metric_name,
        matched_keyword
    )

    value_text = trim_row_at_boundary(
        value_text,
        metric_name
    )

    numbers = extract_metric_value_tokens(
        value_text
    )

    if (
        metric_name in ["revenue", "total_income"]
        and numbers
        and "." not in value_text
        and "," not in value_text
        and len(numbers) >= 4
        and all(
            abs(number) >= 10000
            for number in numbers[:min(MAX_VALUES_PER_METRIC_ROW, len(numbers))]
        )
    ):
        numbers = [
            round(number / 100, 2)
            for number in numbers
        ]

    if (
        metric_name == "profit_after_tax"
        and "other comprehensive" in row_text.lower()
        and len(numbers) >= MAX_VALUES_PER_METRIC_ROW
        and abs(numbers[MAX_VALUES_PER_METRIC_ROW - 1]) <= 20
        and float(numbers[MAX_VALUES_PER_METRIC_ROW - 1]).is_integer()
    ):
        numbers = (
            numbers[:MAX_VALUES_PER_METRIC_ROW - 1]
            + numbers[MAX_VALUES_PER_METRIC_ROW:]
        )

    if (
        metric_name == "eps"
        and numbers
        and "." not in value_text
        and all(
            number != 0
            and abs(number) >= 10
            and float(number).is_integer()
            for number in numbers[:MAX_VALUES_PER_METRIC_ROW]
        )
    ):
        numbers = [
            round(number / 100, 2)
            for number in numbers
        ]

    return numbers[:MAX_RAW_VALUES_PER_METRIC_ROW]


def is_clean_metric_value_line(line):

    if not line:
        return False

    if line_has_metric_keyword(line):
        return False

    numbers = extract_metric_value_tokens(line)

    if len(numbers) < MAX_VALUES_PER_METRIC_ROW:
        return False

    line_lower = line.lower()

    if any(
        word in line_lower
        for word in [
            "march",
            "december",
            "audited",
            "unaudited",
            "refer note",
            "particulars",
        ]
    ):
        return False

    return True


def line_has_metric_keyword(line):

    line_lower = line.lower()

    for keywords in FINANCIAL_METRIC_PATTERNS.values():
        if any(
            keyword in line_lower
            for keyword in keywords
        ):
            return True

    return False


def line_starts_new_financial_row(line):

    line_lower = line.lower().strip()

    if not line_lower:
        return False

    if line_has_metric_keyword(line_lower):
        return True

    return any(
        keyword in line_lower
        for keyword in ROW_BOUNDARY_KEYWORDS
    )


def extract_metric_row_block(lines, start_index):

    row_lines = [
        lines[start_index].strip()
    ]

    for index in range(
        start_index + 1,
        min(
            len(lines),
            start_index + MAX_ROW_LOOKAHEAD_LINES + 1
        )
    ):

        candidate = lines[index].strip()

        if not candidate:
            continue

        current_numbers = extract_numbers_for_row_completion(
            " ".join(row_lines)
        )

        if (
            line_starts_new_financial_row(candidate)
            and current_numbers
            and len(row_lines) > 1
        ):
            break

        row_lines.append(candidate)

        numbers = extract_numbers_for_row_completion(
            " ".join(row_lines)
        )

        if len(numbers) >= MAX_VALUES_PER_METRIC_ROW:
            break

    row_text = " ".join(row_lines)

    return (
        row_text,
        extract_numbers_from_line(row_text)
    )


def map_values_to_periods(values):

    return {
        period: value
        for period, value in zip(
            FINANCIAL_RESULT_PERIOD_LABELS,
            values[:len(FINANCIAL_RESULT_PERIOD_LABELS)]
        )
    }


def select_period_values(numbers, source_type="unknown"):

    if not numbers:
        return []

    clean_numbers = list(numbers)

    if (
        len(clean_numbers) > MAX_VALUES_PER_METRIC_ROW
        and abs(clean_numbers[0]) <= 20
        and float(clean_numbers[0]).is_integer()
    ):
        clean_numbers = clean_numbers[1:]

    if len(clean_numbers) >= 10:

        is_dual_standalone_consolidated_layout = (
            abs(clean_numbers[6]) > abs(clean_numbers[0])
            and abs(clean_numbers[8]) > abs(clean_numbers[3])
        )

        if is_dual_standalone_consolidated_layout:

            if source_type in ["consolidated", "unknown"]:
                return [
                    clean_numbers[3],
                    clean_numbers[4],
                    clean_numbers[5],
                    clean_numbers[8],
                    clean_numbers[9],
                ]

            if source_type == "standalone":
                return [
                    clean_numbers[0],
                    clean_numbers[1],
                    clean_numbers[2],
                    clean_numbers[6],
                    clean_numbers[7],
                ]

    return clean_numbers[:MAX_VALUES_PER_METRIC_ROW]


def has_reliable_period_values(values):

    if len(values) < MAX_VALUES_PER_METRIC_ROW:
        return False

    positive_values = [
        abs(value)
        for value in values[:MAX_VALUES_PER_METRIC_ROW]
        if value
    ]

    if len(positive_values) < MAX_VALUES_PER_METRIC_ROW:
        return True

    smallest_value = min(positive_values)
    largest_value = max(positive_values)

    if smallest_value == 0:
        return True

    # A huge spread in the same table row usually means OCR split a comma
    # formatted number into multiple cells, e.g. "98 483" instead of "98,483".
    return (largest_value / smallest_value) <= 500


def build_metric_result(
    raw_line,
    numbers,
    source_type="unknown",
    row_score=None
):

    period_numbers = select_period_values(
        numbers,
        source_type
    )

    period_values = {}
    period_mapping_complete = has_reliable_period_values(
        period_numbers
    )

    if period_mapping_complete:
        period_values = map_values_to_periods(
            period_numbers
        )

    return {
        "raw_line": raw_line.strip(),
        "period_labels": FINANCIAL_RESULT_PERIOD_LABELS,
        "values": period_numbers,
        "raw_values": numbers,
        "period_values": period_values,
        "source_type": source_type,
        "row_score": (
            row_score
            if row_score is not None
            else score_metric_row(
                "unknown",
                raw_line,
                numbers
            )
        ),
        "period_mapping_complete": period_mapping_complete
    }


# =========================================================
# EXTRACT FINANCIAL METRICS
# =========================================================


def _extract_financial_metrics_from_text(
    text,
    source_type="unknown"
):

    if not text:
        return {}

    lines = text.splitlines()

    extracted_metrics = {}

    best_metric_scores = defaultdict(
        lambda: -1000
    )

    for index, line in enumerate(lines):

        if line.strip().startswith("-"):
            continue

        line_lower = line.lower()
        # =========================================================
        # SPECIAL PAT EXTRACTION
        # =========================================================
        if (
            "total profit after tax" in line_lower
            and "comprehensive" not in line_lower
            and "segment" not in line_lower
            ):
            raw_line, block_numbers = extract_metric_row_block(
                lines,
                index
            )
            numbers = extract_metric_numbers(
                raw_line,
                "profit_after_tax",
                "total profit after tax"
            )

            if len(numbers) >= 5:
                row_score = score_metric_row(
                    "profit_after_tax",
                    raw_line,
                    numbers
                )

                if row_score < 0:
                    continue

                extracted_metrics["profit_after_tax"] = (
                    build_metric_result(
                        raw_line,
                        numbers,
                        source_type,
                        row_score
                    )
                )
                best_metric_scores["profit_after_tax"] = (
                    row_score
                    )
                continue
        elif (
            "profit after tax" in line_lower
            and "other comprehensive" not in line_lower
            and "comprehensive" not in line_lower
            and "segment" not in line_lower
        ):
            raw_line, block_numbers = extract_metric_row_block(
                lines,
                index
            )
            numbers = extract_metric_numbers(
                raw_line,
                "profit_after_tax",
                "profit after tax"
            )

            if (
                len(numbers) >= 5
                and score_metric_row(
                    "profit_after_tax",
                    raw_line,
                    numbers
                ) > best_metric_scores["profit_after_tax"]
            ):
                row_score = score_metric_row(
                    "profit_after_tax",
                    raw_line,
                    numbers
                )

                if row_score < 0:
                    continue

                extracted_metrics["profit_after_tax"] = (
                    build_metric_result(
                        raw_line,
                        numbers,
                        source_type,
                        row_score
                    )
                )
            
                best_metric_scores["profit_after_tax"] = (
                    row_score
                    )
                continue

        for metric_name, keywords in (
            FINANCIAL_METRIC_PATTERNS.items()
        ):

            matched_keyword = find_matched_keyword(
                line,
                keywords
            )

            if not matched_keyword:
                continue

            if (
                metric_name == "revenue"
                and not extract_metric_value_tokens(line)
                and index > 0
                and is_clean_metric_value_line(
                    lines[index - 1]
                )
            ):
                raw_line = (
                    line.strip()
                    + " "
                    + lines[index - 1].strip()
                )
                block_numbers = extract_metric_value_tokens(
                    lines[index - 1]
                )
            else:
                raw_line, block_numbers = extract_metric_row_block(
                    lines,
                    index
                )

            numbers = extract_metric_numbers(
                raw_line,
                metric_name,
                matched_keyword
            )

            if not numbers:
                continue

            score = score_metric_row(
                metric_name,
                raw_line,
                numbers
            )
            if score < 0:
                continue
            if score <= best_metric_scores[metric_name]:
                continue
            best_metric_scores[metric_name] = score
            
            extracted_metrics[metric_name] = (
                build_metric_result(
                    raw_line,
                    numbers,
                    source_type,
                    score
                )
            )

    return extracted_metrics


def split_financial_sections(text):

    if not text:
        return []

    header_pattern = re.compile(
        r"(?=--- PDF PAGE\s+\d+.*?---)",
        re.IGNORECASE
    )

    sections = [
        section.strip()
        for section in header_pattern.split(text)
        if section.strip()
    ]

    if not sections:
        sections = [text]

    return sections


def identify_financial_source_type(section_text):

    text_lower = (section_text or "").lower()

    if (
        "consolidated financial results" in text_lower
        or "statement of consolidated" in text_lower
        or "consolidated segment" in text_lower
        or "consolidated" in text_lower
    ):
        return "consolidated"

    if (
        "standalone financial results" in text_lower
        or "statement of standalone" in text_lower
        or "standalone segment" in text_lower
        or "standalone" in text_lower
    ):
        return "standalone"

    return "unknown"


def score_metric_set(metrics, source_type):

    if not metrics:
        return 0

    score = 0

    if source_type == "consolidated":
        score += 100
    elif source_type == "standalone":
        score += 20

    metric_weights = {
        "revenue": 30,
        "profit_after_tax": 30,
        "profit_before_tax": 20,
        "total_income": 10,
        "finance_cost": 5,
    }

    for metric_name, weight in metric_weights.items():

        metric = metrics.get(metric_name)

        if not metric:
            continue

        if metric.get("period_mapping_complete"):
            score += weight
        else:
            score += 1

    return score


def score_single_metric(metric):

    if not metric:
        return 0

    score = 0

    if metric.get("period_mapping_complete"):
        score += 1000

    score += metric.get("row_score", 0) * 10

    source_type = metric.get(
        "source_type",
        "unknown"
    )

    if source_type == "consolidated":
        score += 20
    elif source_type == "standalone":
        score += 5

    score += len(
        metric.get(
            "values",
            []
        )
    )

    return score


def extract_financial_metrics(text):

    if not text:
        return {}

    sections = split_financial_sections(text)

    best_metrics = {}
    section_metric_sets = []

    for section in sections:

        source_type = identify_financial_source_type(
            section
        )

        metrics = _extract_financial_metrics_from_text(
            section,
            source_type
        )

        if not metrics:
            continue

        section_metric_sets.append(
            {
                "source_type": source_type,
                "metrics": metrics,
                "score": score_metric_set(
                    metrics,
                    source_type
                )
            }
        )

        for metric_name, metric in metrics.items():

            current_best = best_metrics.get(
                metric_name
            )

            if (
                not current_best
                or score_single_metric(metric) > score_single_metric(
                    current_best
                )
            ):
                best_metrics[metric_name] = metric

    if not best_metrics:
        return _extract_financial_metrics_from_text(
            text
        )

    primary_metric_set = max(
        section_metric_sets,
        key=lambda metric_set: metric_set["score"],
        default=None
    )

    if primary_metric_set:

        primary_source_type = primary_metric_set["source_type"]
        coherent_metrics = dict(
            primary_metric_set["metrics"]
        )

        for metric_set in sorted(
            section_metric_sets,
            key=lambda metric_set: metric_set["score"],
            reverse=True
        ):

            if metric_set["source_type"] != primary_source_type:
                continue

            for metric_name, metric in metric_set["metrics"].items():

                current_metric = coherent_metrics.get(
                    metric_name
                )

                if (
                    not current_metric
                    or (
                        not current_metric.get("period_mapping_complete")
                        and metric.get("period_mapping_complete")
                    )
                ):
                    coherent_metrics[metric_name] = metric

        for metric_name, metric in best_metrics.items():

            current_metric = coherent_metrics.get(
                metric_name
            )

            if (
                not current_metric
                or (
                    not current_metric.get("period_mapping_complete")
                    and metric.get("period_mapping_complete")
                )
            ):
                coherent_metrics[metric_name] = metric

        return coherent_metrics

    return best_metrics


# =========================================================
# CALCULATE BASIC GROWTH
# =========================================================


def calculate_growth(current, previous):

    try:

        if previous == 0:
            return None

        growth = (
            (current - previous) / previous
            ) * 100
        # =========================================================
        # OCR SANITY VALIDATION
        # =========================================================
        if abs(growth) > 2000:
            return None
        return round(growth, 2)

    except Exception:
        return None


# =========================================================
# GENERATE STRUCTURED INSIGHTS
# =========================================================


def generate_financial_insights(metrics):

    insights = {}

    # Revenue
    revenue_data = metrics.get("revenue")

    if (
        revenue_data
        and len(revenue_data["values"]) >= 2
    ):

        period_values = revenue_data.get(
            "period_values",
            {}
        )
        current = period_values.get(
            "year_current"
        )
        previous = period_values.get(
            "year_previous"
        )

        if (
            current is not None
            and previous is not None
        ):
            insights["revenue_growth_pct"] = (
                calculate_growth(
                    current,
                    previous
                )
            )

    # PAT
    pat_data = metrics.get(
        "profit_after_tax"
    )

    if (
        pat_data
        and len(pat_data["values"]) >= 2
    ):

        period_values = pat_data.get(
            "period_values",
            {}
        )
        current = period_values.get(
            "year_current"
        )
        previous = period_values.get(
            "year_previous"
        )

        if (
            current is not None
            and previous is not None
        ):
            if current < 0 and previous < 0:
                insights["pat_loss_narrowed_pct"] = (
                    round(
                        (
                            (abs(previous) - abs(current))
                            / abs(previous)
                        ) * 100,
                        2
                    )
                )
            elif current >= 0 and previous < 0:
                insights["pat_turnaround_from_loss"] = True
            elif current < 0 and previous >= 0:
                insights["pat_declined_to_loss"] = True
            else:
                insights["pat_growth_pct"] = (
                    calculate_growth(
                        current,
                        previous
                    )
                )

    return insights
