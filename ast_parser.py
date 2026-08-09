import ast
import os

def parse_file(filename):
    if not os.path.exists(filename):
        return
    with open(filename, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    print(f"=== {filename} ===")
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            docstring = ast.get_docstring(node)
            print(f"Function: {node.name}({', '.join(args)})")
            if docstring:
                lines = [l.strip() for l in docstring.split('\n') if l.strip()]
                print(f"  Doc: {lines[0] if lines else 'None'}")
            print("  " + "-" * 20)
        elif isinstance(node, ast.ClassDef):
            print(f"Class: {node.name}")
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    args = [a.arg for a in item.args.args]
                    docstring = ast.get_docstring(item)
                    print(f"  Method: {item.name}({', '.join(args)})")
                    if docstring:
                        lines = [l.strip() for l in docstring.split('\n') if l.strip()]
                        print(f"  Doc: {lines[0] if lines else 'None'}")
                    print("  " + "-" * 20)

parse_file('smartmoneyconcepts/smc.py')
