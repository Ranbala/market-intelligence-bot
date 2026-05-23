def print_filing_event(
    analyzed,
    ai_summary,
    exchange_time,
    detected_dates,
    combined_pdf_text
):

    print("\n" + "=" * 80)

    print("🚨 EARLY CORPORATE EVENT\n")

    print(f"🏢 Stock        : {analyzed['symbol']}")
    print(f"🏛 Company      : {analyzed['company']}")
    print(f"📌 Event        : {analyzed['event']}")

    final_sentiment = ai_summary.get(
        "sentiment",
        analyzed["sentiment"]
    )

    print(f"📈 Sentiment    : {final_sentiment}")

    print(
        f"🔥 Importance   : "
        f"{ai_summary.get('importance', analyzed['importance'])}/10"
    )

    print(f"🕒 Time         : {analyzed['time']}")

    print(
        f"📅 NSE Filing Time : "
        f"{exchange_time}"
    )

    print(
        f"📄 Dates Found In PDF : "
        f"{detected_dates}"
    )

    print("\n🤖 AI EVENT SUMMARY:\n")

    for point in ai_summary["summary_points"]:
        print(f"• {point}")

    print(
        f"\n📈 AI Sentiment: "
        f"{ai_summary['sentiment']}"
    )

    print("\n⚡ Market Impact:")
    print(
        ai_summary.get(
            "market_impact",
            analyzed["impact"]
        )
    )

    print("\n🎯 Key Event:")
    print(
        ai_summary.get(
            "key_event",
            "Unknown"
        )
    )

    print("\n📄 COMBINED PDF PREVIEW:\n")
    print(combined_pdf_text[:3000])

    print("\n" + "=" * 80)