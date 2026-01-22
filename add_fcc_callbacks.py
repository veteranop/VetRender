#!/usr/bin/env python3

# Script to add FCC callbacks to get_menu_callbacks method

with open('gui/main_window.py', 'r') as f:
    content = f.read()

# Find the get_menu_callbacks method return dictionary
import re

# Pattern to find the return dictionary in get_menu_callbacks
pattern = r'(def get_menu_callbacks\(self\):.*?)(\n    return \{.*?\n    \})'

match = re.search(pattern, content, re.DOTALL)
if match:
    method_start = match.group(1)
    return_dict = match.group(2)

    print("Found get_menu_callbacks method")
    print("Current return dictionary:")
    print(return_dict)

    # Check if FCC callbacks are already there
    if 'on_fcc_' in return_dict:
        print("FCC callbacks already present")
    else:
        print("Adding FCC callbacks")

        # Find the closing brace
        lines = return_dict.split('\n')
        last_line_idx = len(lines) - 1

        # Insert FCC callbacks before the closing brace
        fcc_lines = [
            "        'on_fcc_pull_current': self.fcc_pull_current_station,",
            "        'on_fcc_view': self.fcc_view_data,",
            "        'on_fcc_purge': self.fcc_purge_data,",
            "        'on_fcc_manual': self.fcc_manual_query,"
        ]

        # Insert before the last line (which should be '}')
        lines.insert(last_line_idx, '\n'.join(fcc_lines))

        new_return_dict = '\n'.join(lines)

        # Replace in content
        new_content = content.replace(return_dict, new_return_dict)

        with open('gui/main_window.py', 'w') as f:
            f.write(new_content)

        print("FCC callbacks added successfully")
else:
    print("Could not find get_menu_callbacks method return dictionary")