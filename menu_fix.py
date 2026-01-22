#!/usr/bin/env python3

# Manually fix the menu callbacks by finding the get_menu_callbacks method

with open('gui/main_window.py', 'r') as f:
    content = f.read()

# Find the get_menu_callbacks method
start_idx = content.find('def get_menu_callbacks(self):')
if start_idx == -1:
    print("get_menu_callbacks method not found")
    exit(1)

print(f"Found get_menu_callbacks at position {start_idx}")

# Find the return statement
return_idx = content.find('return {', start_idx)
if return_idx == -1:
    print("return statement not found")
    exit(1)

print(f"Found return at position {return_idx}")

# Find the closing brace of the dictionary
brace_count = 0
end_idx = return_idx
for i in range(return_idx, len(content)):
    if content[i] == '{':
        brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end_idx = i
            break

dict_content = content[return_idx:end_idx+1]
print("Dictionary content:")
print(dict_content)

# Check if FCC callbacks are already there
if "'on_fcc_" in dict_content:
    print("FCC callbacks already present")
else:
    print("Adding FCC callbacks")

    # Find the last line before the closing }
    lines = dict_content.split('\n')
    insert_idx = -1
    for i in range(len(lines)-1, -1, -1):
        if lines[i].strip() and not lines[i].strip().endswith(',') and not lines[i].strip().endswith('{'):
            insert_idx = i
            break

    if insert_idx >= 0:
        # Add comma to the previous line if needed
        if not lines[insert_idx].strip().endswith(','):
            lines[insert_idx] += ','

        # Insert FCC callbacks
        fcc_lines = [
            "        'on_fcc_pull_current': self.fcc_pull_current_station,",
            "        'on_fcc_view': self.fcc_view_data,",
            "        'on_fcc_purge': self.fcc_purge_data,",
            "        'on_fcc_manual': self.fcc_manual_query,"
        ]

        lines[insert_idx+1:insert_idx+1] = fcc_lines

        new_dict_content = '\n'.join(lines)
        new_content = content.replace(dict_content, new_dict_content)

        with open('gui/main_window.py', 'w') as f:
            f.write(new_content)

        print("FCC callbacks added successfully")
    else:
        print("Could not find insertion point")