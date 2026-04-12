import spacy

nlp = spacy.load(r"models\model-last")

test_texts = [
    "2 cups plain flour",
    "1 tbsp sunflower oil",
    "Beat the eggs in a bowl for 2 minutes",
    "Easy pancakes",
    "Serves 4 people",
    "Preparation time 10 minutes",
]

for text in test_texts:
    doc = nlp(text)
    print(f"\nText: {text}")
    for ent in doc.ents:
        print(f"  {ent.label_:12} → '{ent.text}'")
        