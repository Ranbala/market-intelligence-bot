from datetime import datetime, timedelta
from loguru import logger

# Keywords we WANT
IMPORTANT_KEYWORDS = [
    "earnings",
    "results",
    "profit",
    "loss",
    "order",
    "contract",
    "deal",
    "acquisition",
    "merger",
    "stake",
    "dividend",
    "buyback",
    "ipo",
    "investment",
    "approval",
    "policy",
    "government",
    "capex",
    "infrastructure",
    "bank",
    "stocks",
    "shares",
    "market",
    "nifty",
    "sensex"
]

# Keywords we DON'T WANT
EXCLUDED_KEYWORDS = [
    "us stocks",
    "s&p 500",
    "nasdaq",
    "dow jones",
    "spacex",
    "mars",
    "fed's",
    "federal reserve",
    "wall street",
    "middle east peace hopes"
]

def is_recent(published_date):

    try:
        news_date = datetime.strptime(
            published_date,
            "%a, %d %b %Y %H:%M:%S %z"
        )

        now = datetime.now(news_date.tzinfo)

        return news_date >= now - timedelta(days=2)

    except:
        return False

def is_relevant(title):

    title_lower = title.lower()

    # Exclude unwanted news
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in title_lower:
            return False

    # Keep important market news
    for keyword in IMPORTANT_KEYWORDS:
        if keyword in title_lower:
            return True

    return False

def filter_news(news_list):

    filtered_news = []

    for item in news_list:

        title = item.get("title", "")
        published = item.get("published", "")

        if not is_recent(published):
            continue

        if not is_relevant(title):
            continue

        filtered_news.append(item)

    logger.success(f"Filtered down to {len(filtered_news)} high-quality articles")

    return filtered_news