from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import spacy
import tempfile
import os
from extract_text import extract_text_from_pdf

app = FastAPI(title="MealPlanr NLP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar modelo entrenado
nlp = spacy.load("models/model-best")

def parse_entities(text: str) -> dict:

    doc = nlp(text)
    
    result = {
        "name": "",
        "ingredients": [],
        "steps": [],
        "prepTime": None,
        "cookTime": None,
        "servings": None,
        "imageUrl": None
    }
    
    current_ingredient = {"name": "", "quantity": "", "unit": ""}
    
    for ent in doc.ents:
        if ent.label_ == "RECIPE_NAME":
            result["name"] = ent.text
        elif ent.label_ == "INGREDIENT":
            current_ingredient["name"] = ent.text
        elif ent.label_ == "QUANTITY":
            current_ingredient["quantity"] = ent.text
        elif ent.label_ == "UNIT":
            current_ingredient["unit"] = ent.text
        elif ent.label_ == "STEP":
            result["steps"].append(ent.text)
        elif ent.label_ == "TIME":
            result["prepTime"] = ent.text
        elif ent.label_ == "SERVINGS":
            result["servings"] = ent.text
        
    
        if current_ingredient["name"]:
            result["ingredients"].append({
                "name": current_ingredient["name"],
                "quantity": current_ingredient["quantity"],
                "unit": current_ingredient["unit"]
            })
            current_ingredient = {"name": "", "quantity": "", "unit": ""}
    
    return result

@app.post("/extract")
async def extract_recipe(file: UploadFile = File(...)):
    
    
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not supported")
    

    suffix = ".pdf" if "pdf" in file.content_type else ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        
        if suffix == ".pdf":
            result = extract_text_from_pdf(tmp_path)
            full_text = " ".join([p["text"] for p in result["pages"]])
        else:
            import pytesseract
            from PIL import Image
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            full_text = pytesseract.image_to_string(Image.open(tmp_path), lang="spa+eng")
        
        
        recipe = parse_entities(full_text)
        return recipe
        
    finally:
        os.unlink(tmp_path)

@app.get("/health")
async def health():
    return {"status": "ok", "model": "meal-planr-nlp-v1"}