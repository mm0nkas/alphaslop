import json
from pathlib import Path
from rank_bm25 import BM25Plus
from dataclasses import dataclass

@dataclass
class KBChunk:
    text: str
    doc_name: str
    chunk_id: str

class BankKB:
    def __init__(self, index_path: str = "data/kb_index.json"):
        self.index_path = Path(index_path)
        self.chunks = []
        self.bm25 = None
        
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Теперь d - это словарь, и **d сработает корректно!
            self.chunks = [KBChunk(**d) for d in data["chunks"]]
            
            # Пересобираем BM25 индекс в памяти при загрузке
            tokenized = [self._tokenize(c.text) for c in self.chunks]
            self.bm25 = BM25Plus(tokenized)
        else:
            print(f"⚠️ Индекс не найден по пути {self.index_path}")

    def _tokenize(self, text: str) -> list:
        return [w.lower() for w in text.split() if len(w) > 2]

    def search(self, query: str, top_k: int = 3) -> list:
        if not self.bm25 or not self.chunks:
            return []
        
        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)
        
        # Сортируем индексы по убыванию scores
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Возвращаем только релевантные результаты
                results.append({
                    "text": self.chunks[idx].text,
                    "doc": self.chunks[idx].doc_name,
                    "score": float(scores[idx])
                })
        return results