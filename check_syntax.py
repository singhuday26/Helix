import ast
import sys

try:
    with open('src/inference.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    ast.parse(code)
    print("OK: Syntax is valid!")
    sys.exit(0)
except SyntaxError as e:
    print(f"ERROR: Syntax Error at line {e.lineno}: {e.msg}")
    print(f"  {e.text}")
    sys.exit(1)
