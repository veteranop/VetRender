"""
Cellfire RF Studio - Professional RF Propagation Analysis
Main entry point
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# Add auto-updater check (only if not in development mode)
def check_for_updates():
    try:
        # Only check for updates if running from installed location
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            import auto_updater
            auto_updater.check_for_updates_at_startup()
    except Exception as e:
        print(f"Update check skipped: {e}")

if __name__ == "__main__":
    print("="*60)
    print("Cellfire RF Studio - Professional RF Propagation Analysis")

    # Get version if available
    try:
        import auto_updater
        print(f"Version {auto_updater.CURRENT_VERSION}")
    except:
        pass

    print("="*60)
    print("Debug logging enabled - all operations will be printed to console")
    print("You can copy/paste this output for troubleshooting")
    print("="*60 + "\n")

    # Check for updates
    check_for_updates()

    # Create root window
    root = tk.Tk()

    # Apply modern dark theme
    from gui.theme import apply_theme
    print("Applying modern dark theme...")
    apply_theme(root)
    print("Theme applied successfully")

    # Import and create main application
    from gui.main_window import CellfireRFStudio
    app = CellfireRFStudio(root)
    root.mainloop()