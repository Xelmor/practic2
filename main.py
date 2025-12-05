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
            return {"info": {"requires_dist": []}}

    def parse_dependencies(self, dependencies):
        pattern = r"(^[a-zA-Z\d_-]+)"
        deps = set()

        if not dependencies:
            return deps

        for dep in dependencies:
            dep_clean = dep.strip().split(';')[0]
            match = re.match(pattern, dep_clean)
            if match:
                deps.add(match.group(1))

        return deps

    def get_direct_dependencies(self, name: str, version: str = ''):
        info = self.load_package_info(name, version)
        requires = info.get("info", {}).get("requires_dist", [])
        return self.parse_dependencies(requires)

    def print_direct_dependencies(self):
        pkg = self.params["package_name"]
        ver = self.params["version"]

        deps = self.get_direct_dependencies(pkg, ver)

        print("Прямые зависимости пакета:")
        if not deps:
            print("  (нет зависимостей)")
        else:
            for d in sorted(deps):
                print(" ", d)


    def _load_test_graph(self, path: str):
        graph = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    pkg, deps = line.split(':')
                    pkg = pkg.strip()
                    deps_list = deps.strip().split() if deps.strip() else []
                    graph[pkg] = deps_list
        except:
            print(f"Ошибка загрузки тестового файла {path}")
            sys.exit(1)
        return graph

    def build_dependency_graph(self):
        pkg = self.params["package_name"]
        ver = self.params["version"]
        max_depth = int(self.params.get("max_depth", "3"))
        ignore = self.params.get("ignore_substring", "")
        test_mode = self.params.get("test_mode", "false").lower() == "true"
        test_file = self.params.get("test_file_path", "test_repo.txt")

        graph = {}
        cycles = []
        visited = set()

        test_graph = self._load_test_graph(test_file) if test_mode else None

        stack = [(pkg, 0, [pkg])]

        while stack:
            node, depth, path = stack.pop()

            if depth > max_depth:
                continue
            if ignore and ignore in node:
                continue
            if node in visited:
                continue

            visited.add(node)
            graph.setdefault(node, set())

            if test_mode:
                deps = test_graph.get(node, [])
            else:
                deps = (
                    self.get_direct_dependencies(node, ver)
                    if node == pkg else
                    self.get_direct_dependencies(node, "")
                )

            deps = [d for d in deps if not ignore or ignore not in d]

            for d in deps:
                if d in path:
                    cycles.append(path + [d])
                    continue

                graph[node].add(d)
                stack.append((d, depth + 1, path + [d]))

        print("\nГраф зависимостей (до глубины", max_depth, "):")
        for node in sorted(graph.keys()):
            d = sorted(graph[node])
            if d:
                print(f"  {node} -> {', '.join(d)}")
            else:
                print(f"  {node} -> (нет зависимостей)")

        if cycles:
            print("\nОбнаружены циклы зависимостей:")
            for c in cycles:
                print("  " + " -> ".join(c))
        else:
            print("\nЦиклы зависимостей не обнаружены.")

    def print_reverse_dependencies(self):
        test_mode = self.params.get("test_mode", "false").lower() == "true"
        test_file = self.params.get("test_file_path", "test_repo.txt")

        if not test_mode:
            print("\nОбратные зависимости доступны только при test_mode=true")
            return

        graph = self._load_test_graph(test_file)

        reverse_graph = {pkg: [] for pkg in graph}

        for pkg, deps in graph.items():
            for d in deps:
                reverse_graph.setdefault(d, [])
                reverse_graph[d].append(pkg)

        print("\nОБРАТНЫЕ ЗАВИСИМОСТИ:")
        for pkg in sorted(reverse_graph.keys()):
            rev = reverse_graph[pkg]
            if rev:
                print(f"  {pkg} <- {', '.join(sorted(rev))}")
            else:
                print(f"  {pkg} <- (нет зависимых пакетов)")

if __name__ == "__main__":
    analyzer = CLI_PIP('csv_file')

    analyzer.print_direct_dependencies()
    analyzer.build_dependency_graph()
    analyzer.print_reverse_dependencies()
