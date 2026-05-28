from analyzers.event_taxonomy import EVENT_PATTERNS
import re

def extract_structured_events(text):

    if not text:
        return {
            "events": [],
            "narratives": []
            }

    text_lower = text.lower()

    detected_events = []

    narratives = []

    for event_type, config in EVENT_PATTERNS.items():
        required_keywords = config.get(
            "required_keywords",
            []
        )
        
        optional_keywords = config.get(
            "optional_keywords",
            []
        )
        
        negative_keywords = config.get(
            "negative_keywords",
            []
        )

        minimum_optional_matches = config.get(
            "minimum_optional_matches",
            0
            )
        
        matched_required = [
            kw for kw in required_keywords
            if re.search(
                r"\b" + re.escape(kw.lower()) + r"\b",
                text_lower
                )
            ]
            
        matched_optional = [
            kw for kw in optional_keywords
            if re.search(
                r"\b" + re.escape(kw.lower()) + r"\b",
                text_lower
            )
            ]
        
        matched_negative = [
            kw for kw in negative_keywords
            if re.search(
                r"\b" + re.escape(kw.lower()) + r"\b",
                text_lower
                )
            ]
        
        negative_match = (
            len(matched_negative) > 0
            )
        
        score = 0
        
        score += len(matched_required) * 3
        score += len(matched_optional) * 1
        score -= len(matched_negative) * 5
        
        if len(matched_optional) < minimum_optional_matches:
            continue

        if score >= 3 and not negative_match:
            
            confidence = score
            
            detected_events.append({
                "event_type": event_type,
                "matched_keywords": matched_required + matched_optional,
                "importance":
                    config["importance"],
                "tradeability":
                    config["tradeability"],
                "sentiment":
                    config["sentiment"],
                "confidence":
                    confidence
            })

    # =========================
    # MARKET NARRATIVE DETECTION
    # =========================

    if (
        "nclt" in text_lower
        or "insolvency" in text_lower
        or "debt restructuring" in text_lower
        or "narcl" in text_lower
        ):

        narratives.append({
            "narrative": "distressed_turnaround",
            "description": (
                "Company may be undergoing financial restructuring "
                "or survival turnaround."
                ),
                "market_behavior": (
                    "High speculative momentum possible."
                    )
                })
    if (
        "capacity expansion" in text_lower
        or "new plant" in text_lower
        or "capex" in text_lower
        ):

        narratives.append({
            "narrative": "growth_expansion",
            "description": (
                "Company is expanding operational capacity."
            ),
            "market_behavior": (
                "Long-term growth expectations may improve."
            )
        })


    if (
        "analyst" in text_lower
        or "investor meeting" in text_lower
        or "institutional investor" in text_lower
    ):

        narratives.append({
            "narrative": "institutional_interest",
            "description": (
                "Management interacting with institutions."
            ),
            "market_behavior": (
                "Possible institutional accumulation interest."
            )
        })

    overall_tradeability = 0

    if detected_events:
        overall_tradeability = max(
            event["tradeability"]
            for event in detected_events
        )

    return {
        "events": detected_events,
        "narratives": narratives
        }