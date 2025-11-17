import argparse
import os
import sys
import re
import urllib.request
import json
from collections import defaultdict, deque
 
def validate_args(args):
    errors = []

    if not args.package_name or not re.match(r'^[A-Za-z0-9_\-]+$', args.package_name):
        errors.append("Некорректное имя пакета (допустимы только буквы, цифры, -, _)")

    if args.mode not in ["local", "remote", "test"]:
        errors.append("Режим должен быть: local, remote или test")

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

def parse_dependency(dep_string):
    """Извлекает имя пакета из строки зависимости"""
    # Убираем версии и дополнительные условия
    match = re.match(r'^([A-Za-z0-9_\-]+)', dep_string)
    return match.group(1) if match else dep_string

def create_test_repository():
    """Создает тестовый репозиторий прямо в коде"""
    return {
        "A": ["B", "C"],      # A зависит от B и C
        "B": ["D", "E"],      # B зависит от D и E  
        "C": ["E", "F"],      # C зависит от E и F
        "D": ["G"],           # D зависит от G
        "E": ["G", "H"],      # E зависит от G и H
        "F": ["H"],           # F зависит от H
        "G": [],              # G не зависит ни от чего
        "H": [],              # H не зависит ни от чего
        
        # Циклические зависимости для тестов
        "X": ["Y"],           # X -> Y -> X (цикл)
        "Y": ["X"],           # 
        
        "P": ["Q", "R"],      # Более сложный цикл
        "Q": ["R"],           #
        "R": ["P"]            # P -> Q -> R -> P
    }

class DependencyGraph:
    def __init__(self, filter_string=""):
        self.graph = defaultdict(list)
        self.visited = set()
        self.filter_string = filter_string
        self.cycle_detected = False
        
    def should_skip_package(self, package_name):
        """Проверяет, нужно ли пропустить пакет по фильтру"""
        return self.filter_string and self.filter_string.lower() in package_name.lower()
    
    def dfs_build_graph(self, package, version, get_dependencies_func, depth=0, path=None):
        """Рекурсивный DFS для построения графа зависимостей"""
        if path is None:
            path = set()
            
        # Проверка циклических зависимостей
        if package in path:
            print(f"Обнаружена циклическая зависимость: {' => '.join(path)} => {package}")
            self.cycle_detected = True
            return
            
        # Пропускаем пакеты по фильтру
        if self.should_skip_package(package):
            print(f"Пропущен пакет (фильтр): {package}")
            return
            
        if package in self.visited:
            return
            
        self.visited.add(package)
        current_path = path | {package}
        
        print(f"{'  ' * depth} {package} {version if version else ''}")
        
        # Получаем зависимости
        dependencies = get_dependencies_func(package, version)
        
        for dep in dependencies:
            dep_name = parse_dependency(dep) if isinstance(dep, str) else dep
            
            # Добавляем в граф
            if dep_name not in self.graph[package]:
                self.graph[package].append(dep_name)
                
            # Рекурсивно обрабатываем зависимости
            self.dfs_build_graph(dep_name, version, get_dependencies_func, depth + 1, current_path)
    
    def display_graph(self):
        """Отображает граф зависимостей"""
        print("==ГРАФ ЗАВИСИМОСТЕЙ==")
        
        for package, dependencies in self.graph.items():
            if dependencies:
                print(f"{package} => {', '.join(dependencies)}")
            else:
                print(f"{package} => (нет зависимостей)")
                
        if self.cycle_detected:
            print("\nВ графе обнаружены циклические зависимости!")
            
        print(f"\nВсего пакетов: {len(self.graph)}")

def main():
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей"
    )

    parser.add_argument("--package-name", default="pandas")
    parser.add_argument("--repo-url", default="https://pypi.org/project/")
    parser.add_argument("--mode", default="remote")
    parser.add_argument("--version", default="1.2.1")
    parser.add_argument("--filter", default="")

    args = parser.parse_args()
    validate_args(args)

    print("\nПараметры конфигурации:")
    print(f"  package-name: {args.package_name}")
    print(f"  mode:         {args.mode}")
    print(f"  version:      {args.version}")
    print(f"  filter:       {args.filter}")

    # Инициализация графа
    graph = DependencyGraph(filter_string=args.filter)

    if args.mode == "remote":
        print("\nИзвлекаю граф зависимостей из PyPI (DFS)...")
        graph.dfs_build_graph(args.package_name, args.version, get_dependencies_from_pypi)
        
    elif args.mode == "test":
        print("\nТЕСТОВЫЙ РЕЖИМ: используем встроенные тестовые данные")
        test_repo = create_test_repository()
        
        def get_test_deps(package, version):
            return test_repo.get(package, [])
            
        print(f"Строю граф для пакета {args.package_name}...")
        graph.dfs_build_graph(args.package_name, args.version, get_test_deps)
    
    # Отображаем итоговый граф
    graph.display_graph()

if __name__ == "__main__":
    main()