from database import init_db
from main import run_rss_news_pipeline

if __name__ == "__main__":

    init_db()

    run_rss_news_pipeline()