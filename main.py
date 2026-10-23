# main.py
import argparse
import sys
from pathlib import Path

# Добавляем корень проекта в пути
sys.path.insert(0, str(Path(__file__).resolve().parent))

def run_command(module_name):
    """Запускает функцию main() из указанного модуля"""
    try:
        # Динамически импортируем модуль из папки scripts
        module = __import__(f"scripts.{module_name}", fromlist=["main"])
        module.main()
    except Exception as e:
        print(f"❌ Ошибка при выполнении {module_name}: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Alfa News Analytics CLI")
    parser.add_argument(
        "command", 
        choices=["init", "collect", "tag", "link", "demo", "all"],
        help="Команда для выполнения"
    )
    args = parser.parse_args()

    print(f"🚀 Запуск команды: {args.command}\n" + "="*50)

    if args.command == "all":
        run_command("init_kb")
        run_command("collect_news")
        run_command("tag_news")
        run_command("link_to_bank")
        run_command("demo")
    else:
        # Маппинг коротких команд на имена файлов
        command_map = {
            "init": "init_kb",
            "collect": "collect_news",
            "tag": "tag_news",
            "link": "link_to_bank",
            "demo": "demo"
        }
        run_command(command_map[args.command])

if __name__ == "__main__":
    main()