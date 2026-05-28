import re


def extract_order_details(text):

    result = {}

    # ==========================================
    # ORDER VALUE
    # ==========================================

    order_value_patterns = [
        r'Rs\.?\s*([\d,]+\.\d+)\s*Crore',
        r'₹\s*([\d,]+\.\d+)\s*crores',
        r'₹\s*([\d,]+\.\d+)\s*Crore',
        r'([\d,]+\.\d+)\s*crores',
        r'(?:rs\.?|inr|~inr)\s*([\d,.]+)\s*crore'
    ]

    for pattern in order_value_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = (
                match.group(1)
                .replace(",", "")
            )

            result["order_value_crore"] = float(value)
            break

    # ==========================================
    # CLIENT NAME
    # ==========================================

    client_patterns = [
        r'from\s+([A-Za-z0-9\s&\-.]+?Limited)',
        r'awarded by\s+([A-Za-z0-9\s&\-.]+?Limited)',
    ]

    for pattern in client_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            result["client_name"] = (
                match.group(1).strip()
            )

            break

    # ==========================================
    # EXECUTION PERIOD
    # ==========================================

    execution_pattern = (
        r'(\d+)\s*(Months|Month|Years|Year)'
        )

    match = re.search(
        execution_pattern,
        text,
        re.IGNORECASE
    )

    if match:
        result["execution_period"] = (
            match.group(1)
            + " "
            + match.group(2)
        )

    # ==========================================
    # DOMESTIC / INTERNATIONAL
    # ==========================================

    if "Domestic" in text:

        result["order_scope"] = "Domestic"

    elif "International" in text:

        result["order_scope"] = "International"

    return result