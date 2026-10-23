from pathlib import Path
import fitz

pdf_dir = Path("data/bank_analytics")
for pdf_file in sorted(pdf_dir.glob("*.pdf")):
    doc = fitz.open(pdf_file)
    first_page_text = doc[0].get_text().strip()
    has_images = len(doc[0].get_images()) > 0
    print(f"{pdf_file.name}:")
    print(f"  Текст на стр.1: {'✅ Есть' if first_page_text else ' Нет'} ({len(first_page_text)} симв.)")
    print(f"  Изображения: {'✅ Есть' if has_images else '❌ Нет'}")
    doc.close()