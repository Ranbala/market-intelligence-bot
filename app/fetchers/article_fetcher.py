from newspaper import Article
from loguru import logger


def fetch_full_article(url):

    try:

        article = Article(url)

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