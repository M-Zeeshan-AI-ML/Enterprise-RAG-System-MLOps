import json
from pathlib import Path
from app.rag.pipeline import RAGPipeline

def evaluate():
    dataset = json.loads(Path("evaluation/dataset.json").read_text(encoding="utf-8"))
    rag = RAGPipeline()
    hits = 0
    for item in dataset:
        docs = rag.retrieve(item["question"], k=5)
        pages = [int(d.metadata.get("page", 0)) + 1 for d in docs]
        expected = set(item["expected_pages"])
        if expected.intersection(pages):
            hits += 1
        print(f"Q: {item['question']}\nExpected pages: {sorted(expected)}\nRetrieved pages: {pages}\n")
    print(f"Recall@5: {hits / len(dataset) if dataset else 0.0:.3f}")

if __name__ == "__main__":
    evaluate()
