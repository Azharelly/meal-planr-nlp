from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import spacy
import tempfile
import os
import requests
import re
from extract_text import extract_text_from_pdf
from bs4 import BeautifulSoup
from scrape_recipes import extract_schema_recipe

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
            if current_ingredient["name"] and len(current_ingredient["name"]) > 2:
                ing_str = f"{current_ingredient['quantity']}{current_ingredient['unit']} {current_ingredient['name']}".strip()
                result["ingredients"].append(ing_str)
                current_ingredient = {"name": "", "quantity": "", "unit": ""}
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
    
    # Guardar el último ingrediente pendiente
    if current_ingredient["name"] and len(current_ingredient["name"]) > 2:
        ing_str = f"{current_ingredient['quantity']}{current_ingredient['unit']} {current_ingredient['name']}".strip()
        result["ingredients"].append(ing_str)
    
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
            full_text = pytesseract.image_to_string(Image.open(tmp_path), lang="spa+eng")
        
        recipe = parse_entities(full_text)
        print("NLP OUTPUT:", recipe)
        return recipe
        
    finally:
        os.unlink(tmp_path)


@app.get("/health")
async def health():
    return {"status": "ok", "model": "meal-planr-nlp-v1"}


@app.post("/extract-url")
async def extract_from_url(data: dict):
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Intentar Schema.org primero
    print(f"🔍 Intentando Schema.org para: {url}")
    recipe = extract_schema_recipe(url)
    
    if recipe:
        print("✅ Schema.org funcionó")
        return recipe
    
    print("⚠️ Schema.org falló, usando spaCy")
    
    # Fallback: scraping + spaCy
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Limpiar texto
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # quitar no-ASCII
        text = re.sub(r'\s+', ' ', text).strip()      # normalizar espacios
        text = text[:5000]                             # limitar tamaño
        
        recipe = parse_entities(text)
        return recipe
        
    except Exception as e:
        print(f"❌ Error en fallback: {e}")
        raise HTTPException(status_code=404, detail="Could not extract recipe")
