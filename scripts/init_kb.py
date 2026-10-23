from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pymupdf
from PIL import Image
import io
import pytesseract
from rank_bm25 import BM25Plus

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from backend.ingest.bank_kb import BankKB


def extract_text_with_ocr(pdf_path: Path) -> str:
    doc = pymupdf.open(pdf_path)
    all_text = ""
    for page_num, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        ocr_text = pytesseract.image_to_string(image, lang="rus+eng")
        all_text += f"\n--- Страница {page_num + 1} ---\n{ocr_text}"
    doc.close()
    return all_text


def chunk_text_simple(text: str, chunk_size: int = 400, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def main():
    pdf_dir = Path("data/bank_analytics")
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    
    print(f"📁 Найдено PDF: {len(pdf_files)}")
    if not pdf_files:
        print("❌ PDF не найдены!")
        return
    
    try:
        pytesseract.get_tesseract_version()
        print("✅ Tesseract найден\n")
    except Exception as e:
        print(f"❌ Tesseract не найден: {e}")
        return
    
    all_chunks = []
    
    for pdf_file in pdf_files:
        print(f"📄 {pdf_file.name}")
        try:
            text = extract_text_with_ocr(pdf_file)
            chunks = chunk_text_simple(text, chunk_size=400, overlap=50)
            
            # СОЗДАЁМ СЛОВАРИ вместо простых строк
            for i, chunk_text in enumerate(chunks):
                all_chunks.append({
                    "text": chunk_text,
                    "doc_name": pdf_file.name,
                    "chunk_id": f"{pdf_file.stem}_{i}"
                })
            print(f"   Чанков: {len(chunks)}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print(f"\n✅ Всего чанков: {len(all_chunks)}")
    if not all_chunks:
        return
    
    print("\n🔨 Построение BM25 индекса...")
    
    def tokenize(text: str) -> list:
        return [w.lower() for w in text.split() if len(w) > 2]

    tokenized_chunks = [tokenize(chunk["text"]) for chunk in all_chunks]
    
    index_data = {
        "chunks": all_chunks,
        "tokenized": tokenized_chunks,
        "bm25_params": {"k1": 1.5, "b": 0.75}
    }

    index_path = Path("data/kb_index.json")
    index_path.parent.mkdir(exist_ok=True)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Индекс сохранён в {index_path}")
    
    print("\n🔍 Тестовый поиск...")
    kb = BankKB()
    results = kb.search("ключевая ставка инфляция", top_k=2)
    for i, res in enumerate(results, 1):
        print(f"  {i}. [{res.get('doc')}] {res.get('text', '')[:100]}... (score: {res.get('score'):.2f})")


if __name__ == "__main__":
    main()