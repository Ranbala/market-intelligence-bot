from newspaper import Article
from loguru import logger


def fetch_full_article(url):

    try:

        article = Article(
            url,
            browser_user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
                )
            )
        article.download()
        article.parse()
        text = article.text

        if not text or len(text) < 100:

            logger.warning(
                f"Very short article extracted: {url}"
            )
            return None
        return text
    except Exception as e:
        logger.error(
            f"Article extraction failed: {e}"
        )
        return None