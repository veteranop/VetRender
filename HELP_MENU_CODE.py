"""
COPY THIS CODE INTO gui/main_window.py
========================================
Add these methods and updates to integrate the Help menu
"""

# ============================================================================
# STEP 1: Add these imports at the top of main_window.py
# ============================================================================
import webbrowser
import urllib.parse


# ============================================================================
# STEP 2: Add these four methods to the VetRender class
# Place them after your existing methods (e.g., after on_closing())
# ============================================================================

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


# ============================================================================
# STEP 3: Update get_menu_callbacks() method
# Find this method and ADD these four lines to the return dictionary
# ============================================================================

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
        
        # ADD THESE FOUR LINES:
        'on_show_help': self.show_help,
        'on_about': self.show_about,
        'on_check_updates': self.check_for_updates_manual,
        'on_report_bug': self.report_bug,
    }


# ============================================================================
# STEP 4: Add F1 keyboard shortcut
# Find where keyboard shortcuts are bound (in setup_ui method) and add this:
# ============================================================================

# Keyboard shortcuts
self.root.bind('<Control-n>', lambda e: self.new_project())
self.root.bind('<Control-s>', lambda e: self.save_project())
self.root.bind('<Control-o>', lambda e: self.load_project())
self.root.bind('<Control-q>', lambda e: self.on_closing())
self.root.bind('<F1>', lambda e: self.show_help())  # ADD THIS LINE


# ============================================================================
# DONE! Test the Help menu:
# - Press F1 or Help > User Guide
# - Click Help > About VetRender
# - Click Help > Check for Updates
# - Click Help > Report a Bug
# ============================================================================
