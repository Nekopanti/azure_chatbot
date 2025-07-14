import base64
import fitz
from common.logger import get_logger

logger = get_logger("extractor")


def convert_pdf_to_images(doc):
    images_base64 = []
    for page_num in range(len(doc)):
        try:
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            pixbytes = pix.tobytes("png")
            b64_str = base64.b64encode(pixbytes).decode("utf-8")
            images_base64.append(f"data:image/png;base64,{b64_str}")
        except Exception as e:
            logger.error(f"Failed to convert image on page {page_num+1}: {e}")
            images_base64.append(None)
    return images_base64


def extract_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF: {e}")
        return [], []

    images = convert_pdf_to_images(doc)
    texts = []
    for page_num in range(len(doc)):
        try:
            page = doc.load_page(page_num)
            text = page.get_text()
            texts.append(text)
        except Exception as e:
            logger.error(f"Failed to extract text from page {page_num+1}: {e}")
            texts.append("")
    return images, texts
