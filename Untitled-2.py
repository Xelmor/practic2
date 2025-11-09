import argparse
import os
import sys
import re
import urllib.request
import json
 
def validate_args(args):
    errors = []

    if not args.package_name or not re.match(r'^[A-Za-z0-9_\-]+$', args.package_name):
        errors.append("Некорректное имя пакета (допустимы только буквы, цифры, -, _)")

    if args.mode not in ["local", "remote"]:
        errors.append("Режим должен быть: local или remote")

    if args.version and not re.match(r'^\d+\.\d+(\.\d+)?$', args.version):
        errors.append("Некорректная версия (пример: 1.0 или 1.0.3)")

    if errors:
        for e in errors:
            print(e)
        sys.exit(1)

def get_dependencies_from_pypi(package, version):
    url = f"https://pypi.org/pypi/{package}/{version}/json"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
    except:
        print("Ошибка: Не удалось получить данные по указанной версии пакета.")
        return []

    requires = data["info"].get("requires_dist", [])
    return requires if requires else []

def main():
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей (Этап 1 + Этап 2)"
    )

    parser.add_argument("--package-name", default="pandas")
    parser.add_argument("--repo-url", default="https://pypi.org/project/")
    parser.add_argument("--mode", default="remote")   # Этап 2 работает в режиме remote
    parser.add_argument("--version", default="2.3.2")  # Любая версия, существующая на PyPI
    parser.add_argument("--filter", default="ru")

    args = parser.parse_args()
    validate_args(args)

    print("\nПараметры конфигурации:")
    print(f"  package-name: {args.package_name}")
    print(f"  mode:         {args.mode}")
    print(f"  version:      {args.version}")
    print(f"  filter:       {args.filter}")

    if args.mode == "remote":
        print("\nИзвлекаю прямые зависимости из PyPI...")
        deps = get_dependencies_from_pypi(args.package_name, args.version)

        if deps:
            print("\nПрямые зависимости:")
            for d in deps:
                print(" -", d)
        else:
            print("Зависимости не найдены.")

if __name__ == "__main__":
    main()