import argparse
import os
import sys
import re

#корректность переданных данных
def validate_args(args):
    errors = []

    # Проверка имени пакета
    if not args.package_name or not re.match(r'^[A-Za-z0-9_\-]+$', args.package_name):
        errors.append("Некорректное имя пакета (допустимы только буквы, цифры, -, _)")

    # Проверка URL или пути
    if args.repo_url.startswith(("http://", "https://")):
        pass
    elif not os.path.exists(args.repo_url):
        errors.append("Указанный путь к репозиторию не существует")

    # Проверка режима
    if args.mode not in ["local", "remote"]:
        errors.append("Неверный режим работы (используйте 'local' или 'remote')")

    # Проверка версии
    if args.version and not re.match(r'^\d+\.\d+(\.\d+)?$', args.version):
        errors.append("Некорректная версия (пример: 1.0 или 1.0.3)")

    # Проверка фильтра
    if args.filter and len(args.filter) < 2:
        errors.append("Фильтр должен содержать минимум 2 символа")

    if errors:
        for e in errors:
            print(e)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей" #этап 1 - прототиап
    )

    parser.add_argument("--package-name", required=False, default="numpy", help="Имя анализируемого пакета")
    parser.add_argument("--repo-url", required=False, default=r"c:/Users/maxim/Desktop/Уроки ВУЗ/Конфиг управление суббота/Практика 2/test_repo", help="URL или путь к репозиторию")
    parser.add_argument("--mode", required=False, default="remote", help="Режим работы: local / remote")
    parser.add_argument("--version", required=False, default="9.1.0", help="Версия пакета (например, 1.0.0)")
    parser.add_argument("--filter", required=False, default="ru", help="Подстрока для фильтрации пакетов")

    args = parser.parse_args()

    # Проверка и вывод
    validate_args(args)

    print("\nПараметры конфигурации:")
    print(f"  package-name: {args.package_name}")
    print(f"  repo-url:     {args.repo_url}")
    print(f"  mode:         {args.mode}")
    print(f"  version:      {args.version or '—'}")
    print(f"  filter:       {args.filter or '—'}")

if __name__ == "__main__":
    main()
