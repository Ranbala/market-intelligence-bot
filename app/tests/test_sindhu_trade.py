test_filing = {
        "symbol": "SINDHUTRAD",
        "companyName": "Sindhu Trade Links Limited",
        "subject": "Strategic Acquisition and Preferential Issue",
        "dateTime": "22-May-2026 17:27:06",
        "attchmntFile": "https://nsearchives.nseindia.com/corporate/SINDHUTRAD_22052026172706_Outcome22052026Signed.pdf"
    }

    print("\n================ SINDHU TRADE FULL TEST ================\n")

    combined_pdf_text = ""

    pdf_text = extract_pdf_text(
        test_filing["attchmntFile"]
    )

    combined_pdf_text += pdf_text

    detected_dates = extract_filing_dates(
        combined_pdf_text
    )

    analyzed = analyze_filing(
        test_filing
    )

    ai_summary = analyze_filing_with_llm(
        combined_pdf_text
    )

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
    print(f"🔥 Importance   : {ai_summary.get('importance', analyzed['importance'])}/10")

    print(f"🕒 NSE Time     : {test_filing['dateTime']}")

    print(f"📄 Dates Found  : {detected_dates}")

    print("\n🤖 AI EVENT SUMMARY:\n")

    for point in ai_summary["summary_points"]:
        print(f"• {point}")

    print(f"\n📈 AI Sentiment: {ai_summary['sentiment']}")

    print("\n⚡ Market Impact:")
    print(ai_summary.get("market_impact", "Unknown"))

    print("\n🎯 Key Event:")
    print(ai_summary.get("key_event", "Unknown"))

    print("\n📄 PDF PREVIEW:\n")
    print(combined_pdf_text[:3000])

    print("\n" + "=" * 80)