"""
Auto-patcher to fix the calculate_propagation function
Runs once and then deletes itself
"""
import os

# Read the file
with open('gui/main_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start of calculate_propagation
start_idx = None
for i, line in enumerate(lines):
    if 'def calculate_propagation(self):' in line:
        start_idx = i
        break

if start_idx is None:
    print("ERROR: Could not find calculate_propagation function!")
    exit(1)

# Find the end (next def at same indentation)
end_idx = None
for i in range(start_idx + 1, len(lines)):
    if lines[i].startswith('    def ') and not lines[i].startswith('        '):
        end_idx = i
        break

if end_idx is None:
    print("ERROR: Could not find end of calculate_propagation function!")
    exit(1)

print(f"Found calculate_propagation from line {start_idx+1} to {end_idx}")
print(f"Replacing {end_idx - start_idx} lines...")

# Read the fixed version
with open('calculate_propagation_FIXED_v2.py', 'r', encoding='utf-8') as f:
    fixed_code = f.read()

# Extract just the function body (remove the leading comment)
fixed_lines = fixed_code.split('\n')
# Skip the comment lines at the start
function_start = None
for i, line in enumerate(fixed_lines):
    if line.startswith('def calculate_propagation'):
        function_start = i
        break

if function_start is None:
    print("ERROR: Could not find function in fixed file!")
    exit(1)

fixed_function = '\n'.join(fixed_lines[function_start:])

# Replace the old function
new_lines = lines[:start_idx] + [fixed_function + '\n'] + lines[end_idx:]

# Write back
with open('gui/main_window.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ Successfully patched calculate_propagation")
print("✓ Deleting patcher script...")

# Delete this script
os.remove(__file__)
print("✓ Done!")
