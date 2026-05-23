from collections import defaultdict


def get_event_family(desc):

    desc = desc.lower()

    if any(word in desc for word in [
        "dividend",
        "board",
        "financial",
        "results",
        "record date"
    ]):
        return "financials"

    if any(word in desc for word in [
        "order",
        "contract"
    ]):
        return "orders"

    if any(word in desc for word in [
        "acquisition",
        "stake",
        "merger",
        "investment"
    ]):
        return "corporate"

    return "general"


def cluster_filings(filings):

    grouped = defaultdict(list)

    for filing in filings:

        symbol = filing.get("symbol", "")

        desc = filing.get("desc", "")

        family = get_event_family(desc)

        cluster_key = f"{symbol}_{family}"

        grouped[cluster_key].append(filing)

    return grouped