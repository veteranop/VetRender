"""
VetRender - RF Propagation Tool
Main entry point
"""
import tkinter as tk
from gui.main_window import VetRender

if __name__ == "__main__":
    print("="*60)
    print("VetRender - RF Propagation Tool")
    print("="*60)
    print("Debug logging enabled - all operations will be printed to console")
    print("You can copy/paste this output for troubleshooting")
    print("="*60 + "\n")
    
    root = tk.Tk()
    app = VetRender(root)
    root.mainloop()