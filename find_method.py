#!/usr/bin/env python3

with open('gui/main_window.py', 'r') as f:
    lines = f.readlines()

# Find get_menu_callbacks method
start_line = None
for i, line in enumerate(lines):
    if 'def get_menu_callbacks(self):' in line:
        start_line = i
        break

if start_line is None:
    print("get_menu_callbacks method not found")
    exit(1)

print(f"get_menu_callbacks found at line {start_line + 1}")

# Read the method content
method_lines = []
for i in range(start_line, len(lines)):
    line = lines[i]
    method_lines.append(line)
    # Check for end of method (next def or class)
    if i > start_line and (line.strip().startswith('def ') or line.strip().startswith('class ')):
        break

method_content = ''.join(method_lines)
print("Method content:")
print(method_content)

# Check if FCC callbacks are included
fcc_callbacks = ['on_fcc_pull_current', 'on_fcc_view', 'on_fcc_purge', 'on_fcc_manual']
missing = []
for cb in fcc_callbacks:
    if cb not in method_content:
        missing.append(cb)

if missing:
    print(f"Missing FCC callbacks: {missing}")
else:
    print("All FCC callbacks found")