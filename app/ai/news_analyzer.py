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

def build_prompt(news_text):

    return f"""
You are an expert Indian stock market intelligence AI.

Analyze the below financial news article carefully.

Your goals:

1. Identify impacted Indian stocks.
2. Identify impacted sectors if applicable.
3. Detect whether impact is Positive, Negative or Neutral.
4. Classify the market event type.
5. Give importance score from 1-10.
6. Write short easy-English actionable summary.
7. Ignore recommendation/advisory style content.

VERY IMPORTANT:

- If company names are directly mentioned,
  include them in IMPACTED_STOCKS.

- If the company names are not directly mentioned, then check this news can impact which stocks and add those in the IMPACTED_STOCKS

- If macro news affects sectors,
  infer major Indian stocks.

Examples:

Weak Rupee:
Infosys, TCS, Wipro

Oil Price Rise:
ONGC, Oil India, Indigo

Rate Cuts:
HDFC Bank, ICICI Bank

Return STRICTLY in this format:

IMPACTED_STOCKS: comma separated names

EVENT_TYPE: short event type

SENTIMENT: Positive / Negative / Neutral

IMPORTANCE: 1-10

SUMMARY: short simple-English summary

NEWS ARTICLE:
{news_text}
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

def analyze_news(news_text):

    prompt = build_prompt(news_text)

    # TRY GEMINI FIRST
    try:

        print("Using Gemini AI...")

        return analyze_with_gemini(prompt)

    except Exception as gemini_error:

        print(f"Gemini failed: {gemini_error}")
        print("Switching to Groq AI...")

    # FALLBACK TO GROQ
    try:

        print("Using Groq AI...")

        return analyze_with_groq(prompt)

    except Exception as groq_error:

        return f'''
AI ANALYSIS FAILED

GEMINI ERROR:
{str(gemini_error)}

GROQ ERROR:
{str(groq_error)}
'''