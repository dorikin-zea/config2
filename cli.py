import argparse
import urllib.request
import urllib.error
import re
import os
import sys
import gzip
from typing import List, Dict, Optional

class DependencyExtractor:
    def __init__(self):
        self.cache = {}
    
    def get_package_content(self, repository_url: str, package_name: str, version: str) -> str:
        """Получает содержимое страницы пакета из репозитория"""
        try:
            # Нормализуем URL репозитория
            if repository_url.endswith('/'):
                repository_url = repository_url[:-1]
            
            # Для Ubuntu репозиториев используем правильную структуру URL
            # Формируем URL к сжатому файлу Packages.gz
            packages_url = f"{repository_url}/Packages.gz"
            
            print(f"Попытка доступа к: {packages_url}")
            
            # Если это файловая система
            if repository_url.startswith('file://'):
                file_path = repository_url[7:]
                if os.path.isdir(file_path):
                    file_path = os.path.join(file_path, "Packages.gz")
                
                if os.path.exists(file_path):
                    with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                else:
                    # Попробуем несжатый файл
                    file_path = file_path.replace('.gz', '')
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            return f.read()
                    else:
                        raise Exception(f"Файл Packages не найден по пути: {file_path}")
            else:
                # Скачиваем и распаковываем gz файл
                with urllib.request.urlopen(packages_url) as response:
                    compressed_content = response.read()
                    content = gzip.decompress(compressed_content).decode('utf-8', errors='ignore')
                    return content
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Попробуем несжатый файл Packages
                try:
                    packages_url = f"{repository_url}/Packages"
                    print(f"Попытка доступа к несжатому файлу: {packages_url}")
                    with urllib.request.urlopen(packages_url) as response:
                        return response.read().decode('utf-8', errors='ignore')
                except urllib.error.HTTPError as e2:
                    raise Exception(f"Не удалось найти файл Packages в репозитории. URL: {packages_url}")
            else:
                raise Exception(f"Ошибка доступа к репозиторию: {e}")
        except Exception as e:
            raise Exception(f"Ошибка при получении данных пакета: {e}")
    
    def parse_package_info(self, content: str, package_name: str, version: str) -> Optional[Dict]:
        """Парсит информацию о пакете из содержимого репозитория"""
        # Разделяем на отдельные пакеты (двойной перевод строки - разделитель)
        packages = content.split('\n\n')
        
        for package_block in packages:
            if not package_block.strip():
                continue
                
            lines = package_block.strip().split('\n')
            package_data = {}
            current_field = None
            
            for line in lines:
                if line and not line.startswith(' '):
                    # Новое поле
                    if ':' in line:
                        field, value = line.split(':', 1)
                        current_field = field.strip()
                        package_data[current_field] = value.strip()
                elif current_field and line.startswith(' '):
                    # Продолжение предыдущего поля
                    package_data[current_field] += ' ' + line.strip()
            
            # Проверяем, нужный ли это пакет
            if package_data.get('Package') == package_name:
                # Проверяем версию (может быть частичное совпадение)
                pkg_version = package_data.get('Version', '')
                if version in pkg_version or version == pkg_version:
                    return package_data
        
        # Если точное совпадение не найдено, попробуем найти любой пакет с таким именем
        for package_block in packages:
            if not package_block.strip():
                continue
                
            lines = package_block.strip().split('\n')
            package_data = {}
            current_field = None
            
            for line in lines:
                if line and not line.startswith(' '):
                    if ':' in line:
                        field, value = line.split(':', 1)
                        current_field = field.strip()
                        package_data[current_field] = value.strip()
                elif current_field and line.startswith(' '):
                    package_data[current_field] += ' ' + line.strip()
            
            if package_data.get('Package') == package_name:
                print(f"Предупреждение: точная версия {version} не найдена, используется версия {package_data.get('Version')}")
                return package_data
        
        return None
    
    def extract_dependencies(self, package_data: Dict) -> List[str]:
        """Извлекает зависимости из данных пакета"""
        dependencies = []
        
        # Основные зависимости
        depends_field = package_data.get('Depends', '')
        if depends_field:
            deps = self.parse_dependency_field(depends_field)
            dependencies.extend(deps)
        
        return dependencies
    
    def parse_dependency_field(self, field: str) -> List[str]:
        """Парсит поле зависимостей и извлекает имена пакетов"""
        dependencies = []
        
        if not field:
            return dependencies
            
        # Удаляем версии и альтернативы
        # Пример: "libc6 (>= 2.14), libgcc1 (>= 1:3.0) | libgcc2" -> ["libc6", "libgcc1", "libgcc2"]
        field = re.sub(r'\([^)]*\)', '', field)  # Удаляем версии в скобках
        
        # Разделяем по запятым и вертикальным чертам
        parts = re.split(r'[,|]', field)
        
        for part in parts:
            part = part.strip()
            if part and not part.isspace():
                dependencies.append(part)
        
        return dependencies
    
    def get_dependencies(self, package_name: str, version: str, repository_url: str) -> List[str]:
        """Основной метод для получения зависимостей пакета"""
        print(f"Получение зависимостей для пакета: {package_name} версии {version}")
        print(f"Репозиторий: {repository_url}")
        
        # Получаем содержимое репозитория
        content = self.get_package_content(repository_url, package_name, version)
        
        # Парсим информацию о пакете
        package_data = self.parse_package_info(content, package_name, version)
        
        if not package_data:
            raise Exception(f"Пакет {package_name} версии {version} не найден в репозитории")
        
        # Извлекаем зависимости
        dependencies = self.extract_dependencies(package_data)
        
        return dependencies

def main():
    parser = argparse.ArgumentParser(description='Визуализатор графа зависимостей пакетов')
    
    # Параметры конфигурации
    parser.add_argument('--package', type=str, required=True, help='Имя анализируемого пакета')
    parser.add_argument('--repository', type=str, required=True, help='URL репозитория или путь к файлу')
    parser.add_argument('--test-repo-mode', action='store_true', help='Режим работы с тестовым репозиторием')
    parser.add_argument('--version', type=str, required=True, help='Версия пакета')
    parser.add_argument('--output', type=str, default='graph.png', help='Имя файла для изображения графа')
    parser.add_argument('--ascii-tree', action='store_true', help='Вывод зависимостей в формате ASCII-дерева')
    parser.add_argument('--max-depth', type=int, default=0, help='Максимальная глубина анализа')
    
    args = parser.parse_args()
    
    # Этап 1: Вывод параметров конфигурации
    print("=== КОНФИГУРАЦИЯ ПАРАМЕТРОВ ===")
    config_params = {
        'package': args.package,
        'repository': args.repository,
        'test_repo_mode': args.test_repo_mode,
        'version': args.version,
        'output': args.output,
        'ascii_tree': args.ascii_tree,
        'max_depth': args.max_depth
    }
    
    for key, value in config_params.items():
        print(f"{key}: {value}")
    print()
    
    try:
        # Этап 2: Получение зависимостей
        extractor = DependencyExtractor()
        dependencies = extractor.get_dependencies(args.package, args.version, args.repository)
        
        print("=== ПРЯМЫЕ ЗАВИСИМОСТИ ПАКЕТА ===")
        if dependencies:
            for i, dep in enumerate(dependencies, 1):
                print(f"{i}. {dep}")
        else:
            print("Зависимости не найдены")
            
    except Exception as e:
        print(f"Ошибка при получении зависимостей: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()