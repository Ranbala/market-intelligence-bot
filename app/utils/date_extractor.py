import re

def extract_filing_dates(text):

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    patterns = [

        # 22-May-2026
        r"\d{1,2}[- ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[- ]\d{4}",

        # 22nd May, 2026
        r"\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\,?\s+\d{4}",

        # May 22, 2026
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
    ]

    found_dates = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        found_dates.extend(matches)

    cleaned = []

    for date in found_dates:

        if len(date) > 8:
            cleaned.append(date.strip())

    seen = set()
    unique_dates = []
    for date in cleaned:
        if date not in seen:
            seen.add(date)
            unique_dates.append(date)

    return unique_dates[:10]