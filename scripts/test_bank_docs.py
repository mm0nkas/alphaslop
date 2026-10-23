from pathlib import Path
import sys

# Добавляем корень проекта в путь импортов
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.ingest.bank_kb import BankKB, build_index, chunk_text

# Путь к вашим PDF
pdf_dir = Path("data//bank_analytics")
pdf_dir.mkdir(exist_ok=True)  # создаст папку, если её нет

pdf_files = list(pdf_dir.glob("*.pdf"))
print(f"📁 Найдено PDF в {pdf_dir}: {len(pdf_files)}")

if pdf_files:
    kb = BankKB()
    # Пробуем прочитать первый файл
    first_pdf = pdf_files[0]
    print(f"\n📄 Читаем: {first_pdf.name}")
    
    try:
        chunks = kb.load_pdf(first_pdf)
        print(f"✅ Получено чанков: {len(chunks)}")
        if chunks:
            print(f"\n📝 Пример первого чанка (200 символов):")
            print(chunks[0][:200])
            print("...")
    except Exception as e:
        print(f"❌ Ошибка чтения PDF: {e}")
else:
    print("⚠️  PDF не найдены! Скачайте 9 документов со слайда 17")
    print("   и положите в папку: data/bank_analytics/")