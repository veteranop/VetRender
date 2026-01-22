#!/usr/bin/env python3

# Script to fix the FCC menu in menus.py

with open('gui/menus.py', 'r') as f:
    content = f.read()

# Check if setup_fcc_menu is already called in setup_menus
if 'self.setup_fcc_menu()' not in content:
    # Add the call to setup_menus
    content = content.replace(
        '        self.setup_station_menu()\n        self.setup_plot_settings_menu()',
        '        self.setup_station_menu()\n        self.setup_fcc_menu()\n        self.setup_plot_settings_menu()'
    )

# Check if setup_fcc_menu method exists
if 'def setup_fcc_menu(self):' not in content:
    # Add the method at the end
    fcc_method = '''
    def setup_fcc_menu(self):
        """Create FCC Query menu"""
        fcc_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Query FCC", menu=fcc_menu)

        fcc_menu.add_command(label="Pull Report for Current Station",
                            command=self.callbacks.get('on_fcc_pull_current', lambda: None))
        fcc_menu.add_command(label="View FCC Data for This Project",
                            command=self.callbacks.get('on_fcc_view', lambda: None))
        fcc_menu.add_command(label="Purge FCC Data from Project",
                            command=self.callbacks.get('on_fcc_purge', lambda: None))
        fcc_menu.add_separator()
        fcc_menu.add_command(label="Pull Report from Station ID",
                            command=self.callbacks.get('on_fcc_manual', lambda: None))
'''
    content += fcc_method

with open('gui/menus.py', 'w') as f:
    f.write(content)

print("FCC menu fix applied to gui/menus.py")