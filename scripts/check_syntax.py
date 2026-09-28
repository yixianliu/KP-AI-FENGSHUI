import ast, pathlib
root = pathlib.Path('core')
files = []
for p in root.rglob('*.py'):
    files.append(str(p))
ok=True
for f in files[:20]:
    try:
        ast.parse(open(f, encoding='utf-8').read())
    except SyntaxError as e:
        print('语法错误', f, e)
        ok=False
print('检查通过' if ok else '存在错误')
