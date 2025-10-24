@echo off
python cli.py --package numpy --repo https://pypi.org --test-mode off --version 1.0 --output deps.png --ascii-tree off --max-depth 5
pause