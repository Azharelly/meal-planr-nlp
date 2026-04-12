import json
import os
import re
from extract_text import extract_text_from_pdf



def clean_text(text: str) -> str:
    # "11/2" → "1 1/2"
    text = re.sub(r'(\d)(\d/\d)', r'\1 \2', text)
    # "1taza" → "1 taza"
    text = re.sub(r'(\d)([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])', r'\1 \2', text)
    # "123g" → "123 g"
    text = re.sub(r'(\d)(g|ml|kg|mg|oz|lb)(\b|~)', r'\1 \2', text)
    # "~ 123" → "| 123"
    text = re.sub(r'~\s*(\d)', r'| \1', text)
    # limpiar símbolos OCR
    text = re.sub(r'[*•·»«]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def prepare_for_label_studio(pdf_paths: list) -> list:
    tasks = []
    
    for pdf_path in pdf_paths:
        result = extract_text_from_pdf(pdf_path)
        
        for page in result["pages"]:
            # Dividir por salto de línea simple
            lines = page["text"].split("\n")
            
            current_block = []
            for line in lines:
                line = line.strip()
                if line:
                    current_block.append(line)
                else:
                    if current_block:
                        block_text = clean_text(" ".join(current_block))
                        if len(block_text) > 20:
                            tasks.append({
                                "data": {
                                    "text": block_text,
                                    "source_file": result["file"],
                                    "page": page["page"]
                                }
                            })
                        current_block = []
            
            # último bloque
            if current_block:
                block_text = clean_text(" ".join(current_block))
                if len(block_text) > 20:
                    tasks.append({
                        "data": {
                            "text": block_text,
                            "source_file": result["file"],
                            "page": page["page"]
                        }
                    })
    
    return tasks

if __name__ == "__main__":
    pdf_paths = [
       # r"data\raw\distribución 04-04-26.pdf",
        r"data\raw\101_Square_Meals.pdf"
    ]
    
    tasks = prepare_for_label_studio(pdf_paths)
    
    print(f"Total tareas: {len(tasks)}")
    print("\nPrimeras 5 tareas:")
    for task in tasks[:5]:
        print(f"\n---")
        print(task["data"]["text"])
    
    output_path = r"data\annotated\tasks_v2.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    print(f"\nGuardado en: {output_path}")