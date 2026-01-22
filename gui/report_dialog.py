"""
Report Configuration Dialog
============================
Dialog for configuring report generation options.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class ReportConfigDialog:
    """Dialog for configuring report generation"""

    def __init__(self, parent, config_manager):
        """Initialize report configuration dialog

        Args:
            parent: Parent window
            config_manager: Configuration manager instance
        """
        self.parent = parent
        self.config = config_manager
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Generate Report")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Create UI
        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI"""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Report Configuration",
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = ttk.Label(main_frame,
                              text="Select the sections to include in your report:",
                              wraplength=450)
        desc_label.pack(pady=(0, 15))

        # Create scrollable frame for checkboxes
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Report sections with checkboxes
        self.sections = {}

        # FCC Information Section
        fcc_frame = ttk.LabelFrame(scrollable_frame, text="FCC Database", padding="10")
        fcc_frame.pack(fill=tk.X, pady=5)

        self.sections['fcc_info'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(fcc_frame, text="FCC Filing Information",
                       variable=self.sections['fcc_info']).pack(anchor=tk.W)

        fcc_note = ttk.Label(fcc_frame,
                            text="Search by coordinates and frequency",
                            font=('Arial', 8, 'italic'),
                            foreground='gray')
        fcc_note.pack(anchor=tk.W, padx=20)

        # Station Information Section
        station_frame = ttk.LabelFrame(scrollable_frame, text="Station Details", padding="10")
        station_frame.pack(fill=tk.X, pady=5)

        self.sections['station_info'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(station_frame, text="Station Information",
                       variable=self.sections['station_info']).pack(anchor=tk.W)

        self.sections['transmitter_info'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(station_frame, text="Transmitter Specifications",
                       variable=self.sections['transmitter_info']).pack(anchor=tk.W)

        self.sections['frequency_info'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(station_frame, text="Frequency & Power Information",
                       variable=self.sections['frequency_info']).pack(anchor=tk.W)

        # RF Chain Section
        rf_frame = ttk.LabelFrame(scrollable_frame, text="RF System", padding="10")
        rf_frame.pack(fill=tk.X, pady=5)

        self.sections['rf_chain'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(rf_frame, text="RF Chain Summary",
                       variable=self.sections['rf_chain']).pack(anchor=tk.W)

        self.sections['cable_report'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(rf_frame, text="Cable Report (Types & Lengths)",
                       variable=self.sections['cable_report']).pack(anchor=tk.W)

        self.sections['loss_budget'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(rf_frame, text="Detailed Loss Budget",
                       variable=self.sections['loss_budget']).pack(anchor=tk.W)

        self.sections['antenna_info'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(rf_frame, text="Antenna Specifications",
                       variable=self.sections['antenna_info']).pack(anchor=tk.W)

        # Coverage Maps Section
        coverage_frame = ttk.LabelFrame(scrollable_frame, text="Coverage Analysis", padding="10")
        coverage_frame.pack(fill=tk.X, pady=5)

        self.sections['coverage_maps'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(coverage_frame, text="Coverage Maps",
                       variable=self.sections['coverage_maps']).pack(anchor=tk.W)

        # Zoom level selection
        zoom_subframe = ttk.Frame(coverage_frame)
        zoom_subframe.pack(anchor=tk.W, padx=20, pady=5)

        ttk.Label(zoom_subframe, text="Zoom levels:").pack(side=tk.LEFT)

        self.zoom_levels = {}
        for zoom in [9, 10, 11, 12, 13]:
            self.zoom_levels[zoom] = tk.BooleanVar(value=zoom in [10, 11, 12])
            ttk.Checkbutton(zoom_subframe, text=str(zoom),
                           variable=self.zoom_levels[zoom]).pack(side=tk.LEFT, padx=5)

        self.sections['coverage_stats'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(coverage_frame, text="Coverage Statistics",
                       variable=self.sections['coverage_stats']).pack(anchor=tk.W)

        # Additional Information Section
        additional_frame = ttk.LabelFrame(scrollable_frame, text="Additional", padding="10")
        additional_frame.pack(fill=tk.X, pady=5)

        self.sections['terrain_profile'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(additional_frame, text="Terrain Profile Analysis",
                       variable=self.sections['terrain_profile']).pack(anchor=tk.W)

        self.sections['compliance'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(additional_frame, text="FCC Compliance Check",
                       variable=self.sections['compliance']).pack(anchor=tk.W)

        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Output format section
        format_frame = ttk.LabelFrame(main_frame, text="Output Format", padding="10")
        format_frame.pack(fill=tk.X, pady=10)

        self.format_var = tk.StringVar(value="PDF")
        ttk.Radiobutton(format_frame, text="PDF Document",
                       variable=self.format_var, value="PDF").pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Generate Report",
                  command=self.on_generate, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                  command=self.on_cancel, width=15).pack(side=tk.LEFT, padx=5)

        # Quick select buttons
        quick_frame = ttk.Frame(main_frame)
        quick_frame.pack(pady=5)

        ttk.Button(quick_frame, text="Select All",
                  command=self.select_all, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="Select None",
                  command=self.select_none, width=12).pack(side=tk.LEFT, padx=5)

    def select_all(self):
        """Select all report sections"""
        for var in self.sections.values():
            var.set(True)
        for var in self.zoom_levels.values():
            var.set(True)

    def select_none(self):
        """Deselect all report sections"""
        for var in self.sections.values():
            var.set(False)
        for var in self.zoom_levels.values():
            var.set(False)

    def on_generate(self):
        """Handle generate button click"""
        # Collect selected sections
        selected_sections = {
            key: var.get() for key, var in self.sections.items()
        }

        # Collect selected zoom levels
        selected_zooms = [zoom for zoom, var in self.zoom_levels.items() if var.get()]

        # Check if at least one section is selected
        if not any(selected_sections.values()):
            messagebox.showwarning("No Sections Selected",
                                 "Please select at least one report section.")
            return

        self.result = {
            'sections': selected_sections,
            'zoom_levels': selected_zooms,
            'format': self.format_var.get()
        }

        self.dialog.destroy()

    def on_cancel(self):
        """Handle cancel button click"""
        self.result = None
        self.dialog.destroy()

    def show(self):
        """Show dialog and wait for result

        Returns:
            Dictionary with report configuration or None
        """
        self.dialog.wait_window()
        return self.result
