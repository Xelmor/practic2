import csv
import json
import re
import sys
import urllib.request


class CLI_PIP:
    def __init__(self, input_type: str = 'csv_file'):
        self.input_type = input_type
        if self.input_type == 'csv_file':
            self.params = self.csv_file()
        else:
            raise ValueError("Сейчас поддерживается только режим 'csv_file'")

    def csv_file(self):
        params = {}
        try:
            with open('csv_config.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    parameter = row['parameter']
                    value = row['value']
                    params[parameter] = value

            if not params.get('package_name'):
                raise ValueError('package_name cannot be empty')

            if not params.get('repo_url'):
                raise ValueError('repo_url cannot be empty')

            return params

        except FileNotFoundError:
            print('ERROR: csv_config.csv file not found', file=sys.stderr)
            sys.exit(1)

    def load_package_info(self, name: str, version: str = '') -> dict:
        repo_url = self.params['repo_url'].rstrip('/')
        if not version or version == "latest":
            url = f"https://{repo_url}/{name}/json"
        else:
            url = f"https://{repo_url}/{name}/{version}/json"

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
            return data
        except Exception as e:
            print(f"Ошибка при получении {name}: {e}", file=sys.stderr)
            sys.exit(1)

    def parse_dependencies(self, dependencies):
        """
        dependencies: список строк из requires_dist
        Возвращает множество имён пакетов-зависимостей.
        """
        pattern = r"(^[a-zA-Z\d_-]+)\s*(>=|<=|==|!=|~=|<|>)?\s*([\d\.-_]*)"
        deps = set()

        for dep in dependencies:
            if 'extra' in dep:
                # Игнорируем optional extras
                continue

            dep_str = dep.strip().split(';')[0]
            match = re.match(pattern, dep_str)
            if match:
                package_name = match.group(1)
                deps.add(package_name)

        return deps

    def get_direct_dependencies(self, name: str, version: str = ''):
        package_info = self.load_package_info(name, version)
        info = package_info['info']
        requires_dist = info.get('requires_dist', []) or []
        deps = self.parse_dependencies(requires_dist)
        return deps

    def print_direct_dependencies(self):
        """Вывод прямых зависимостей (как на этапе 2)."""
        package_name = self.params['package_name']
        version = self.params['version']

        deps = self.get_direct_dependencies(package_name, version)

        print("Прямые зависимости пакета:")
        if not deps:
            print("  Пакет не имеет зависимостей.")
        else:
            for d in sorted(deps):
                print(f"  {d}")

    def _load_test_graph(self, path: str):
        graph = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split(':')
                    pkg = parts[0].strip()
                    deps = []
                    if len(parts) > 1 and parts[1].strip():
                        deps = parts[1].strip().split()
                    graph[pkg] = deps
        except FileNotFoundError:
            print(f"ERROR: test graph file '{path}' not found", file=sys.stderr)
            sys.exit(1)

        return graph

    def build_dependency_graph(self):
        package_name = self.params['package_name']
        version = self.params['version']

        max_depth = int(self.params.get('max_depth', '3'))
        ignore_substring = self.params.get('ignore_substring', '')
        test_mode = self.params.get('test_mode', 'false').lower() == 'true'
        test_file_path = self.params.get('test_file_path', 'test_repo.txt')

        # граф, который мы построим
        graph = {}
        cycles = []

        # если test_mode, заранее загружаем тестовый граф
        test_graph = None
        if test_mode:
            test_graph = self._load_test_graph(test_file_path)

        # стек для DFS: (node, depth, path)
        stack = [(package_name, 0, [package_name])]
        visited = set()

        while stack:
            node, depth, path = stack.pop()

            # фильтр по глубине
            if depth > max_depth:
                continue

            # фильтр по подстроке
            if ignore_substring and ignore_substring in node:
                continue

            if node in visited:
                continue
            visited.add(node)

            # получаем прямые зависимости для текущего узла
            if test_mode:
                deps = test_graph.get(node, [])
                deps = list(deps)
            else:
                # для корневого пакета учитываем указанную версию
                if node == package_name:
                    direct = self.get_direct_dependencies(node, version)
                else:
                    # для транзитивных — берём последнюю версию (version не указываем)
                    direct = self.get_direct_dependencies(node, '')
                deps = list(direct)

            # фильтрация по подстроке
            if ignore_substring:
                deps = [d for d in deps if ignore_substring not in d]

            graph.setdefault(node, set())
            for dep in deps:
                graph[node].add(dep)

                if dep in path:
                    # цикл: путь + текущая зависимость
                    cycles.append(path + [dep])
                    continue

                # добавляем в стек следующий уровень
                stack.append((dep, depth + 1, path + [dep]))


        print("\nГраф зависимостей (до глубины", max_depth, "):")
        for pkg in sorted(graph.keys()):
            deps = sorted(graph[pkg])
            if deps:
                print(f"  {pkg} -> {', '.join(deps)}")
            else:
                print(f"  {pkg} -> (нет зависимостей)")

        if cycles:
            print("\nОбнаружены циклы зависимостей:")
            for c in cycles:
                print("  " + " -> ".join(c))
        else:
            print("\nЦиклы зависимостей не обнаружены.")


if __name__ == "__main__":
    analyzer = CLI_PIP('csv_file')

    analyzer.print_direct_dependencies()

    # Этап 3: построение графа зависимостей
    analyzer.build_dependency_graph()