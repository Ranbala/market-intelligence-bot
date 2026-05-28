import fitz
import requests
import tempfile
from loguru import logger
import io
from PyPDF2 import PdfReader


MAX_PDF_TEXT_CHARS = 15000
MIN_USEFUL_PDF_TEXT_CHARS = 5000
MIN_TEXT_PAGE_RATIO = 0.5
OCR_RENDER_ZOOM = 2
OCR_MAX_PAGES = 40


def _build_page_result(page_no, text, layout_text=""):

    clean_text = text or ""
    clean_layout_text = layout_text or ""

    return {
        "page_no": page_no,
        "text": clean_text,
        "layout_text": clean_layout_text,
        "char_count": len(clean_text)
    }


def extract_layout_text_from_fitz_page(page):

    try:

        words = page.get_text("words") or []

    except Exception:
        return ""

    rows = []

    for word in words:

        x0, y0, x1, y1, text, *_ = word

        clean_text = str(text or "").strip()

        if not clean_text:
            continue

        y_bucket = round(y0 / 3) * 3

        matched_row = None

        for row in rows:
            if abs(row["y"] - y_bucket) <= 2:
                matched_row = row
                break

        if matched_row is None:
            matched_row = {
                "y": y_bucket,
                "words": []
            }
            rows.append(matched_row)

        matched_row["words"].append(word)

    rows.sort(
        key=lambda row: row["y"]
    )

    lines = []

    for row in rows:

        sorted_words = sorted(
            row["words"],
            key=lambda word: word[0]
        )

        line = " ".join(
            str(word[4]).strip()
            for word in sorted_words
            if str(word[4]).strip()
        )

        if line:
            lines.append(line)

    return "\n".join(lines)


def is_text_extraction_poor(pages):

    if not pages:
        return True

    total_pages = len(pages)
    total_chars = sum(
        page.get("char_count", 0)
        for page in pages
    )
    text_pages = sum(
        1
        for page in pages
        if page.get("char_count", 0) >= 100
    )

    if total_pages < 5:
        return False

    text_page_ratio = text_pages / total_pages

    return (
        total_chars < MIN_USEFUL_PDF_TEXT_CHARS
        or text_page_ratio < MIN_TEXT_PAGE_RATIO
    )


def is_ocr_available():

    try:
        import pytesseract

        pytesseract.get_tesseract_version()

        return True

    except Exception:
        return False


def extract_pdf_pages_with_ocr_from_bytes(
    pdf_bytes,
    existing_pages=None,
    max_pages=OCR_MAX_PAGES
):

    if not pdf_bytes:
        return existing_pages or []

    try:
        import pytesseract
        from PIL import Image

    except Exception as e:
        logger.warning(
            "OCR fallback skipped. Install pytesseract "
            f"and tesseract binary. Error: {str(e)}"
        )
        return existing_pages or []

    try:
        pytesseract.get_tesseract_version()

    except Exception as e:
        logger.warning(
            "OCR fallback skipped. Tesseract binary not available. "
            f"Error: {str(e)}"
        )
        return existing_pages or []

    try:
        existing_by_page = {
            page.get("page_no"): page
            for page in existing_pages or []
        }

        pdf_stream = io.BytesIO(pdf_bytes)

        doc = fitz.open(
            stream=pdf_stream,
            filetype="pdf"
        )

        total_doc_pages = len(doc)

        pages = []

        pages_to_process = min(
            total_doc_pages,
            max_pages
        )

        for index in range(pages_to_process):

            page_no = index + 1
            existing_page = existing_by_page.get(
                page_no,
                {}
            )
            existing_text = existing_page.get(
                "text",
                ""
            )

            # Keep already-useful text pages. OCR only blank/scanned pages.
            if len(existing_text.strip()) >= 100:
                pages.append(
                    _build_page_result(
                        page_no,
                        existing_text,
                        existing_page.get("layout_text", "")
                    )
                )
                continue

            page = doc[index]
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(
                    OCR_RENDER_ZOOM,
                    OCR_RENDER_ZOOM
                ),
                alpha=False
            )

            image = Image.frombytes(
                "RGB",
                [
                    pixmap.width,
                    pixmap.height
                ],
                pixmap.samples
            )

            ocr_text = pytesseract.image_to_string(
                image,
                config="--psm 6"
            )

            pages.append(
                _build_page_result(
                    page_no,
                    ocr_text
                )
            )

        if total_doc_pages > pages_to_process:
            for index in range(
                pages_to_process + 1,
                total_doc_pages + 1
            ):
                existing_page = existing_by_page.get(
                    index,
                    {}
                )
                pages.append(
                    _build_page_result(
                        index,
                        existing_page.get("text", ""),
                        existing_page.get("layout_text", "")
                    )
                )

        doc.close()

        logger.success(
            f"PDF OCR fallback completed: {len(pages)} pages"
        )

        return pages

    except Exception as e:

        logger.error(
            f"PDF OCR fallback failed: {str(e)}"
        )

        return existing_pages or []


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

        pages = extract_pdf_pages_from_path(
            pdf_path
        )

        full_text = "\n".join(
            page["text"]
            for page in pages
            if page.get("text")
        )

        logger.success(
            "PDF text extracted successfully"
        )

        return full_text[:MAX_PDF_TEXT_CHARS]

    except Exception as e:

        logger.error(
            f"PDF extraction failed: {str(e)}"
        )

        return ""


def extract_pdf_pages_from_path(pdf_path):

    try:

        doc = fitz.open(pdf_path)

        pages = []

        for index, page in enumerate(doc, start=1):

            text = page.get_text("text") or ""
            layout_text = extract_layout_text_from_fitz_page(
                page
            )

            pages.append(
                _build_page_result(
                    index,
                    text,
                    layout_text
                )
            )

        doc.close()

        logger.success(
            f"PDF pages extracted successfully: {len(pages)} pages"
        )

        return pages

    except Exception as e:

        logger.error(
            f"PDF page extraction from path failed: {str(e)}"
        )

        return []


def extract_pdf_pages_from_bytes(pdf_bytes):

    if not pdf_bytes:
        return []

    # PyMuPDF gives better page locality and usually cleaner layout text.
    try:

        pdf_stream = io.BytesIO(pdf_bytes)

        doc = fitz.open(
            stream=pdf_stream,
            filetype="pdf"
        )

        pages = []

        for index, page in enumerate(doc, start=1):

            text = page.get_text("text") or ""
            layout_text = extract_layout_text_from_fitz_page(
                page
            )

            pages.append(
                _build_page_result(
                    index,
                    text,
                    layout_text
                )
            )

        doc.close()

        logger.success(
            f"PDF pages extracted successfully from bytes: {len(pages)} pages"
        )

        return pages

    except Exception as e:

        logger.warning(
            f"PyMuPDF page extraction failed, trying PyPDF2: {str(e)}"
        )

    try:

        pages = []

        pdf_stream = io.BytesIO(pdf_bytes)

        pdf_reader = PdfReader(pdf_stream)

        for index, page in enumerate(
            pdf_reader.pages,
            start=1
        ):

            extracted = page.extract_text() or ""

            pages.append(
                _build_page_result(
                    index,
                    extracted
                )
            )

        logger.success(
            f"PDF pages extracted successfully from bytes: {len(pages)} pages"
        )

        return pages

    except Exception as e:

        logger.error(
            f"PDF byte page extraction failed: {str(e)}"
        )

        return []


def extract_pdf_text_from_bytes(pdf_bytes):

    try:

        pages = extract_pdf_pages_from_bytes(
            pdf_bytes
        )

        text = "\n".join(
            page["text"]
            for page in pages
            if page.get("text")
        )

        logger.success(
            "PDF text extracted successfully from bytes"
        )

        return text

    except Exception as e:

        logger.error(
            f"PDF byte extraction failed: {str(e)}"
        )

        return ""
