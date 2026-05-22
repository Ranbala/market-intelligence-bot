import feedparser
from loguru import logger

RSS_FEEDS = {
    "Moneycontrol": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "ETMarkets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "ReutersBusiness": "https://feeds.reuters.com/reuters/businessNews"
}

def fetch_news():
    all_news = []

    for source, url in RSS_FEEDS.items():
        try:
            logger.info(f"Fetching news from {source}")

            feed = feedparser.parse(url)

            for entry in feed.entries:

                news_item = {
                    "source": source,
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "")
                }

                all_news.append(news_item)

            logger.success(f"{source}: {len(feed.entries)} articles fetched")

        except Exception as e:
            logger.error(f"Error fetching from {source}: {e}")

    return all_news