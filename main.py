import argparse
import os
import sys

def error(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Минимальное CLI-приложение для конфигурации.")

    parser.add_argument("--package", required=True,
                        help="Имя анализируемого пакета.")

    parser.add_argument("--repo", required=True,
                        help="URL-адрес репозитория или путь к файлу тестового репозитория.")

    parser.add_argument("--mode", required=True, choices=["local", "remote"],
                        help="Режим работы с тестовым репозиторием: local или remote.")

    parser.add_argument("--version", required=True,
                        help="Версия пакета.")

    parser.add_argument("--filter", required=True,
                        help="Подстрока для фильтрации пакетов.")

    args = parser.parse_args()

    # ---- ОБРАБОТКА ОШИБОК ----

    # package: должно быть непустым словом
    if not args.package.strip():
        error("Имя пакета не может быть пустым.")

    # repo: проверяем валидность
    if args.mode == "local":
        if not os.path.exists(args.repo):
            error("Локальный путь к репозиторию не существует.")
    else:  # remote
        if not (args.repo.startswith("http://") or args.repo.startswith("https://")):
            error("Для режима remote репозиторий должен быть корректным URL.")

    # version: минимальная проверка формата X.Y или X.Y.Z
    parts = args.version.split(".")
    if not all(part.isdigit() for part in parts):
        error("Версия пакета должна состоять из чисел, разделённых точками.")

    # filter: непустая строка
    if not args.filter.strip():
        error("Подстрока фильтрации не может быть пустой.")

    # ---- ВЫВОД ВСЕХ ПАРАМЕТРОВ ----
    print("package =", args.package)
    print("repo =", args.repo)
    print("mode =", args.mode)
    print("version =", args.version)
    print("filter =", args.filter)

if __name__ == "__main__":
    main()
