import sqlite3

DB_PATH = "../data/news.db"


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