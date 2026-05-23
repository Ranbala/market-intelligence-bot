import requests
from loguru import logger

API_URL = (
    "https://www.nseindia.com/api/"
    "corporate-announcements?index=equities"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_nse_filings():

    logger.info("Fetching NSE corporate filings...")

    try:

        session = requests.Session()

        # VERY IMPORTANT
        session.get(
            "https://www.nseindia.com",
            headers=HEADERS,
            timeout=10
        )

        response = session.get(
            API_URL,
            headers=HEADERS,
            timeout=10
        )

        data = response.json()

        logger.success(
            f"NSE Filings fetched: {len(data)}"
        )

        return data

    except Exception as e:

        logger.error(
            f"NSE Filing Fetch Failed: {str(e)}"
        )

        return []