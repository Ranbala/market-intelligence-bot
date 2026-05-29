import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)
from analyzers.filing_classifier import (
    classify_filing
)
from fetchers.pdf_extractor import (
    extract_pdf_text,
    extract_pdf_text_from_bytes,
    extract_pdf_pages_from_bytes,
    extract_pdf_pages_with_ocr_from_bytes,
    is_text_extraction_poor
)
from analyzers.financial_table_extractor import (
    extract_financial_metrics,
    generate_financial_insights
)
from analyzers.order_extractor import (
    extract_order_details
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

from analyzers.earnings_ai_context_builder import (
    build_earnings_ai_context
)

from analyzers.acquisition_ai_context_builder import (
    build_acquisition_ai_context
)

from ai.filing_ai_router import (
    analyze_filing_with_llm
)



# ==========================================
# LOCAL PDF PATH
# ==========================================

PDF_PATH = (
    "/Users/balakumarmoorthy/Downloads/NSE Filings reprocess/BATAINDIA_27052026190204_SE-Outcome-May27-2026_signed.pdf"
)

if len(sys.argv) > 1:
    PDF_PATH = sys.argv[1]

RUN_AI_ANALYSIS = True
SMART_TEXT_PREVIEW_CHARS = 1200


def estimate_tokens(text):

    return round(
        len(text or "") / 4
    )


# ==========================================
# STEP 1 - EXTRACT PDF TEXT
# ==========================================

print("\n" + "=" * 100)
print("STEP 1 - EXTRACTING PDF TEXT")
print("=" * 100)

with open(PDF_PATH, "rb") as f:

    pdf_bytes = f.read()

pdf_text = extract_pdf_text_from_bytes(
    pdf_bytes
)

pdf_pages = extract_pdf_pages_from_bytes(
    pdf_bytes
)

if is_text_extraction_poor(pdf_pages):
    print("\nPDF text layer looks weak. Trying OCR fallback...")
    pdf_pages = extract_pdf_pages_with_ocr_from_bytes(
        pdf_bytes,
        existing_pages=pdf_pages
    )
    pdf_text = "\n".join(
        page["text"]
        for page in pdf_pages
        if page.get("text")
    )

print("\nPDF TEXT EXTRACTED")
print(f"Total Characters: {len(pdf_text)}")
print(f"Total Pages: {len(pdf_pages)}")


# ==========================================
# STEP 2 - SMART PDF EXTRACTION
# ==========================================

print("\n" + "=" * 100)
print("STEP 2 - SMART PDF EXTRACTION")
print("=" * 100)

if is_likely_financial_results_pdf(pdf_pages):
    smart_text = extract_financial_result_text_from_pages(
        pdf_pages
    )
    financial_unit = detect_financial_unit_from_pages(
        pdf_pages
    )
else:
    smart_text = extract_important_sections(
        pdf_text
    )
    financial_unit = {
        "currency": "INR",
        "unit": "unknown",
        "display_unit": "reported units",
        "scale": None,
        "source_line": None,
    }

print("\nSMART EXTRACTED TEXT:\n")
print(smart_text[:SMART_TEXT_PREVIEW_CHARS])
print(f"\nSmart Text Characters: {len(smart_text)}")
print(f"Financial Unit: {financial_unit}")

print("\n" + "="*100)
print("STEP 2.5 - FILING CLASSIFICATION")
print("="*100)

filing_type_result = classify_filing(
    smart_text
)

print("\nFILING CLASSIFICATION:\n")
print(filing_type_result)

# ==========================================
# STEP 3 - EVENT EXTRACTION
# ==========================================

print("\n" + "=" * 100)
print("STEP 3 - STRUCTURED EVENT EXTRACTION")
print("=" * 100)

structured_events = extract_structured_events(
    smart_text
)

print("\nDETECTED EVENTS:\n")
print(structured_events)

# ==========================================
# STEP 4 - FINANCIAL METRICS EXTRACTION
# ==========================================

print("\n" + "=" * 100)
print("STEP 4 - FINANCIAL METRICS")
print("=" * 100)

financial_metrics = {}

# ==========================================
# ORDER DETAILS EXTRACTION
# ==========================================

if filing_type_result["filing_type"] == "order_win":
    order_details = extract_order_details(
        pdf_text
        )

    print(order_details)

# ==========================================
# EARNINGS EXTRACTION
# ==========================================
if filing_type_result["filing_type"] == "earnings":

    financial_metrics = extract_financial_metrics(
        smart_text
    )

print("\nEXTRACTED FINANCIAL METRICS:\n")
print(financial_metrics)


financial_insights = generate_financial_insights(
    financial_metrics
)

print("\nGENERATED FINANCIAL INSIGHTS:\n")
print(financial_insights)

structured_context = {
    "filing_type": filing_type_result,
    "structured_events": structured_events,
    "financial_unit": financial_unit,
    "financial_metrics": financial_metrics,
    "financial_insights": financial_insights,
    "period_label_meaning": {
        "quarter_current": "Current quarter",
        "quarter_previous": "Previous quarter",
        "quarter_previous_year": "Same quarter previous year",
        "year_current": "Current full financial year",
        "year_previous": "Previous full financial year"
    }
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
        pdf_text,
        structured_context
    )

# ==========================================
# STEP 5 - AI ANALYSIS
# ==========================================

print("\n" + "=" * 100)
print("STEP 4 - AI ANALYSIS")
print("=" * 100)
print(f"Raw Smart Text Characters: {len(smart_text)}")
print(f"Raw Smart Text Estimated Tokens: {estimate_tokens(smart_text)}")
print(f"Compact AI Text Characters: {len(ai_input_text)}")
print(f"Compact AI Text Estimated Tokens: {estimate_tokens(ai_input_text)}")
print(
    "Structured Context Estimated Tokens: "
    f"{estimate_tokens(str(structured_context))}"
)
print(
    "Total Estimated Input Tokens: "
    f"{estimate_tokens(ai_input_text) + estimate_tokens(str(structured_context))}"
)
print("\nCOMPACT AI INPUT PREVIEW:\n")
print(ai_input_text[:SMART_TEXT_PREVIEW_CHARS])

if RUN_AI_ANALYSIS:
    ai_result = analyze_filing_with_llm(
        ai_input_text,
        structured_context
    )
else:
    ai_result = {
        "skipped": True,
        "reason": "RUN_AI_ANALYSIS is False"
    }

print("\nAI RESULT:\n")
print(ai_result)
