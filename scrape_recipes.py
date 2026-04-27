import requests
import extruct
import json
import time
from bs4 import BeautifulSoup
from w3lib.html import get_base_url
import re

def clean_ingredient(text: str) -> str:
    # "100g" → "100 g"
    text = re.sub(r'(\d)(g|ml|kg|mg|oz|lb|tsp|tbsp|cup|cups)(\b)', r'\1 \2', text)
    # "½" → "1/2", "¼" → "1/4", "¾" → "3/4"
    text = text.replace("½", "1/2").replace("¼", "1/4").replace("¾", "3/4")
    return text.strip()

def extract_schema_recipe(url: str) -> dict | None:
    """Intenta extraer receta usando Schema.org"""
    try:
        headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
        response = requests.get(url, headers=headers, timeout=10)
        base_url = get_base_url(response.text, response.url)
        
        data = extruct.extract(response.text, base_url=base_url, syntaxes=["json-ld", "microdata"])
        
        # Buscar Schema.org/Recipe en json-ld
        for item in data.get("json-ld", []):
            if "Recipe" in str(item.get("@type", "")):
                return parse_schema_recipe(item)
        
        # Buscar en microdata
        for item in data.get("microdata", []):
            if "Recipe" in str(item.get("type", "")):
                return parse_schema_recipe(item.get("properties", {}))
                
        return None
        
    except Exception as e:
        print(f"Error con {url}: {e}")
        return None

def parse_schema_recipe(data: dict) -> dict:
    """Convierte Schema.org Recipe a nuestro formato"""
    
    ingredients = data.get("recipeIngredient", [])
    
    instructions = []
    raw_instructions = data.get("recipeInstructions", [])
    for step in raw_instructions:
        if isinstance(step, str):
            instructions.append(step)
        elif isinstance(step, dict):
            instructions.append(step.get("text", ""))
    
    return {
        "name": data.get("name", ""),
        "ingredients": ingredients,
        "steps": instructions,
        "prepTime": data.get("prepTime", ""),
        "cookTime": data.get("cookTime", ""),
        "servings": str(data.get("recipeYield", ""))
    }

def recipes_to_label_studio_tasks(recipes: list) -> list:
    """Convierte recetas a tareas para Label Studio"""
    tasks = []
    
    for recipe in recipes:
        # Tarea para el nombre
        if recipe["name"]:
            tasks.append({"data": {"text": recipe["name"], "type": "name"}})
        
        # Tarea por cada ingrediente
        for ingredient in recipe["ingredients"]:
            if ingredient.strip():
                tasks.append({"data": {"text":  clean_ingredient(ingredient), "type": "ingredient"}})
        
        # Tarea por cada paso
        for step in recipe["steps"]:
            if step.strip():
                tasks.append({"data": {"text": step.strip(), "type": "step"}})
    
    return tasks

if __name__ == "__main__":
    urls = [
    "https://www.bbcgoodfood.com/recipes/easy-pancakes",
    "https://www.bbcgoodfood.com/recipes/banana-bread",
    "https://www.bbcgoodfood.com/recipes/classic-spaghetti-bolognese",
    "https://www.bbcgoodfood.com/recipes/chicken-tikka-masala",
    "https://www.bbcgoodfood.com/recipes/easy-chocolate-chip-cookies",
    "https://www.bbcgoodfood.com/recipes/sticky-toffee-pudding",
    "https://www.bbcgoodfood.com/recipes/lasagne",
    "https://www.bbcgoodfood.com/recipes/shepherd-s-pie",
    "https://www.bbcgoodfood.com/recipes/fish-chips",
    "https://www.bbcgoodfood.com/recipes/beef-stew",
    "https://www.bbcgoodfood.com/recipes/caesar-salad",
    "https://www.bbcgoodfood.com/recipes/mushroom-risotto",
    "https://www.bbcgoodfood.com/recipes/chicken-soup",
    "https://www.bbcgoodfood.com/recipes/carrot-cake",
    "https://www.bbcgoodfood.com/recipes/greek-salad",
    "https://www.bbcgoodfood.com/recipes/chocolate-brownies",
    "https://www.bbcgoodfood.com/recipes/chicken-curry",
    "https://www.bbcgoodfood.com/recipes/apple-crumble",
    "https://www.bbcgoodfood.com/recipes/victoria-sponge",
    "https://www.bbcgoodfood.com/recipes/egg-fried-rice",
    "https://www.bbcgoodfood.com/recipes/chicken-caesar-salad",
    "https://www.bbcgoodfood.com/recipes/prawn-stir-fry",
    "https://www.bbcgoodfood.com/recipes/beef-burgers",
    "https://www.bbcgoodfood.com/recipes/lemon-drizzle-cake",
    "https://www.bbcgoodfood.com/recipes/tomato-soup",
    "https://www.bbcgoodfood.com/recipes/quiche-lorraine",
    "https://www.bbcgoodfood.com/recipes/garlic-bread",
    "https://www.bbcgoodfood.com/recipes/tuna-pasta-bake",
    "https://www.bbcgoodfood.com/recipes/vegetable-curry",
    "https://www.bbcgoodfood.com/recipes/french-onion-soup"
]   
    
    recipes = []
    for url in urls:
        print(f"Scraping: {url}")
        recipe = extract_schema_recipe(url)
        if recipe:
            print(f" {recipe['name']} — {len(recipe['ingredients'])} ingredientes")
            recipes.append(recipe)
        else:
            print(f"Couldn't find Schema.org")
        time.sleep(1)
    
    print(f"\nTotal recipies: {len(recipes)}")
    
    tasks = recipes_to_label_studio_tasks(recipes)
    print(f"Total tareas: {len(tasks)}")
    
    with open(r"data\annotated\tasks_en.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    print("Saved in data/annotated/tasks_en.json")