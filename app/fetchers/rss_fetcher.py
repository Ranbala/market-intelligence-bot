import feedparser
from loguru import logger

RSS_FEEDS = {
    "Moneycontrol": "https://www.moneycontrol.com/rss/MCtopnews.xml",

    "ETMarkets":
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",

    "LiveMint":
    "https://www.livemint.com/rss/markets",

    "Investing":
    "https://www.investing.com/rss/news.rss",

    "Reuters": "https://news.google.com/rss/search?q=site:reuters.com+india+stocks&hl=en-IN&gl=IN&ceid=IN:en",
    
    "CNBC": "https://news.google.com/rss/search?q=site:cnbctv18.com+market&hl=en-IN&gl=IN&ceid=IN:en",
    
    "Bloomberg": "https://news.google.com/rss/search?q=site:bloomberg.com+india+markets&hl=en-IN&gl=IN&ceid=IN:en",
}


def fetch_news():

    all_news = []
    dead_feeds = 0

    for source, url in RSS_FEEDS.items():

        try:
            logger.info(f"Fetching news from {source}")

            feed = feedparser.parse(url)

            # Feed validation
            if not feed.entries:
                logger.warning(f"{source}: No articles found")
                dead_feeds += 1
                continue

            for entry in feed.entries:

                news_item = {
                    "source": source,
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "")
                }

                all_news.append(news_item)

            logger.success(
                f"{source}: {len(feed.entries)} articles fetched"
            )

            # Print latest headline
            logger.info(
                f"{source} Latest: {feed.entries[0].get('title', 'No title')}"
            )

        except Exception as e:
            logger.error(f"Error fetching from {source}: {e}")
            dead_feeds += 1

    logger.info(f"Total dead/problematic feeds: {dead_feeds}")

    return all_news