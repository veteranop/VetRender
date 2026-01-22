"""
Quick Add Component Dialog
===========================
Simple dialog for quickly adding custom RF components to the library.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class QuickAddComponentDialog:
    """Quick component creation dialog"""

    def __init__(self, parent, frequency_mhz: float, callback: Optional[Callable] = None):
        """Initialize quick add dialog

        Args:
            parent: Parent window
            frequency_mhz: Operating frequency
            callback: Callback function(component_data)
        """
        self.parent = parent
        self.frequency_mhz = frequency_mhz
        self.callback = callback

        self._create_dialog()

    def _create_dialog(self):
        """Create dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Quick Add Component")
        self.dialog.geometry("600x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="⚡ Quick Add Component",
                         font=('TkDefaultFont', 14, 'bold'))
        title.pack(pady=(0, 10))

        desc = ttk.Label(main_frame, text="Manually create a new RF component",
                        font=('TkDefaultFont', 9, 'italic'))
        desc.pack(pady=(0, 20))

        # Component Type Selection
        type_frame = ttk.LabelFrame(main_frame, text="Component Type", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 15))

        self.comp_type_var = tk.StringVar(value="cable")

        ttk.Radiobutton(type_frame, text="📡 Transmitter", variable=self.comp_type_var,
                       value="transmitter", command=self._on_type_changed).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_frame, text="🔌 Cable / Feedline", variable=self.comp_type_var,
                       value="cable", command=self._on_type_changed).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_frame, text="📶 Antenna", variable=self.comp_type_var,
                       value="antenna", command=self._on_type_changed).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_frame, text="⚙️ Passive Component (Filter, Splitter, etc.)", variable=self.comp_type_var,
                       value="passive", command=self._on_type_changed).pack(anchor=tk.W, pady=2)

        # Scrollable form frame
        form_container = ttk.Frame(main_frame)
        form_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(form_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_container, orient="vertical", command=canvas.yview)
        self.form_frame = ttk.Frame(canvas)

        self.form_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Initialize form fields
        self.fields = {}
        self._create_form_fields()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(button_frame, text="Create Component", command=self._create_component,
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _on_type_changed(self):
        """Handle component type change"""
        # Clear and recreate form
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.fields.clear()
        self._create_form_fields()

    def _create_form_fields(self):
        """Create form fields based on component type"""
        comp_type = self.comp_type_var.get()

        # Common fields
        self._add_field("Model / Name", "model", "e.g., LMR-400, TX-500, Jampro JSCP")
        self._add_field("Description", "description", "Brief description", multiline=True)

        if comp_type == "transmitter":
            self._add_field("Power Output (Watts)", "power_output_watts", "300")
            self._add_field("Frequency Range Min (MHz)", "freq_min", "87.5")
            self._add_field("Frequency Range Max (MHz)", "freq_max", "108")
            self._add_field("Efficiency (%)", "efficiency_percent", "65")
            self._add_field("Manufacturer", "manufacturer", "")
            self._add_field("Part Number", "part_number", "")

        elif comp_type == "cable":
            self._add_field("Cable Type", "cable_type", "e.g., LMR-400, Heliax 7/8\"")
            self._add_field(f"Loss @ {self.frequency_mhz} MHz (dB/100ft)", "loss_per_100ft", "3.9")
            self._add_field("Impedance (Ohms)", "impedance_ohms", "50")
            self._add_field("Velocity Factor", "velocity_factor", "0.85")
            self._add_field("Max Power Rating (Watts)", "max_power_watts", "5000")
            self._add_field("Manufacturer", "manufacturer", "")

        elif comp_type == "antenna":
            self._add_field("Gain (dBi)", "gain_dbi", "0")
            self._add_field("Pattern Type", "pattern", "e.g., Omnidirectional, Directional")
            self._add_field("Frequency Range Min (MHz)", "freq_min", "87.5")
            self._add_field("Frequency Range Max (MHz)", "freq_max", "108")
            self._add_field("VSWR", "vswr", "1.5")
            self._add_field("Power Rating (Watts)", "power_rating_watts", "5000")
            self._add_field("Manufacturer", "manufacturer", "")
            self._add_field("Part Number", "part_number", "")

        elif comp_type == "passive":
            self._add_field("Component Type", "passive_type", "e.g., Filter, Splitter, Combiner")
            self._add_field("Insertion Loss (dB)", "insertion_loss_db", "0.5")
            self._add_field("Frequency Range Min (MHz)", "freq_min", "87.5")
            self._add_field("Frequency Range Max (MHz)", "freq_max", "108")
            self._add_field("Power Rating (Watts)", "power_rating_watts", "1000")
            self._add_field("Manufacturer", "manufacturer", "")
            self._add_field("Part Number", "part_number", "")

        # Optional fields
        self._add_field("Notes", "notes", "Additional notes or specifications", multiline=True)

    def _add_field(self, label, key, placeholder="", multiline=False):
        """Add a form field

        Args:
            label: Field label
            key: Dictionary key
            placeholder: Placeholder text
            multiline: If True, use Text widget instead of Entry
        """
        row_frame = ttk.Frame(self.form_frame)
        row_frame.pack(fill=tk.X, pady=5)

        ttk.Label(row_frame, text=label + ":", width=25, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))

        if multiline:
            text_widget = tk.Text(row_frame, height=3, width=40, wrap=tk.WORD)
            text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
            if placeholder:
                text_widget.insert('1.0', placeholder)
                text_widget.config(foreground='gray')

                def on_focus_in(event):
                    if text_widget.get('1.0', 'end-1c') == placeholder:
                        text_widget.delete('1.0', tk.END)
                        text_widget.config(foreground='black')

                def on_focus_out(event):
                    if not text_widget.get('1.0', 'end-1c'):
                        text_widget.insert('1.0', placeholder)
                        text_widget.config(foreground='gray')

                text_widget.bind('<FocusIn>', on_focus_in)
                text_widget.bind('<FocusOut>', on_focus_out)

            self.fields[key] = ('text', text_widget)
        else:
            var = tk.StringVar(value=placeholder if placeholder else "")
            entry = ttk.Entry(row_frame, textvariable=var, width=40)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.fields[key] = ('var', var)

    def _create_component(self):
        """Create component from form data"""
        comp_type = self.comp_type_var.get()

        # Collect field values
        component_data = {
            'component_type': comp_type,
            'source': 'Custom',
            'custom': True
        }

        # Get all field values
        for key, (field_type, widget) in self.fields.items():
            if field_type == 'text':
                value = widget.get('1.0', 'end-1c').strip()
                # Skip placeholder text
                if value and value != widget.tag_names():
                    component_data[key] = value
            else:  # var
                value = widget.get().strip()
                if value:
                    # Try to convert numeric fields
                    if key in ['power_output_watts', 'freq_min', 'freq_max', 'efficiency_percent',
                              'loss_per_100ft', 'impedance_ohms', 'velocity_factor', 'max_power_watts',
                              'gain_dbi', 'vswr', 'power_rating_watts', 'insertion_loss_db']:
                        try:
                            component_data[key] = float(value)
                        except ValueError:
                            messagebox.showerror("Invalid Input",
                                               f"'{key}' must be a number")
                            return
                    else:
                        component_data[key] = value

        # Validate required fields
        if 'model' not in component_data or not component_data['model']:
            messagebox.showerror("Missing Field", "Model/Name is required")
            return

        # Add frequency range if provided
        if 'freq_min' in component_data and 'freq_max' in component_data:
            component_data['frequency_range_mhz'] = [
                component_data['freq_min'],
                component_data['freq_max']
            ]

        # Calculate dBm/dBW for transmitters
        if comp_type == 'transmitter' and 'power_output_watts' in component_data:
            import math
            watts = component_data['power_output_watts']
            component_data['power_output_dbm'] = 10 * math.log10(watts * 1000)
            component_data['power_output_dbw'] = 10 * math.log10(watts)

        # Success message
        messagebox.showinfo("Component Created",
                          f"Component '{component_data['model']}' created successfully!")

        # Call callback
        if self.callback:
            self.callback(component_data)

        # Close dialog
        self.dialog.destroy()
