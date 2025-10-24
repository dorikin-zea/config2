import argparse
import sys

def main():
    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description='Dependency graph visualizer')
    
    # Добавляем аргументы командной строки
    parser.add_argument('--package', required=True, help='Package name to analyze')
    parser.add_argument('--repo', required=True, help='Repository URL or path to test repository')
    parser.add_argument('--test-mode', choices=['on', 'off'], default='off', help='Test repository mode')
    parser.add_argument('--version', help='Package version')
    parser.add_argument('--output', default='graph.png', help='Output image filename')
    parser.add_argument('--ascii-tree', choices=['on', 'off'], default='off', help='ASCII tree output mode')
    parser.add_argument('--max-depth', type=int, default=10, help='Maximum dependency analysis depth')
    
    # Парсим аргументы
    args = parser.parse_args()
    
    # Выводим параметры, переданные пользователем
    try:
        print("User configured parameters:")
        print(f"package: {args.package}")
        print(f"repo: {args.repo}")
        print(f"test_mode: {args.test_mode}")
        print(f"version: {args.version}")
        print(f"output: {args.output}")
        print(f"ascii_tree: {args.ascii_tree}")
        print(f"max_depth: {args.max_depth}")
        
        # Обрабатываем ошибки и выходим с кодом ошибки
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()