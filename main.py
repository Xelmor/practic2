import argparse
import sys
import urllib.request
import csv
import gzip
import re
import json


class CLI_PIP:
    def __init__(self, input_type: str = 'command_line'):
        self.input_type = input_type
        if self.input_type == 'command_line':
            self.params = self.command_line()

        if self.input_type == 'csv_file':
            self.params = self.csv_file()

    def csv_file(self):
        params = {}
        try:
            with open('csv_config.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    parameter = row['parameter']
                    value = row['value']
                    params[parameter] = value

            if not params['package_name']:
                raise ValueError('package_name cannot be empty')

            if not params['repo_url']:
                raise ValueError('repo_url')

            return params

        except:
            raise FileNotFoundError('csv_config.csv file not found')

    def print_params(self):
        print(f"Имя пакета: {self.params['package_name']}")
        print(f"Репозиторий: {self.params['repo_url']}")
        print(f"Тестовый режим: {self.params['test_mode']}")
        print(f"Версия: {self.params['version']}")

    def load_package_info(self, name='pandas', version: str = '') -> dict:
        if not version or version == "latest":
            url = f"https://{self.params['repo_url']}{name}/json"
        else:
            url = f"https://{self.params['repo_url']}{name}/{version}/json"

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
            return data
        except Exception as e:
            print(f"Ошибка при получении {name}: {e}")
            sys.exit(1)

    def get_versions(self):
        package_name = self.params['package_name']
        package_info = self.load_package_info(package_name)
        return list(package_info['releases'].keys())

    def get_dependencies(self):
        package_name = self.params['package_name']
        version = self.params['version']

        package_info = self.load_package_info(package_name, version)
        version_info = package_info['info']

        # "requires_dist" содержит прямые зависимости
        requires_dist = version_info.get('requires_dist', [])
        deps = self.parse_dependencies(requires_dist)

        #ЭТАП 2: выводим зависимости
        print("\nПрямые зависимости пакета:")
        if not deps:
            print("  Пакет не имеет зависимостей.")
        else:
            for name, ver in deps:
                if ver:
                    print(f"  {name} ({ver})")
                else:
                    print(f"  {name}")

    def parse_dependencies(self, dependencies):
        pattern = r"(^[a-zA-Z\d_-]+)\s*(>=|<=|==|!=|~=|<|>)?\s*([\d\.-_]*)"
        deps = set()
        result = set()

        for dep in dependencies:
            if 'extra' in dep:
                continue  # игнорируем extras

            dep_str = dep.strip().split(';')[0]
            match = re.match(pattern, dep_str)

            if match:
                name = match.group(1)
                version = match.group(3) if match.group(3) else None

                if name not in deps:
                    deps.add(name)
                    result.add((name, version))

        return result

cl = CLI_PIP('csv_file')
cl.get_dependencies()
