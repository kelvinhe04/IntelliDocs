import pdfplumber
import pytesseract
from PIL import Image
import io
import os

# Configure Tesseract path for Windows
# Common default installation path
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file.
    Tries to extract text natively using pdfplumber.
    If little text is found, falls back to OCR using pytesseract on page images.
    """
    text_content = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Tuning layout analysis - increased tolerance for buttons/banners
                page_text = page.extract_text(x_tolerance=3, y_tolerance=3)
                
                # Check if enough text was extracted, otherwise use OCR
                if not page_text or len(page_text.strip()) < 50:
                    try:
                        # Convert page to image for OCR
                        # pdfplumber allows converting page to image
                        im = page.to_image(resolution=300)
                        ocr_text = pytesseract.image_to_string(im.original)
                        page_text = ocr_text
                    except pytesseract.TesseractNotFoundError:
                        print("Warning: Tesseract not found. Using partial text from pdfplumber.")
                        # If we have some text, use it. If None, make empty string.
                        if page_text is None:
                            page_text = ""
                    except Exception as e:
                        print(f"Warning: OCR failed ({e}). Using partial text.")
                        if page_text is None:
                            page_text = ""
                
                text_content += page_text + "\n"
    except pytesseract.TesseractNotFoundError:
        print("Tesseract not found. Please install Tesseract OCR and add it to PATH.")
        return "Error: Tesseract OCR not found. Please install it."
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return f"Error reading PDF: {str(e)}"
        
    return text_content.strip()

if __name__ == "__main__":
    # Test with a dummy path if needed, or just run valid tests later
    pass
