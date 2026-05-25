import sqlite3
import os

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "news.db"
)


def init_db():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            source TEXT,
            published TEXT
        )
    """)

    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS processed_nse_filings (

        unique_id TEXT PRIMARY KEY,
        symbol TEXT,
        event_name TEXT,
        exchange_time TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """
)

    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS nse_filing_processing (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        symbol TEXT,

        file_hash TEXT UNIQUE,

        normalized_hash TEXT,

        source_url TEXT,

        file_name TEXT,

        exchange_time TEXT,

        processing_status TEXT,

        ai_processed INTEGER DEFAULT 0,

        ai_provider TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """
)

    conn.commit()
    conn.close()


def news_exists(title):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM processed_news WHERE title = ?",
        (title,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def save_news(title, source, published):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO processed_news (
            title,
            source,
            published
        )
        VALUES (?, ?, ?)
    """, (title, source, published))

    conn.commit()
    conn.close()

def filing_exists(unique_id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM processed_nse_filings
        WHERE unique_id = ?
        """,
        (unique_id,)
    )
    result = cursor.fetchone()
    conn.close()

    return result is not None

def save_filing(

    unique_id,
    symbol,
    event_name,
    exchange_time

):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO processed_nse_filings (

            unique_id,
            symbol,
            event_name,
            exchange_time

        )
        VALUES (?, ?, ?, ?)
        """,
        (
            unique_id,
            symbol,
            event_name,
            exchange_time
        )
    )

    conn.commit()
    conn.close()


# New functions for nse_filing_processing table

def filing_hash_exists(file_hash):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM nse_filing_processing
        WHERE file_hash = ?
        """,
        (file_hash,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def save_filing_hash(

    symbol,
    file_hash,
    normalized_hash,
    source_url,
    file_name,
    exchange_time,
    processing_status,
    ai_processed=0,
    ai_provider=None

):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO nse_filing_processing (

            symbol,
            file_hash,
            normalized_hash,
            source_url,
            file_name,
            exchange_time,
            processing_status,
            ai_processed,
            ai_provider

        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            symbol,
            file_hash,
            normalized_hash,
            source_url,
            file_name,
            exchange_time,
            processing_status,
            ai_processed,
            ai_provider
        )
    )

    conn.commit()
    conn.close()