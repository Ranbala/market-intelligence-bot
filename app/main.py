from fetchers.rss_fetcher import fetch_news
from fetchers.news_filter import filter_news
from ai.news_analyzer import analyze_news
from telegram_bot.sender import send_telegram_message
from fetchers.article_fetcher import fetch_full_article
from fetchers.filing_fetcher import fetch_nse_filings
from fetchers.filing_filter import filter_important_filings
from analyzers.filing_analyzer import analyze_filing
from fetchers.pdf_extractor import (
    extract_pdf_text,
    extract_pdf_text_from_bytes,
    extract_pdf_pages_from_bytes,
    extract_pdf_pages_with_ocr_from_bytes,
    is_text_extraction_poor
)
from analyzers.event_cluster import cluster_filings
from ai.filing_ai_router import (
    analyze_filing_with_llm
)
from dotenv import load_dotenv
from utils.date_extractor import extract_filing_dates
from utils.filing_printer import print_filing_event
import hashlib
from database import (
    init_db,
    news_exists,
    save_news,
    filing_exists,
    save_filing,
    filing_hash_exists,
    save_filing_hash
)
import re
from datetime import datetime
import requests
import time
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)
from analyzers.smart_pdf_analyzer import (
    extract_important_sections
)
from analyzers.nse_financial_result_extractor import (
    extract_financial_result_text_from_pages,
    is_likely_financial_results_pdf,
    detect_financial_unit_from_pages
)
from analyzers.event_engine import (
    extract_structured_events
)
from analyzers.filing_classifier import (
    classify_filing
)
from analyzers.financial_table_extractor import (
    extract_financial_metrics,
    generate_financial_insights
)
from analyzers.earnings_ai_context_builder import (
    build_earnings_ai_context
)
from analyzers.acquisition_ai_context_builder import (
    build_acquisition_ai_context
)
from analyzers.order_extractor import (
    extract_order_details
)

DEBUG_MODE = False

load_dotenv()

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

def format_percent(value):

    if value is None:
        return "N/A"

    sign = "+" if value > 0 else ""

    return f"{sign}{round(value, 2)}%"


def calculate_percent_change(current, previous):

    try:
        if current is None or previous in [None, 0]:
            return None

        return round(
            ((current - previous) / previous) * 100,
            2
        )

    except Exception:
        return None


def format_amount_for_telegram(value, financial_unit):

    if value is None:
        return "N/A"

    unit_name = (
        financial_unit or {}
    ).get(
        "display_unit",
        "reported units"
    )

    return f"{value} {unit_name}"


def format_change_phrase(current, previous):

    if current is None or previous is None:
        return "N/A"

    if current < 0 and previous < 0:
        if previous == 0:
            return "N/A"

        loss_change = round(
            ((abs(previous) - abs(current)) / abs(previous)) * 100,
            2
        )
        label = (
            "loss narrowed"
            if loss_change >= 0
            else "loss widened"
        )

        return f"{label} {format_percent(abs(loss_change))}"

    if current >= 0 and previous < 0:
        return "turned profitable"

    if current < 0 and previous >= 0:
        return "turned loss-making"

    return format_percent(
        calculate_percent_change(
            current,
            previous
        )
    )


def format_metric_snapshot(
    label,
    metric_data,
    financial_unit,
    profit_metric=False
):

    if (
        not metric_data
        or not metric_data.get("period_mapping_complete")
    ):
        return ""

    period_values = metric_data.get(
        "period_values",
        {}
    )

    year_current = period_values.get(
        "year_current"
    )
    year_previous = period_values.get(
        "year_previous"
    )
    quarter_current = period_values.get(
        "quarter_current"
    )
    quarter_previous_year = period_values.get(
        "quarter_previous_year"
    )

    year_change = (
        format_change_phrase(
            year_current,
            year_previous
        )
        if profit_metric
        else format_percent(
            calculate_percent_change(
                year_current,
                year_previous
            )
        )
    )

    quarter_yoy = (
        format_change_phrase(
            quarter_current,
            quarter_previous_year
        )
        if profit_metric
        else format_percent(
            calculate_percent_change(
                quarter_current,
                quarter_previous_year
            )
        )
    )

    return (
        f"\n• {label} FY: "
        f"{format_amount_for_telegram(year_current, financial_unit)} "
        f"vs {format_amount_for_telegram(year_previous, financial_unit)} "
        f"({year_change} YoY)"
        f"\n  Qtr: {format_amount_for_telegram(quarter_current, financial_unit)} "
        f"({quarter_yoy} YoY)"
    )


def build_financial_details_for_telegram(ai_summary):

    financial_metrics = ai_summary.get(
        "financial_metrics",
        {}
    )
    financial_unit = ai_summary.get(
        "financial_unit",
        {}
    )
    financial_insights = ai_summary.get(
        "financial_insights",
        {}
    )

    if not financial_metrics:
        return ""

    details = "\n📊 Key Numbers:"

    unit_name = financial_unit.get(
        "display_unit",
        "reported units"
    )
    details += f"\n• Unit: {unit_name}"

    details += format_metric_snapshot(
        "Revenue",
        financial_metrics.get("revenue"),
        financial_unit
    )
    details += format_metric_snapshot(
        "PAT",
        financial_metrics.get("profit_after_tax"),
        financial_unit,
        profit_metric=True
    )
    details += format_metric_snapshot(
        "PBT",
        financial_metrics.get("profit_before_tax"),
        financial_unit,
        profit_metric=True
    )

    if financial_insights.get(
        "pat_loss_narrowed_pct"
    ) is not None:
        details += (
            "\n• PAT Loss: narrowed "
            f"{format_percent(financial_insights.get('pat_loss_narrowed_pct'))} YoY"
        )

    if financial_insights.get(
        "pat_turnaround_from_loss"
    ):
        details += "\n• PAT: turned profitable from last year's loss"

    if financial_insights.get(
        "pat_declined_to_loss"
    ):
        details += "\n• PAT: declined from profit to loss"

    return details


def format_filing_telegram_message(
    analyzed,
    ai_summary,
    exchange_time,
    detected_dates
):

    stock = analyzed.get("symbol", "Unknown")
    company = (
        ai_summary.get("company_name")
        or analyzed.get("company_name")
        or analyzed.get("symbol", "Unknown")
    )
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
    
    filing_type = ai_summary.get(
        "filing_type",
        "Unknown"
        )
    tradeability = ai_summary.get(
        "tradeability",
        "N/A"
        )
    client_name = ai_summary.get(
        "client_name",""
    )
    order_value = ai_summary.get(
        "order_value_crore",
        ""
    )
    execution_period = ai_summary.get(
        "execution_period",
        ""
    )
    extra_details = ""
    if client_name:
        extra_details += (
            f"\n🤝 Client       : {client_name}"
            )
    if order_value:
        extra_details += (
            f"\n💰 Order Value  : ₹{order_value} Cr"
            )
    if execution_period:
        extra_details += (
            f"\n⏳ Execution    : {execution_period}"
            )

    financial_details = build_financial_details_for_telegram(
        ai_summary
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

📂 Filing Type  : {filing_type}

📌 Event        : {event}
📈 Sentiment    : {sentiment}
🔥 Importance   : {importance}/10
⚡ Tradeability : {tradeability}/10
{extra_details}
{financial_details}
🕒 NSE Time     : {exchange_time}
{important_dates}
🤖 EVENT SUMMARY:
{summary_text}
⚡ Market Impact:
{market_impact}
🎯 Key Event:
{event}
"""

    return telegram_message

def process_news_item(item):

    try:
        if news_exists(item["title"]):
            return (
                f"⏭ DUPLICATE SKIPPED: "
                f"{item['title'][:80]}"
                )

        full_article = fetch_full_article(
            item["link"]
        )

        content_for_ai = item["title"]

        if full_article:
            content_for_ai += (
                "\n\n"
                + full_article[:1500]
            )

        analysis = analyze_news(
            content_for_ai
        )

        if (
            not analysis
            or not isinstance(
                analysis,
                str
            )
        ):

            analysis = """
EVENT_TYPE: General Market News
SENTIMENT: Neutral
IMPORTANCE: 5
IMPACTED_STOCKS: Unknown
SUMMARY:
AI analysis unavailable. Fallback neutral classification used.
"""

        telegram_message = (
            format_telegram_message(
                item["title"],
                analysis,
                item["source"],
                item["published"]
            )
        )

        send_telegram_message(
            telegram_message
        )

        save_news(
            item["title"],
            item["source"],
            item["published"]
        )

        return (
            f"✅ DONE: "
            f"{item['title'][:80]}"
        )

    except Exception as e:

        return (
            f"❌ FAILED: "
            f"{item['title'][:80]} "
            f"| ERROR: {str(e)}"
        )



# =========================================================
# NSE FILING PIPELINE
# =========================================================

def run_nse_filing_pipeline():

    print("\n================ NSE FILINGS ================\n")
    filings = fetch_nse_filings()

    print("\n================ ALL NSE FILINGS ================\n")
    for idx, filing in enumerate(filings, start=1):
        print(
            f"{idx}. "
            f"{filing.get('symbol')} | "
            f"{filing.get('desc')} | "
            f"{filing.get('an_dt')} | "
            f"{filing.get('attchmntFile', '')[:80]}"
        )
    print("\n=================================================\n")

    important_filings = filter_important_filings(filings)

    if DEBUG_MODE:
        print(
            f"IMPORTANT FILINGS: "
            f"{len(important_filings)}"
        )

        for filing in important_filings:
            print(
                filing.get("symbol"),
                "|",
                filing.get("desc")
            )

    clustered_events = cluster_filings(
        important_filings
    )

    for cluster_key, cluster_filings_list in list(
        clustered_events.items()
    )[:10]:

        if DEBUG_MODE:
            print("\n" + "#" * 100)
            print(f"\n🔥 EVENT CLUSTER: {cluster_key}")
            print("#" * 100)

        combined_pdf_text = ""
        combined_pdf_pages = []

        sorted_cluster = sorted(
            cluster_filings_list,
            key=lambda x: analyze_filing(x)["importance"],
            reverse=True
        )

        primary_filing = sorted_cluster[0]

        analyzed = analyze_filing(primary_filing)
        exchange_time = (
            primary_filing.get("exchdisstime")
            or primary_filing.get("an_dt")
            or primary_filing.get("sort_date")
            or "Unknown"
        )

        for filing in cluster_filings_list:
            pdf_url = filing.get(
                "attchmntFile",
                ""
            )

            if pdf_url:
                try:
                    print(f"🔽 DOWNLOADING HASH PDF: {pdf_url}")
                    pdf_bytes = requests.get(
                        pdf_url,
                        timeout=(10, 60),
                        headers={
                            "User-Agent": "Mozilla/5.0"
                        }
                    ).content

                    file_hash = hashlib.sha256(
                        pdf_bytes
                    ).hexdigest()

                except Exception as e:
                    print(
                        f"❌ HASH DOWNLOAD FAILED: "
                        f"{pdf_url}"
                    )
                    print(str(e))
                    continue

                if filing_hash_exists(file_hash):
                    print(
                        f"⏭ DUPLICATE HASH SKIPPED: "
                        f"{pdf_url}"
                    )
                    continue

                pdf_pages = extract_pdf_pages_from_bytes(
                    pdf_bytes
                )

                if is_text_extraction_poor(pdf_pages):
                    pdf_pages = extract_pdf_pages_with_ocr_from_bytes(
                        pdf_bytes,
                        existing_pages=pdf_pages
                    )

                if pdf_pages:
                    combined_pdf_pages.extend(
                        pdf_pages
                    )

                    pdf_text = "\n".join(
                        page["text"]
                        for page in pdf_pages
                        if page.get("text")
                    )

                else:
                    pdf_text = extract_pdf_text_from_bytes(
                        pdf_bytes
                    )

                combined_pdf_text += (
                    "\n\n" + pdf_text
                )

        if not combined_pdf_text.strip():
            print(
                "⏭ ENTIRE CLUSTER SKIPPED "
                "(ALL PDFs DUPLICATE)"
            )
            continue

        detected_dates = extract_filing_dates(
            combined_pdf_text
        )

        if is_likely_financial_results_pdf(
            combined_pdf_pages
        ):
            smart_text = extract_financial_result_text_from_pages(
                combined_pdf_pages
            )
            financial_unit = detect_financial_unit_from_pages(
                combined_pdf_pages
            )
        else:
            smart_text = extract_important_sections(
                combined_pdf_text
                )
            financial_unit = {
                "currency": "INR",
                "unit": "unknown",
                "display_unit": "reported units",
                "scale": None,
                "source_line": None,
            }
        if smart_text.strip():
            structured_events = extract_structured_events(
                smart_text
                )
            filing_type_result = classify_filing(
                smart_text
                )
            financial_metrics = {}
            financial_insights = {}
            order_details = {}
            
            if filing_type_result["filing_type"] == "earnings":
                financial_metrics = extract_financial_metrics(
                    smart_text
                    )
            
                financial_insights = generate_financial_insights(
                    financial_metrics
                    )
            
            if filing_type_result["filing_type"] == "order_win":
                order_details = extract_order_details(
                    smart_text
                    )

            structured_context = {
                "structured_events": structured_events,
                "filing_analysis": analyzed,
                "filing_type": filing_type_result,
                "financial_unit": financial_unit,
                "financial_metrics": financial_metrics,
                "financial_insights": financial_insights,
                "order_details": order_details
                }

            ai_input_text = smart_text

            if filing_type_result["filing_type"] == "earnings":
                ai_input_text = build_earnings_ai_context(
                    smart_text,
                    structured_context
                )

            if filing_type_result["filing_type"] in [
                "acquisition",
                "open_offer",
            ]:
                ai_input_text = build_acquisition_ai_context(
                    combined_pdf_text,
                    structured_context
                )

            ai_summary = analyze_filing_with_llm(
                ai_input_text,
                structured_context
                )
            # =====================================================
            # ENRICH AI SUMMARY WITH STRUCTURED DATA
            # =====================================================
            
            primary_event = {}
            if structured_events.get("events"):
                primary_event = structured_events["events"][0]
            ai_summary["filing_type"] = filing_type_result.get(
                "filing_type",
                "Unknown"
            )
            ai_summary["tradeability"] = primary_event.get(
                "tradeability",
                "N/A"
            )
            ai_summary.update(order_details)
            ai_summary["financial_insights"] = (
                financial_insights
                )
            ai_summary["financial_metrics"] = (
                financial_metrics
                )
            ai_summary["financial_unit"] = (
                financial_unit
                )
        else:
            fallback_importance = 5
            fallback_sentiment = "Neutral"
            pdf_lower = combined_pdf_text.lower()

            if "financial results" in pdf_lower:
                fallback_importance = 9
                fallback_sentiment = "Positive"
            if "dividend" in pdf_lower:
                fallback_importance = max(fallback_importance, 8)
                fallback_sentiment = "Positive"
            if "acquisition" in pdf_lower:
                fallback_importance = max(fallback_importance, 9)
                fallback_sentiment = "Positive"
            if "board meeting" in pdf_lower:
                fallback_importance = max(fallback_importance, 7)
            if "qip" in pdf_lower:
                fallback_importance = max(fallback_importance, 8)
            if "cirp" in pdf_lower:
                fallback_importance = max(fallback_importance, 9)
                fallback_sentiment = "Negative"

            ai_summary = {
                "summary_points": [
                    "Fallback rule-based analysis used."
                ],
                "sentiment": fallback_sentiment,
                "importance": fallback_importance,
                "key_event": analyzed.get(
                    "event_type",
                    "Corporate Filing"
                ),
                "market_impact": (
                    "Rule-based fallback engine detected "
                    "important corporate filing."
                )
            }

        event_name = ai_summary.get(
            "key_event",
            analyzed.get("event_type", "Unknown")
        )

        symbol = analyzed.get("symbol", "UNKNOWN")

        attachment_urls = []

        for filing in cluster_filings_list:
            pdf_url = filing.get("attchmntFile", "")

            if pdf_url:
                attachment_urls.append(pdf_url)

        attachment_key = "|".join(sorted(attachment_urls))

        unique_filing_id = (
            f"{symbol}_"
            f"{attachment_key}"
        )

        print(
            f"NSE DEDUPE KEY: {unique_filing_id[:120]}"
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

        if ai_summary.get("importance", 0) >= 5:

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

        for filing in cluster_filings_list:
            pdf_url = filing.get("attchmntFile", "")
            
            if not pdf_url:
                continue
            try:
                pdf_bytes = requests.get(
                    pdf_url,
                    timeout=(10, 60),
                    headers={
                        "User-Agent": "Mozilla/5.0"
                        }
                        ).content
                file_hash = hashlib.sha256(
                        pdf_bytes
                        ).hexdigest()
                save_filing_hash(
                    symbol=primary_filing["symbol"],
                    file_hash=file_hash,
                    normalized_hash=None,
                    source_url=pdf_url,
                    file_name=pdf_url.split("/")[-1],
                    exchange_time=exchange_time,
                    processing_status="SUCCESS",
                    ai_processed=1,
                    ai_provider=None
                    )
            except Exception as e:
                print(f"❌ HASH SAVE FAILED: {pdf_url}")
                print(str(e))

    print("\n✅ Filing intelligence engine completed successfully.\n")

# =========================================================
# RSS NEWS PIPELINE
# =========================================================

def run_rss_news_pipeline():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    debug_file = open(
        f"debug_news_{timestamp}.txt",
        "w",
        encoding="utf-8"
    )

    raw_news = fetch_news()

    filtered_news = filter_news(raw_news)
    source_count = {}

    for item in filtered_news:
        source = item["source"]
        source_count[source] = source_count.get(source, 0) + 1

    print("\nFILTERED SOURCE BREAKDOWN:\n")

    priority_news = []

    priority_keywords = [
        "results",
        "profit",
        "revenue",
        "earnings",
        "ebitda",
        "margin",
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
        "sensex",
        "nifty",
        "bank nifty",
        "52-week",
        "all-time high",
        "record high"
    ]

    for item in filtered_news:

        title = item["title"].lower()

        if any(keyword in title for keyword in priority_keywords):
            priority_news.append(item)

    priority_news = sorted(
        priority_news,
        key=lambda x: x["published"]
    )

    print(
        f"\n🚀 Processing "
        f"{len(priority_news)} news items "
        f"using parallel threads...\n"
    )

    with ThreadPoolExecutor(
        max_workers=5
    ) as executor:

        futures = [
            executor.submit(
                process_news_item,
                item
            )
            for item in priority_news
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                print(result)

    debug_file.close()

    print(f"\nDebug news exported successfully.")


# =========================================================
# MAIN
# =========================================================

def main():
    init_db()

    run_nse_filing_pipeline()

    run_rss_news_pipeline()

if __name__ == "__main__":

    main()
