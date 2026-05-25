from datetime import datetime, timedelta
from loguru import logger
from dateutil import parser


# =========================================================
# IMPORTANT MARKET / STOCK NEWS KEYWORDS
# =========================================================

IMPORTANT_KEYWORDS = [

    # Earnings / Financials
    "earnings",
    "results",
    "profit",
    "loss",
    "revenue",
    "ebitda",
    "margin",

    # Corporate actions
    "order",
    "contract",
    "deal",
    "acquisition",
    "merger",
    "stake",
    "dividend",
    "buyback",
    "ipo",
    "ofs",
    "investment",
    "approval",

    # Stocks / Markets
    "shares",
    "stock",
    "market",
    "nifty",
    "sensex",
    "bank nifty",

    # Stock movement
    "rally",
    "surge",
    "surges",
    "zoom",
    "jumps",
    "rises",
    "gains",
    "falls",
    "drops",
    "slides",

    # Important levels
    "52-week",
    "all-time high",
    "record high",

    # Economy / Macro
    "rbi",
    "inflation",
    "interest rate",
    "crude",
    "oil",
    "rupee",
    "fii",
    "dii",
    "bond",
    "treasury",
    "economy",
    "gdp",

    # India market relevance
    "india",
    "indian shares",
    "nse",
    "bse",

    # Sectors
    "bank",
    "it sector",
    "pharma",
    "auto sector"
]


# =========================================================
# NOISE / RECOMMENDATION / NON-ACTIONABLE NEWS
# =========================================================

EXCLUDED_KEYWORDS = [

    # Recommendations / advisory
    "should you buy",
    "buy sell or hold",
    "top picks",
    "stock picks",
    "stocks to buy",
    "shares to buy",
    "buy today",
    "bullish on",
    "analyst recommends",
    "brokerage recommends",
    "recommended",
    "recommendation",
    "trading idea",
    "target price",
    "stop loss",

    # Educational
    "explainer",
    "how to",
    "why you should",
    "safer than fd",
    "mutual fund guide",
    "investment strategy",
    "portfolio strategy",

    # Generic investing
    "best stocks",
    "long term picks",
    "portfolio",
    "multibagger",

    # Opinion/editorial
    "opinion",
    "editorial",
    "market outlook",

    # Lifestyle / non-market
    "travel",
    "fashion",
    "celebrity",

    # Global irrelevant
    "us stock market",
    "mortgage",
    "treasury yield",
    "dow jones",
    "nasdaq",
    "s&p 500",
    "swot analysis",
    "technical analysis",
    "chart analysis",
    "market analysis",
    "wealth summit",
    "masterclass",
]


# =========================================================
# CHECK IF NEWS IS RECENT
# =========================================================

def is_recent(published_date):
    try:
        news_date = parser.parse(
            published_date
            )
        
        now = datetime.now(
            news_date.tzinfo
        ) if news_date.tzinfo else datetime.now()

        return (
            news_date >=
            now - timedelta(days=2)
        )

    except Exception as e:
        print(
            f"DATE PARSE FAILED | "
            f"DATE: {published_date} | "
            f"ERROR: {str(e)}"
        )

        return False


# =========================================================
# CHECK IF NEWS IS RELEVANT
# =========================================================

def is_relevant(title):

    title_lower = title.lower()

    for keyword in EXCLUDED_KEYWORDS:

        if keyword in title_lower:

            return (
                False,
                f"EXCLUDED KEYWORD: {keyword}"
            )

    for keyword in IMPORTANT_KEYWORDS:

        if keyword in title_lower:

            return (
                True,
                f"IMPORTANT KEYWORD: {keyword}"
            )

    return (
        False,
        "NO IMPORTANT KEYWORD MATCH"
    )


# =========================================================
# MAIN FILTER FUNCTION
# =========================================================

def filter_news(news_list):

    filtered_news = []

    for item in news_list:

        title = item.get("title", "")
        published = item.get("published", "")

        # Remove old news
        if not is_recent(published):

            continue

        # Remove irrelevant news
        is_valid, reason = is_relevant(title)
        if not is_valid:

            # print(
            #     f"FILTER REJECTED | "
            #     f"REASON: {reason} | "
            #     f"SOURCE: {item['source']} | "
            #     f"PUBLISHED: {published} | "
            #     f"TITLE: {title}"
            # )

            continue

        filtered_news.append(item)

    logger.success(
        f"Filtered down to {len(filtered_news)} high-quality articles"
    )

    return filtered_news