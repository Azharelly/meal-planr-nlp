import pdfplumber
import pytesseract
from PIL import Image
import io
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(pdf_path: str) -> dict:
    
    result = {
        "file": os.path.basename(pdf_path),
        "pages": [],
        "method": None
    }

    with pdfplumber.open(pdf_path) as pdf:
        
        texts = [page.extract_text() for page in pdf.pages]
        has_text = any(t and t.strip() for t in texts)

        if has_text:
            result["method"] = "direct"
            for i, text in enumerate(texts):
                if text:
                    result["pages"].append({
                        "page": i + 1,
                        "text": text.strip()
                    })
        else:
            
            result["method"] = "ocr"
            for i, page in enumerate(pdf.pages):
                img = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(img, lang="spa+eng")
                if text.strip():
                    result["pages"].append({
                        "page": i + 1,
                        "text": text.strip()
                    })

    return result

if __name__ == "__main__":
    pdf_path = r"data\raw\distribución 04-04-26.pdf"
    result = extract_text_from_pdf(pdf_path)

    print(f"Método usado: {result['method']}")
    print(f"Páginas extraídas: {len(result['pages'])}")

    for page in result["pages"]:
        print(f"\n{'='*50}")
        print(f"PÁGINA {page['page']}")
        print(f"{'='*50}")
        print(page["text"])