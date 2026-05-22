import os
from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv()

# =========================================================
# GEMINI SETUP
# =========================================================

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

GEMINI_MODEL = "gemini-3.5-flash"

# =========================================================
# GROQ SETUP
# =========================================================

groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

GROQ_MODEL = "openai/gpt-oss-20b"

# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(title):

    return f"""
You are a stock market intelligence AI.

Analyze this market news headline.

Headline:
{title}

Return STRICTLY in this format:

EVENT_TYPE: <type>

SENTIMENT: <Positive/Negative/Neutral>

IMPORTANCE: <1-10>

SUMMARY: <2-line summary>

Only return these fields.
Keep the summary in simple easy English.
"""

# =========================================================
# GEMINI ANALYSIS
# =========================================================

def analyze_with_gemini(prompt):

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text

# =========================================================
# GROQ ANALYSIS
# =========================================================

def analyze_with_groq(prompt):

    response = groq_client.responses.create(
        model=GROQ_MODEL,
        input=prompt
    )

    return response.output_text

# =========================================================
# MAIN ANALYZER
# =========================================================

def analyze_news(title):

    prompt = build_prompt(title)

    # TRY GEMINI FIRST
    try:

        print("Using Gemini AI...")

        return analyze_with_gemini(prompt)

    except Exception as gemini_error:

        print("Gemini quota exceeded. Switching to Groq AI...")

    # FALLBACK TO GROQ
    try:

        print("Using Groq AI...")

        return analyze_with_groq(prompt)

    except Exception as groq_error:

        return f"""
AI ANALYSIS FAILED

GEMINI ERROR:
{str(gemini_error)}

GROQ ERROR:
{str(groq_error)}
"""