import os
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
import threading
import time

load_dotenv()

cerebras_lock = threading.Lock()
last_cerebras_call = 0

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
# CEREBRAS SETUP
# =========================================================

cerebras_client = OpenAI(
    api_key=os.getenv("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1"
)

#CEREBRAS_MODEL = "gpt-oss-120b"
CEREBRAS_MODEL = "llama3.1-8b"

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
# CEREBRAS ANALYSIS
# =========================================================

def analyze_with_cerebras(prompt):

    global last_cerebras_call
    with cerebras_lock:
        current_time = time.time()
        elapsed = (current_time - last_cerebras_call)
        
        if elapsed < 2:
            time.sleep(2 - elapsed)
        last_cerebras_call = time.time()
    
    response = cerebras_client.chat.completions.create(
        model=CEREBRAS_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=1500
    )

    if (not response.choices or not response.choices[0].message):
        raise Exception(
            "Invalid response from Cerebras")
    result = (response.choices[0].message.content)

    if not result or not result.strip():

        response = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=1500
        )

        result = response.choices[0].message.content

    if not result or not result.strip():

        raise Exception(
            "Empty response from Cerebras"
        )

    return result

# =========================================================
# MAIN ANALYZER
# =========================================================

def analyze_news(news_text):

    prompt = build_prompt(news_text)

    cerebras_error = None
    groq_error = None
    gemini_error = None

    # =====================================================
    # TRY CEREBRAS FIRST
    # =====================================================

    try:

        print("Using Cerebras AI...")

        return analyze_with_cerebras(prompt)

    except Exception as e:

        cerebras_error = e

        print(f"Cerebras failed: {e}")
        print("Switching to Groq AI...")

    # =====================================================
    # TRY GROQ
    # =====================================================

    try:

        print("Using Groq AI...")

        return analyze_with_groq(prompt)

    except Exception as e:

        groq_error = e

        print(f"Groq failed: {e}")
        print("Switching to Gemini AI...")

    # =====================================================
    # TRY GEMINI
    # =====================================================

    try:

        print("Using Gemini AI...")

        return analyze_with_gemini(prompt)

    except Exception as e:

        gemini_error = e

        print(f"Gemini failed: {e}")

    # =====================================================
    # FINAL FALLBACK
    # =====================================================

    return f"""
IMPACTED_STOCKS: Unknown

EVENT_TYPE: Unknown

SENTIMENT: Neutral

IMPORTANCE: 5

SUMMARY:
AI analysis unavailable. Fallback neutral classification used.
"""