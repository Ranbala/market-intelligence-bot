from fetchers.rss_fetcher import fetch_news
from fetchers.news_filter import filter_news
from ai.news_analyzer import analyze_news
from telegram_bot.sender import send_telegram_message
from fetchers.article_fetcher import fetch_full_article
from fetchers.filing_fetcher import fetch_nse_filings
from fetchers.filing_filter import filter_important_filings
from analyzers.filing_analyzer import analyze_filing
from fetchers.pdf_extractor import extract_pdf_text
from analyzers.event_cluster import cluster_filings
from services.llm_router import (
    analyze_filing_with_llm
)
from dotenv import load_dotenv
from utils.date_extractor import extract_filing_dates
from utils.filing_printer import print_filing_event
from database import create_tables

load_dotenv()

from database import (
    init_db,
    news_exists,
    save_news,
    filing_exists,
    save_filing
)

import re
from datetime import datetime


# =========================================================
# TELEGRAM MESSAGE FORMATTER
# =========================================================

def format_telegram_message(title, analysis, source, published_time):

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

    impacted_match = re.search(
        r"IMPACTED_STOCKS:\s*(.*)",
        analysis
    )

    if event_match:
        event_type = event_match.group(1).strip()

    if sentiment_match:
        sentiment = sentiment_match.group(1).strip()

    if importance_match:
        importance = importance_match.group(1).strip()

    if summary_match:
        summary = summary_match.group(1).strip()

    impacted_stocks = "Not identified"

    if impacted_match:
        impacted_stocks = impacted_match.group(1).strip()

    telegram_message = f"""
🚨 MARKET IMPACT ALERT

📰 {title}

🎯 Impacted Stocks: {impacted_stocks}

📌 Event: {event_type}
📈 Sentiment: {sentiment}
🔥 Importance: {importance}/10

🧾 News Source: {source}
🕒 Published: {published_time}

💡 AI Summary:
{summary}
"""

    return telegram_message

# =========================================================
# FILING TELEGRAM FORMATTER
# =========================================================

def format_filing_telegram_message(
    analyzed,
    ai_summary,
    exchange_time,
    detected_dates
):

    stock = analyzed.get("symbol", "Unknown")
    company = analyzed.get( "company_name") or analyzed.get("symbol","Unknown")
    event = ai_summary.get(
        "key_event",
        analyzed.get("event_type", "Corporate Filing")
    )

    sentiment = ai_summary.get("sentiment", "Neutral")
    importance = ai_summary.get("importance", 5)
    market_impact = ai_summary.get(
        "market_impact",
        "Unknown"
    )

    summary_points = ai_summary.get(
        "summary_points",
        []
    )

    summary_text = ""

    for point in summary_points:
        summary_text += f"• {point}\n"

    important_dates = ""

    if detected_dates:
        important_dates = "\n📅 Important Dates:\n"

        for date in detected_dates[:5]:
            important_dates += f"• {date}\n"

    telegram_message = f"""
🚨 EARLY CORPORATE EVENT

🏢 Stock        : {stock}
🏛 Company      : {company}
📌 Event        : {event}
📈 Sentiment    : {sentiment}
🔥 Importance   : {importance}/10
🕒 NSE Time     : {exchange_time}
{important_dates}
🤖 AI EVENT SUMMARY:

{summary_text}
⚡ Market Impact:
{market_impact}

🎯 Key Event:
{event}
"""

    return telegram_message

# =========================================================
# MAIN
# =========================================================

def main():

    init_db()
    create_tables()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_file = open(
    f"debug_news_{timestamp}.txt",
    "w",
    encoding="utf-8"
)
    raw_news = fetch_news()
    
    print("\n================ NSE FILINGS ================\n")
    filings = fetch_nse_filings()
    important_filings = filter_important_filings(filings)
    
    clustered_events = cluster_filings(
        important_filings
        )

    for cluster_key, cluster_filings_list in list(
        clustered_events.items()
    )[:10]:

        print("\n" + "#" * 100)
        print(f"\n🔥 EVENT CLUSTER: {cluster_key}")
        print("#" * 100)

        combined_pdf_text = ""

        # Highest importance filing
        sorted_cluster = sorted(
            cluster_filings_list,
            key=lambda x: analyze_filing(x)["importance"],
            reverse=True
        )

        primary_filing = sorted_cluster[0]

        analyzed = analyze_filing(primary_filing)
        exchange_time = primary_filing.get(
            "dateTime",
            "Unknown"
            )

        for filing in cluster_filings_list:
            pdf_url = filing.get(
                "attchmntFile",
                ""
                )
            if pdf_url:
                pdf_text = extract_pdf_text(pdf_url)
                combined_pdf_text += (
                    "\n\n" + pdf_text[:30000]
                )
        detected_dates = extract_filing_dates(
            combined_pdf_text
            )

        if combined_pdf_text.strip():
            ai_summary = analyze_filing_with_llm(
                combined_pdf_text
                )
        else:
            ai_summary = {
                "summary_points": [
                    "No PDF content available for AI analysis."
                ],
                "sentiment": "Neutral",
                "importance": 5,
                "key_event": analyzed.get(
                    "event_type",
                    "Corporate Filing"
                )
            }

        event_name = ai_summary.get(
            "key_event",
            analyzed.get("event_type", "Unknown")
            )
        
        symbol = analyzed.get("symbol","UNKNOWN")
        
        unique_filing_id = (
            f"{symbol}_"
            f"{exchange_time}_"
            f"{event_name}"
            )
        
        if filing_exists(unique_filing_id):
            print(
                f"SKIPPED NSE DUPLICATE | "
                f"SYMBOL: {symbol} | "
                f"EVENT: {event_name}"
            )
            continue

        print_filing_event(
            analyzed,
            ai_summary,
            exchange_time,
            detected_dates,
            combined_pdf_text
            )

        if ai_summary.get("importance", 0) >= 7:

            telegram_message = format_filing_telegram_message(
                analyzed,
                ai_summary,
                exchange_time,
                detected_dates
            )
            
            send_telegram_message(
                telegram_message
            )

            save_filing(
                unique_filing_id,
                symbol,
                event_name,
                exchange_time
                )

    print("\n✅ Filing intelligence engine completed successfully.\n")
    
    header = (
        "\n" + "=" * 120 + "\n"
        + "ALL RAW NEWS FOR VALIDATION\n"
        + "=" * 120
    )

    #print(header)
    #debug_file.write(header + "\n")
    
    for idx, item in enumerate(raw_news, start=1):

        raw_message = (
            f"\n{idx}. SOURCE     : {item['source']}\n"
            f"TITLE           : {item['title']}\n"
            f"PUBLISHED       : {item['published']}\n"
            + "-" * 120
        )

        #print(raw_message)
        #debug_file.write(raw_message + "\n")

    raw_count_message = f"\nRAW NEWS COUNT: {len(raw_news)}\n"

    #print(raw_count_message)
    #debug_file.write(raw_count_message)

    filtered_news = filter_news(raw_news)
    source_count = {}
    
    for item in filtered_news:
        source = item["source"]
        source_count[source] = source_count.get(source, 0) + 1
    print("\nFILTERED SOURCE BREAKDOWN:\n")
    
    #for source, count in source_count.items():
    #    print(f"{source}: {count}")
    
    #filtered_count_message = (
    #    f"\nFILTERED NEWS COUNT: {len(filtered_news)}\n"
   # )

    #print(filtered_count_message)
    #debug_file.write(filtered_count_message)

    priority_news = []

    priority_keywords = [

    # Earnings / finance
    "results",
    "profit",
    "revenue",
    "earnings",
    "ebitda",
    "margin",

    # Corporate actions
    "dividend",
    "bonus",
    "split",
    "buyback",
    "stake",
    "ofs",
    "ipo",
    "merger",
    "acquisition",
    "deal",
    "approval",
    "investment",
    "order",

    # Stock movement
    "shares",
    "stock",
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

    # Macro / markets
    "rbi",
    "fed",
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

    # Markets
    "sensex",
    "nifty",
    "bank nifty",

    # Important levels
    "52-week",
    "all-time high",
    "record high"
]

    for item in filtered_news:

        title = item["title"].lower()

        if any(keyword in title for keyword in priority_keywords):
            priority_news.append(item)
        else:
            pass

    priority_news = sorted(
        priority_news,
        key=lambda x: x["published"]
    )

    for idx, item in enumerate(priority_news, start=1):
        if news_exists(item["title"]):
            continue

        print("=" * 120)

        print(f"\n{idx}. SOURCE     : {item['source']}")

        print(f"TITLE           : {item['title']}")

        print(f"PUBLISHED       : {item['published']}")

        print("\nAI ANALYSIS:\n")

        full_article = fetch_full_article(
            item["link"]
            )
        content_for_ai = item["title"]
        if full_article:
            content_for_ai += "\n\n" + full_article[:5000]
        
        analysis = analyze_news(content_for_ai)

        print(analysis)

        telegram_message = format_telegram_message(
            item["title"],
            analysis,
            item["source"],
            item["published"]
        )

        send_telegram_message(
            telegram_message
        )

        save_news(
            item["title"],
            item["source"],
            item["published"]
        )

    debug_file.close()

    print(f"\nDebug news exported successfully.")


if __name__ == "__main__":

    main()