# Help Menu Integration Guide
**Created:** 2025-01-16

## Overview
This guide shows how to add the Help menu to VetRender's main window.

## Files Created

1. **gui/menus.py** - Updated with Help menu
2. **help.html** - Comprehensive user guide (HTML format)
3. **HELP_MENU_INTEGRATION.md** - This file

## Changes Required to main_window.py

### 1. Add Import at Top
```python
import webbrowser
import urllib.parse
```

### 2. Add Help Menu Methods to VetRender Class

Add these four methods to the `VetRender` class (after existing methods):

```python
def show_help(self):
    """Open help documentation in default browser"""
    help_path = os.path.join(os.path.dirname(__file__), "../help.html")
    help_path = os.path.abspath(help_path)
    
    if os.path.exists(help_path):
        webbrowser.open(f'file://{help_path}')
    else:
        messagebox.showerror("Help Not Found",
                           "Help documentation file not found.\n\n"
                           "Expected location: help.html")

def show_about(self):
    """Show About dialog"""
    try:
        version = auto_updater.CURRENT_VERSION
    except:
        version = "3.0.1"
    
    about_text = f"""VetRender
Professional RF Propagation Analysis Tool

Version: {version}

VetRender provides accurate RF propagation modeling with terrain analysis,
custom antenna patterns, and AI-powered tools for wireless engineers.

Created by: VetRender Team
Website: veteranop.com
Email: mark@veteranop.com

© 2025 VetRender. All rights reserved.

Technologies Used:
• Python & Tkinter
• Matplotlib & NumPy
• SciPy for interpolation
• Open-Elevation API for terrain
• OpenStreetMap for maps
• Ollama for local AI
"""
    
    messagebox.showinfo("About VetRender", about_text)

def check_for_updates_manual(self):
    """Manually check for updates"""
    self.toolbar.set_status("Checking for updates...")
    self.root.update()
    
    try:
        # Placeholder - will be implemented in separate chat
        messagebox.showinfo("Check for Updates",
                          "Update check functionality coming soon!\n\n"
                          "This feature will check GitHub for the latest version\n"
                          "and provide download/update options.\n\n"
                          "Current Version: 3.0.1")
        self.toolbar.set_status("Ready")
    except Exception as e:
        messagebox.showerror("Update Check Failed",
                           f"Failed to check for updates:\n{e}")
        self.toolbar.set_status("Update check failed")

def report_bug(self):
    """Open email client to report a bug"""
    try:
        version = auto_updater.CURRENT_VERSION
    except:
        version = "3.0.1"
    
    # Email details
    recipient = "mark@veteranop.com"
    subject = f"VetRender Bug Report - v{version}"
    body = f"""[Please describe the bug you encountered]

ISSUE DESCRIPTION:


STEPS TO REPRODUCE:
1. 
2. 
3. 

EXPECTED BEHAVIOR:


ACTUAL BEHAVIOR:


SYSTEM INFORMATION:
VetRender Version: {version}
Call Sign: {self.callsign}
Transmitter: {self.tx_lat:.6f}, {self.tx_lon:.6f}
Frequency: {self.frequency} MHz
ERP: {self.erp} dBm

[If available, please attach console logs or screenshots]
"""
    
    # Create mailto link
    mailto_link = f"mailto:{recipient}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    
    try:
        webbrowser.open(mailto_link)
    except Exception as e:
        # Fallback - show email info in message box
        messagebox.showinfo("Report Bug",
                          f"Please email your bug report to:\n\n"
                          f"{recipient}\n\n"
                          f"Subject: {subject}\n\n"
                          f"Your default email client should open automatically.\n"
                          f"If not, copy the email address above.")
```

### 3. Update get_menu_callbacks() Method

Find the `get_menu_callbacks()` method and add these lines to the return dictionary:

```python
def get_menu_callbacks(self):
    """Get menu callback dictionary"""
    return {
        'on_new_project': self.new_project,
        'on_save_project': self.save_project,
        'on_load_project': self.load_project,
        'on_exit': self.on_closing,
        'on_basemap_change': self.on_basemap_change,
        'on_toggle_coverage': self.toggle_coverage_overlay,
        'on_toggle_shadow': self.update_shadow_display,
        'on_max_distance_change': self.on_max_distance_change,
        'on_custom_distance': self.set_custom_distance,
        'on_toggle_terrain': lambda: None,
        'on_quality_change': self.on_quality_change,
        'on_terrain_detail_change': self.on_terrain_detail_change,
        'on_custom_terrain_detail': self.set_custom_terrain_detail,
        
        # NEW: Help menu callbacks
        'on_show_help': self.show_help,
        'on_about': self.show_about,
        'on_check_updates': self.check_for_updates_manual,
        'on_report_bug': self.report_bug,
    }
```

### 4. Add F1 Keyboard Shortcut

In the `setup_ui()` method, find where keyboard shortcuts are bound and add:

```python
# Keyboard shortcuts
self.root.bind('<Control-n>', lambda e: self.new_project())
self.root.bind('<Control-s>', lambda e: self.save_project())
self.root.bind('<Control-o>', lambda e: self.load_project())
self.root.bind('<Control-q>', lambda e: self.on_closing())
self.root.bind('<F1>', lambda e: self.show_help())  # NEW: F1 for help
```

## Files That Need to Be Included in Build

Update `vetrender.spec` to include help.html:

```python
datas=[
    # Include all Python modules
    ('gui', 'gui'),
    ('controllers', 'controllers'),
    ('models', 'models'),
    ('auto_updater.py', '.'),
    ('debug_logger.py', '.'),
    # Include documentation
    ('README.md', '.'),
    ('LICENSE', '.'),
    ('help.html', '.'),  # NEW: Include help documentation
],
```

## Testing the Help Menu

After making the changes:

1. **Test Help Guide**
   - Click Help > User Guide (or press F1)
   - Should open help.html in your default browser
   - Verify all sections load correctly

2. **Test About Dialog**
   - Click Help > About VetRender
   - Should show version and credits

3. **Test Check for Updates**
   - Click Help > Check for Updates
   - Should show placeholder message (functionality coming soon)

4. **Test Report Bug**
   - Click Help > Report a Bug
   - Should open email client with pre-filled template
   - Includes current system configuration

## Help Document Sections

The help.html includes:

1. **Getting Started** - Quick start guide
2. **Interface Overview** - GUI components and shortcuts
3. **RF Propagation Modeling** - How calculations work
4. **Antenna Patterns** - Import/export patterns
5. **Terrain Analysis** - Enable and configure terrain
6. **Settings & Configuration** - All parameters explained
7. **AI Features** - AI tools documentation
8. **Troubleshooting** - Common issues and solutions
9. **Appendix** - RF terminology, power conversion tables

## Future Enhancements

### Check for Updates (Coming Soon)
Will be implemented in a separate chat to:
- Query GitHub API for latest release
- Compare with current version
- Show download link if update available
- Optional auto-update functionality

### AI Features Documentation
As AI features are completed:
- Update help.html with actual usage instructions
- Remove "Coming Soon" placeholders
- Add screenshots and examples

## Notes

- Help document is fully self-contained (CSS inline, no external resources)
- Works offline once included in the build
- Professional styling with gradient headers
- Responsive design works on different screen sizes
- Easy to update - just edit help.html

## Version History

- **v3.0.1** (2025-01-16)
  - Added Help menu
  - Created comprehensive user guide
  - Added About dialog
  - Added placeholder for update checker
  - Added bug report email integration
