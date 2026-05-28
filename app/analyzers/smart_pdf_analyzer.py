IMPORTANT_SECTION_KEYWORDS = [

    # Financial performance
    "revenue",
    "ebitda",
    "profit",
    "net profit",
    "profit before tax",
    "profit after tax",
    "pat",
    "eps",
    "margin",
    "cash flow",
    "finance cost",

    # Corporate actions
    "dividend",
    "bonus",
    "split",
    "rights issue",
    "buyback",
    "preferential",

    # Business growth
    "order",
    "order book",
    "order backlog",
    "contract",
    "guidance",
    "capacity expansion",
    "capex",
    "new plant",
    "acquisition",
    "merger",
    "subsidiary",
    "joint venture",

    # Financial stress / restructuring
    "debt",
    "default",
    "restructuring",
    "nclt",
    "insolvency",
    "narcl",

    # Market / institutional activity
    "analyst",
    "investor",
    "institutional",
    "fund raising",

    # Sector / theme related
    "data center",
    "hyperscaler",
    "export",
    "defence",
    "renewable",
    "ai",

    # Management commentary
    "outlook",
    "future growth",
    "expansion",
    "strategic"
]


IGNORE_LINE_KEYWORDS = [

    "internal control",
    "chartered accountants",
    "true and fair view",
    "accounting principles",
    "standalone statement",
    "consolidated statement",
    "guidance note",
    "in accordance with",
    "ind as",
    "audit procedures",
    "regulatory requirements",
]


LINE_PRIORITY_SCORES = {

    "revenue": 10,
    "net profit": 10,
    "profit after tax": 10,
    "profit before tax": 9,
    "ebitda": 9,
    "eps": 9,
    "order book": 9,
    "order backlog": 9,
    "order": 8,
    "contract": 8,
    "guidance": 8,
    "capacity expansion": 8,
    "acquisition": 8,
    "merger": 8,
    "debt": 9,
    "restructuring": 10,
    "nclt": 10,
    "insolvency": 10,
    "narcl": 10,
    "dividend": 7,
    "buyback": 8,
    "rights issue": 9,
    "preferential": 7,
    "analyst": 6,
    "investor": 6,
    "institutional": 6,
    "outlook": 7,
    "future growth": 7,
    "strategic": 7,
}


MAX_IMPORTANT_LINES = 120
MAX_LINE_LENGTH = 400


def is_garbage_line(line):

    line_lower = line.lower()

    if len(line.strip()) < 15:
        return True

    if len(line) > MAX_LINE_LENGTH:
        return True

    if any(
        keyword in line_lower
        for keyword in IGNORE_LINE_KEYWORDS
    ):
        return True

    return False



def calculate_line_priority(line):

    line_lower = line.lower()

    priority_score = 0

    for keyword, score in LINE_PRIORITY_SCORES.items():

        if keyword in line_lower:
            priority_score = max(
                priority_score,
                score
            )

    return priority_score



def extract_important_sections(text):

    if not text:
        return ""

    lines = text.splitlines()

    scored_lines = []

    seen_lines = set()

    total_lines = len(lines)

    for index, line in enumerate(lines):

        clean_line = line.strip()

        if not clean_line:
            continue

        if clean_line in seen_lines:
            continue

        if is_garbage_line(clean_line):
            continue

        line_lower = clean_line.lower()

        matched = any(
            keyword in line_lower
            for keyword in IMPORTANT_SECTION_KEYWORDS
        )

        if not matched:
            continue

        priority_score = calculate_line_priority(
            clean_line
        )

        context_block = [clean_line]

        for next_index in range(
            index + 1,
            min(index + 3, total_lines)
        ):

            nearby_line = lines[next_index].strip()

            if (
                nearby_line
                and not is_garbage_line(nearby_line)
            ):
                context_block.append(nearby_line)

        scored_lines.append({
            "score": priority_score,
            "text": "\n".join(context_block)
        })

        seen_lines.add(clean_line)

    scored_lines.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    final_sections = []

    seen_sections = set()

    for item in scored_lines:

        section_text = item["text"]

        if section_text in seen_sections:
            continue

        final_sections.append(section_text)
        seen_sections.add(section_text)

    return "\n\n".join(
        final_sections[:MAX_IMPORTANT_LINES]
    )