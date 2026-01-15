"""Show lines 245-260 to see the problem"""
with open('gui/main_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Lines 245-260:")
for i in range(244, 260):
    if i < len(lines):
        indent = len(lines[i]) - len(lines[i].lstrip()) if lines[i].strip() else -1
        print(f"{i+1:4d} (indent={indent:2d}): {lines[i].rstrip()}")
