import fitz
import requests
import tempfile

from loguru import logger


def extract_pdf_text(pdf_url):

    try:

        # ==========================================
        # ONLY PROCESS PDF FILES
        # ==========================================

        if not pdf_url.lower().endswith(".pdf"):
            return ""

        logger.info(f"Downloading PDF: {pdf_url}")

        response = requests.get(
            pdf_url,
            timeout=(10, 60),
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if response.status_code != 200:
            return ""

        # ==========================================
        # SAVE TEMP PDF
        # ==========================================

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as tmp_file:

            tmp_file.write(response.content)

            pdf_path = tmp_file.name

        # ==========================================
        # OPEN PDF
        # ==========================================

        doc = fitz.open(pdf_path)

        full_text = ""

        for page in doc:
            full_text += page.get_text()

        doc.close()

        logger.success(
            "PDF text extracted successfully"
        )

        return full_text[:10000]

    except Exception as e:

        logger.error(
            f"PDF extraction failed: {str(e)}"
        )

        return ""