from fetchers.rss_fetcher import fetch_news
from fetchers.news_filter import filter_news
from ai.news_analyzer import analyze_news
from telegram_bot.sender import send_telegram_message

from database import (
    init_db,
    news_exists,
    save_news
)

import re


# =========================================================
# TELEGRAM MESSAGE FORMATTER
# =========================================================

def format_telegram_message(title, analysis):

    event_type = "Unknown"
    sentiment = "Neutral"
    importance = "5"
    summary = "No summary available"

    event_match = re.search(
        r"EVENT_TYPE:\s*(.*)",
        analysis
    )

    sentiment_match = re.search(
        r"SENTIMENT:\s*(.*)",
        analysis
    )

    importance_match = re.search(
        r"IMPORTANCE:\s*(.*)",
        analysis
    )

    summary_match = re.search(
        r"SUMMARY:\s*(.*)",
        analysis,
        re.DOTALL
    )

    if event_match:
        event_type = event_match.group(1).strip()

    if sentiment_match:
        sentiment = sentiment_match.group(1).strip()

    if importance_match:
        importance = importance_match.group(1).strip()

    if summary_match:
        summary = summary_match.group(1).strip()

    telegram_message = f"""
🚨 MARKET ALERT

📰 {title}

📌 Event: {event_type}
📈 Sentiment: {sentiment}
🔥 Importance: {importance}/10

💡 Summary:
{summary}
"""

    return telegram_message


# =========================================================
# MAIN
# =========================================================

def main():

    init_db()

    raw_news = fetch_news()

    print(f"\nRAW NEWS COUNT: {len(raw_news)}")

    filtered_news = filter_news(raw_news)

    print(f"\nFILTERED NEWS COUNT: {len(filtered_news)}\n")

    priority_news = []

    priority_keywords = [
        "results",
        "profit",
        "order",
        "deal",
        "stake",
        "dividend",
        "acquisition",
        "merger",
        "investment",
        "approval"
    ]

    for item in filtered_news:

        title = item["title"].lower()

        if any(keyword in title for keyword in priority_keywords):

            priority_news.append(item)

    for idx, item in enumerate(priority_news[:10], start=1):

        if news_exists(item["title"]):

            print(
                f"Skipping duplicate news: {item['title']}"
            )

            continue

        print("=" * 120)

        print(f"\n{idx}. SOURCE     : {item['source']}")

        print(f"TITLE           : {item['title']}")

        print(f"PUBLISHED       : {item['published']}")

        print("\nAI ANALYSIS:\n")

        analysis = analyze_news(
            item["title"]
        )

        print(analysis)

        telegram_message = format_telegram_message(
            item["title"],
            analysis
        )

        send_telegram_message(
            telegram_message
        )

        save_news(
            item["title"],
            item["source"],
            item["published"]
        )


if __name__ == "__main__":

    main()