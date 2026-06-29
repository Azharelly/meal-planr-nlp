# MealPlanr NLP

A custom NLP microservice for recipe extraction, built with spaCy and FastAPI. Designed as the AI backbone of the MealPlanr app, it parses recipes from PDFs, images, and URLs into structured data using a trained Named Entity Recognition (NER) model.

## What it does

Given a recipe from a PDF scan, a photo, or a webpage URL the service extracts and returns structured data:

```json
{
  "name": "Spaghetti Carbonara",
  "ingredients": ["200g pasta", "100g pancetta", "2 eggs"],
  "steps": ["Boil the pasta...", "Fry the pancetta..."],
  "prepTime": "10 minutes",
  "cookTime": "20 minutes",
  "servings": "2"
}
```

## Architecture

The pipeline goes from raw text to structured recipe data in three stages:

```
Input (PDF / Image / URL)
        ↓
  Text Extraction
  (pdfplumber / Tesseract OCR — bilingual EN+ES)
        ↓
  Custom spaCy NER Model
  (trained on scraped recipe data)
        ↓
  Structured Recipe JSON (via FastAPI)
```


## Custom NER Model

The model was trained from scratch using spaCy on a custom dataset of recipe texts. It recognises the following entity types:

| Entity | Example |
|---|---|
| `RECIPE_NAME` | "Spaghetti Carbonara" |
| `INGREDIENT` | "pancetta" |
| `QUANTITY` | "200" |
| `UNIT` | "grams" |
| `STEP` | "Bring water to a boil" |
| `TIME` | "20 minutes" |
| `SERVINGS` | "serves 4" |

Training data was scraped from recipe sites using `scrape_recipes.py`, processed with `prepare_data.py`, and converted to spaCy format with `convert_to_spacy.py`.


## API Endpoints

### `POST /extract`
Upload a PDF or image file. Supports bilingual OCR (English + Spanish).

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@recipe.pdf"
```

### `POST /extract-url`
Extract a recipe from a URL. Tries Schema.org structured data first, falls back to spaCy NER.

```bash
curl -X POST "http://localhost:8000/extract-url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/recipe"}'
```

### `GET /health`
```json
{ "status": "ok", "model": "meal-planr-nlp-v1" }
```

## Running locally

### With Docker (recommended)

```bash
docker build -t meal-planr-nlp .
docker run -p 8000:8000 meal-planr-nlp
```

### Without Docker

```bash
pip install -r requirements.txt
python main.py
```

## Project structure

```
meal-planr-nlp/
├── data/                  # Training data
├── models/                # Trained spaCy model (model-best)
├── scrape_recipes.py      # Recipe scraper (Schema.org + BeautifulSoup)
├── prepare_data.py        # Data preprocessing
├── convert_to_spacy.py    # Convert to spaCy training format
├── extract_text.py        # PDF text extraction
├── main.py                # FastAPI app + NER inference
├── test_model.py          # Model evaluation
├── Dockerfile
└── requirements.txt
```

## Tech stack

- **spaCy** — NER model training and inference
- **FastAPI** — REST API
- **Tesseract OCR** — image/scan text extraction (EN + ES)
- **pdfplumber** — PDF text extraction
- **BeautifulSoup** — web scraping fallback
- **Docker** — containerisation

---

## Context

This service was developed as part of the final year project for a BSc in Computing at Dublin Business School (2025–2026). It serves as the AI/NLP microservice for MealPlanr, a full-stack meal planning application.
