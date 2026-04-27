import json
import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

def convert_label_studio_to_spacy(export_path: str) -> list:
   
    with open(export_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    training_data = []
    
    for task in data:
        text = task["data"]["text"]
        annotations = task.get("annotations", [])
        
        if not annotations:
            continue
            
        entities = []
        for annotation in annotations:
            for result in annotation.get("result", []):
                if result.get("type") == "labels":
                    value = result["value"]
                    start = value["start"]
                    end = value["end"]
                    label = value["labels"][0]
                    entities.append((start, end, label))
        
        if entities:
            training_data.append((text, {"entities": entities}))
    
    return training_data

def create_docbin(training_data: list, nlp) -> DocBin:
   
    db = DocBin()
    skipped = 0
    
    for text, annotations in training_data:
        doc = nlp.make_doc(text)
        ents = []
        
        for start, end, label in annotations["entities"]:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is not None:
                ents.append(span)
            else:
                skipped += 1
        
        doc.ents = filter_spans(ents)
        db.add(doc)
    
    print(f"Spans ignorados (desalineados): {skipped}")
    return db

if __name__ == "__main__":
    nlp = spacy.blank("en")

    print("Loading English data...")
    data_en = convert_label_studio_to_spacy(r"data\annotated\export_en.json")
    print(f"English tasks: {len(data_en)}")
    
    print("Loading Spanish data...")
    data_es = convert_label_studio_to_spacy(r"data\annotated\export_es.json")
    print(f"Spanish tasks: {len(data_es)}")
    
    all_data = data_en + data_es
    print(f"Total combined: {len(all_data)}")
    
    # Split 80% train, 20% dev
    split = int(len(all_data) * 0.8)
    train_data = all_data[:split]
    dev_data = all_data[split:]
    
    print(f"Train: {len(train_data)} | Dev: {len(dev_data)}")
    

    train_db = create_docbin(train_data, nlp)
    dev_db = create_docbin(dev_data, nlp)
    
    # Guardar
    train_db.to_disk(r"data\annotated\train.spacy")
    dev_db.to_disk(r"data\annotated\dev.spacy")
    
    print("\nFiles created:")
    print("  data/annotated/train.spacy")
    print("  data/annotated/dev.spacy")