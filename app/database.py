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