import pdfplumber
import json
import os

def extract_text_from_pdf(pdf_path: str) -> dict:
    """Extrae texto de un PDF página por página"""
    result = {
        "file": os.path.basename(pdf_path),
        "pages": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                result["pages"].append({
                    "page": i + 1,
                    "text": text
                })
    
    return result

if __name__ == "__main__":
    
    pdf_path = r"C:\Users\azhar\OneDrive\Desktop\Final Project\distribución_04-04-26.pdf"
    
    result = extract_text_from_pdf(pdf_path)
    
    for page in result["pages"]:
        print(f"\n{'='*50}")
        print(f"PÁGINA {page['page']}")
        print(f"{'='*50}")
        print(page["text"])