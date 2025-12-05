import os
import subprocess
import webbrowser

def load_test_graph(path: str = "test_repo.txt"):
    graph = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Разделяем на 'пакет: зависимости'
                parts = line.split(":")
                pkg = parts[0].strip()
                deps = []
                if len(parts) > 1 and parts[1].strip():
                    deps = parts[1].strip().split()

                graph[pkg] = deps
    except FileNotFoundError:
        print(f"ОШИБКА: файл тестового репозитория '{path}' не найден.")
        exit(1)

    return graph
def build_dependency_subgraph(full_graph: dict, root: str, max_depth: int = 10):
    subgraph = {}
    stack = [(root, 0)]
    visited = set()

    while stack:
        node, depth = stack.pop()
        if depth > max_depth:
            continue

        if node in visited:
            continue
        visited.add(node)

        deps = full_graph.get(node, [])
        subgraph.setdefault(node, set())

        for d in deps:
            subgraph[node].add(d)
            stack.append((d, depth + 1))

    return subgraph

def save_graphviz(graph: dict, filename: str):
    lines = ["digraph dependencies {"]

    for pkg, deps in graph.items():
        if not deps:
            lines.append(f'    "{pkg}";')
        else:
            for d in deps:
                lines.append(f'    "{pkg}" -> "{d}";')

    lines.append("}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def generate_png(dot_file: str, png_file: str):
    cmd = ["dot", "-Tpng", dot_file, "-o", png_file]
    try:
        subprocess.run(cmd, check=True)
        print(f"PNG создан: {png_file}")
    except Exception as e:
        print("ОШИБКА запуска Graphviz (dot):", e)

def visualize_stage_5():
    full_graph = load_test_graph("test_repo.txt")
    roots = ["A", "B", "C"]

    print("Пакеты в тестовом репозитории:", ", ".join(sorted(full_graph.keys())))
    print("Будем визуализировать для пакетов:", ", ".join(roots))

    for root in roots:
        if root not in full_graph:
            print(f"\n[ПРОПУСК] Пакет {root} отсутствует в test_repo.txt")
            continue

        print(f"\n=== Строим граф для пакета {root} ===")

        subgraph = build_dependency_subgraph(full_graph, root, max_depth=10)

        dot_file = f"{root}_deps.dot"
        png_file = f"{root}_deps.png"

        save_graphviz(subgraph, dot_file)
        print(f"Graphviz-файл создан: {dot_file}")

        generate_png(dot_file, png_file)

        if os.path.exists(png_file):
            try:
                webbrowser.open(os.path.abspath(png_file))
                print(f"Открываю: {png_file}")
            except Exception as e:
                print("Не удалось автоматически открыть PNG:", e)

if __name__ == "__main__":
    visualize_stage_5()