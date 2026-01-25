"""
Station Builder Dialog
Build RF transmission chain and calculate system gain/loss
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, List, Dict
from models.component_library import ComponentLibrary
from models.antenna_library import AntennaLibrary


class StationBuilderDialog:
    """Dialog for building station RF chain

    Features:
    - Hierarchical component browser (Vendor > Type > Model)
    - Right-click context menu on RF chain
    - AI import and manual add support
    """

    def __init__(self, parent, frequency_mhz: float, callback: Optional[Callable] = None,
                 initial_chain: Optional[List] = None, initial_antenna: Optional[str] = None,
                 initial_bearing: float = 0.0, initial_downtilt: float = 0.0):
        """Initialize station builder

        Args:
            parent: Parent window
            frequency_mhz: Operating frequency
            callback: Callback function(total_loss_db, total_gain_db, erp_change_db, rf_chain, antenna_id, antenna_bearing, antenna_downtilt)
            initial_chain: Optional initial RF chain to load
            initial_antenna: Optional initial antenna ID
            initial_bearing: Optional initial antenna bearing (degrees, 0=North, clockwise)
            initial_downtilt: Optional initial antenna downtilt (degrees, positive=down)
        """
        self.parent = parent
        self.frequency_mhz = frequency_mhz
        self.callback = callback
        self.component_library = ComponentLibrary()
        self.antenna_library = AntennaLibrary()

        # RF chain components and antenna
        self.rf_chain = initial_chain if initial_chain else []  # List of (component, length_ft) tuples
        self.selected_antenna_id = initial_antenna
        self.antenna_bearing = initial_bearing  # Antenna bearing in degrees (0=North, clockwise)
        self.antenna_downtilt = initial_downtilt  # Antenna downtilt in degrees (positive=down)
        self.search_results = []  # Initialize search results list

        self._create_dialog()
        self._update_chain_display()
        self._calculate_totals()

        # Initialize search results with all components
        self._search_components()

    def _create_dialog(self):
        """Create dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Station Builder")
        self.dialog.geometry("900x700")

        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top section: Add components with browse buttons
        add_frame = ttk.LabelFrame(main_frame, text="Add Component", padding=10)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        # Row of component type browse buttons
        ttk.Label(add_frame, text="Browse by Type:",
                 font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        btn_frame = ttk.Frame(add_frame)
        btn_frame.grid(row=0, column=1, columnspan=4, sticky=tk.W, padx=5, pady=5)

        ttk.Button(btn_frame, text="Cables",
                  command=lambda: self._browse_components('cable')).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Transmitters",
                  command=lambda: self._browse_components('transmitter')).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Amplifiers",
                  command=lambda: self._browse_components('amplifier')).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Filters",
                  command=lambda: self._browse_components('filter')).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Isolators",
                  command=lambda: self._browse_components('isolator')).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Other...",
                  command=self._browse_other_components).pack(side=tk.LEFT, padx=3)

        # Quick search row
        ttk.Separator(add_frame, orient='horizontal').grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=8)

        ttk.Label(add_frame, text="Quick Search:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._search_components())
        search_entry = ttk.Entry(add_frame, textvariable=self.search_var, width=40)
        search_entry.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Component type filter for quick search
        self.comp_type_var = tk.StringVar(value="all")
        comp_types = ['all'] + self.component_library.get_component_types()
        type_combo = ttk.Combobox(add_frame, textvariable=self.comp_type_var,
                                   values=comp_types, width=12, state='readonly')
        type_combo.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self._search_components())

        # Results list (compact)
        results_frame = ttk.Frame(add_frame)
        results_frame.grid(row=3, column=0, columnspan=5, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.results_listbox = tk.Listbox(results_frame, height=4, width=80,
                                          bg='#252526', fg='#cccccc',
                                          selectbackground='#0078d4',
                                          font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        self.results_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Add controls row
        controls_frame = ttk.Frame(add_frame)
        controls_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Label(controls_frame, text="Length (ft):").pack(side=tk.LEFT, padx=5)
        self.length_var = tk.StringVar(value="100")
        ttk.Entry(controls_frame, textvariable=self.length_var, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Button(controls_frame, text="Add to Chain",
                  command=self._add_to_chain).pack(side=tk.LEFT, padx=10)

        ttk.Button(controls_frame, text="Apply to Station",
                  command=self._apply_changes,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(controls_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15)

        # AI and Manual add buttons
        ttk.Button(controls_frame, text="AI Import...",
                  command=self._ai_search_component).pack(side=tk.LEFT, padx=3)
        ttk.Button(controls_frame, text="Upload PDF...",
                  command=self._upload_datasheet).pack(side=tk.LEFT, padx=3)
        ttk.Button(controls_frame, text="Add Manual...",
                  command=self._quick_add_component).pack(side=tk.LEFT, padx=3)

        # Hidden AI search var for compatibility
        self.ai_search_var = tk.StringVar()

        # Antenna selection section
        antenna_frame = ttk.LabelFrame(main_frame, text="Antenna Selection", padding=10)
        antenna_frame.pack(fill=tk.X, pady=(0, 10))

        # Browse button and current selection display
        ttk.Button(antenna_frame, text="Browse Antennas...",
                  command=self._browse_antennas).grid(row=0, column=0, sticky=tk.W, padx=5)

        # Current antenna label
        self.antenna_display_var = tk.StringVar(value="None selected")
        self._update_antenna_display()
        ttk.Label(antenna_frame, textvariable=self.antenna_display_var,
                 font=('Segoe UI', 10, 'bold')).grid(row=0, column=1, sticky=tk.W, padx=10)

        # Quick dropdown for changing (still available)
        antenna_list = ["None (Use ERP directly)"]
        self.antenna_ids = [None]
        for antenna_id, antenna_data in self.antenna_library.antennas.items():
            name = antenna_data.get('name', antenna_id)
            gain = antenna_data.get('gain', 0)
            antenna_list.append(f"{name} ({gain:+.1f} dBi)")
            self.antenna_ids.append(antenna_id)

        self.antenna_var = tk.StringVar()
        if self.selected_antenna_id and self.selected_antenna_id in self.antenna_ids:
            idx = self.antenna_ids.index(self.selected_antenna_id)
            self.antenna_var.set(antenna_list[idx])
        else:
            self.antenna_var.set(antenna_list[0])

        self.antenna_combo = ttk.Combobox(antenna_frame, textvariable=self.antenna_var,
                                          values=antenna_list, width=40, state='readonly')
        self.antenna_combo.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        self.antenna_combo.bind('<<ComboboxSelected>>', self._on_antenna_selected)

        # Second row: orientation controls
        orient_frame = ttk.Frame(antenna_frame)
        orient_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))

        ttk.Label(orient_frame, text="Bearing:").pack(side=tk.LEFT, padx=5)
        self.bearing_var = tk.StringVar(value=str(self.antenna_bearing))
        self.bearing_entry = ttk.Entry(orient_frame, textvariable=self.bearing_var, width=8)
        self.bearing_entry.pack(side=tk.LEFT, padx=5)
        self.bearing_entry.bind('<FocusOut>', self._on_bearing_changed)
        self.bearing_entry.bind('<Return>', self._on_bearing_changed)
        ttk.Label(orient_frame, text="° (0=N)", font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(orient_frame, text="Downtilt:").pack(side=tk.LEFT, padx=5)
        self.downtilt_var = tk.StringVar(value=str(self.antenna_downtilt))
        self.downtilt_entry = ttk.Entry(orient_frame, textvariable=self.downtilt_var, width=8)
        self.downtilt_entry.pack(side=tk.LEFT, padx=5)
        self.downtilt_entry.bind('<FocusOut>', self._on_downtilt_changed)
        self.downtilt_entry.bind('<Return>', self._on_downtilt_changed)
        ttk.Label(orient_frame, text="° (+down)", font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 15))

        # AI Import antenna button
        ttk.Button(orient_frame, text="AI Import Antenna...",
                  command=self._ai_import_antenna).pack(side=tk.LEFT, padx=15)

        antenna_frame.columnconfigure(2, weight=1)

        # Middle section: RF Chain display
        chain_frame = ttk.LabelFrame(main_frame, text="RF Chain (TX → Antenna)", padding=10)
        chain_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Chain tree view
        chain_tree_frame = ttk.Frame(chain_frame)
        chain_tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('component', 'type', 'length', 'loss', 'gain')
        self.chain_tree = ttk.Treeview(chain_tree_frame, columns=columns, show='tree headings', height=10)

        self.chain_tree.heading('component', text='Component')
        self.chain_tree.heading('type', text='Type')
        self.chain_tree.heading('length', text='Length (ft)')
        self.chain_tree.heading('loss', text='Loss (dB)')
        self.chain_tree.heading('gain', text='Gain (dB)')

        self.chain_tree.column('#0', width=50)
        self.chain_tree.column('component', width=250)
        self.chain_tree.column('type', width=100)
        self.chain_tree.column('length', width=80)
        self.chain_tree.column('loss', width=80)
        self.chain_tree.column('gain', width=80)

        chain_scrollbar = ttk.Scrollbar(chain_tree_frame, orient=tk.VERTICAL, command=self.chain_tree.yview)
        self.chain_tree.config(yscrollcommand=chain_scrollbar.set)
        self.chain_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chain_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create context menu for RF chain
        self.chain_context_menu = tk.Menu(self.dialog, tearoff=0)
        self.chain_context_menu.add_command(label="Move Up", command=self._move_up)
        self.chain_context_menu.add_command(label="Move Down", command=self._move_down)
        self.chain_context_menu.add_separator()
        self.chain_context_menu.add_command(label="Edit...", command=self._edit_component)
        self.chain_context_menu.add_command(label="Remove", command=self._remove_component)
        self.chain_context_menu.add_separator()
        self.chain_context_menu.add_command(label="Clear All", command=self._clear_chain)

        # Bind right-click to show context menu
        self.chain_tree.bind('<Button-3>', self._show_chain_context_menu)

        # Chain controls (simplified - main actions in context menu)
        chain_controls = ttk.Frame(chain_frame)
        chain_controls.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(chain_controls, text="Move Up", command=self._move_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Move Down", command=self._move_down).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Edit", command=self._edit_component).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Remove", command=self._remove_component).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Clear All", command=self._clear_chain).pack(side=tk.LEFT, padx=5)

        ttk.Label(chain_controls, text="(Right-click for menu)",
                 font=('Segoe UI', 8, 'italic')).pack(side=tk.RIGHT, padx=10)

        # Bottom section: Totals
        totals_frame = ttk.LabelFrame(main_frame, text="System Totals", padding=10)
        totals_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(totals_frame, text="Total Loss:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.total_loss_var = tk.StringVar(value="0.00 dB")
        ttk.Label(totals_frame, textvariable=self.total_loss_var, font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(totals_frame, text="Total Gain:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.total_gain_var = tk.StringVar(value="0.00 dB")
        ttk.Label(totals_frame, textvariable=self.total_gain_var, font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Label(totals_frame, text="Net Change:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.net_change_var = tk.StringVar(value="0.00 dB")
        self.net_label = ttk.Label(totals_frame, textvariable=self.net_change_var, font=('TkDefaultFont', 10, 'bold'))
        self.net_label.grid(row=0, column=5, sticky=tk.W, padx=5)

        # Buttons (Apply moved to Add Component section)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _browse_components(self, component_type: str):
        """Open component browser for a specific type"""
        from gui.component_browser import ComponentBrowserDialog

        def on_component_selected(component, length_ft):
            """Handle component selection from browser"""
            comp_type = component.get('component_type', component_type)

            # Handle transmitters specially (need power input)
            if comp_type == 'transmitter':
                self._add_transmitter_with_power(component)
            else:
                self.rf_chain.append((component, length_ft))
                self._update_chain_display()
                self._calculate_totals()

        ComponentBrowserDialog(
            self.dialog,
            component_type,
            self.frequency_mhz,
            on_select=on_component_selected,
            on_ai_import=self._ai_search_component,
            on_manual_add=self._quick_add_component
        )

    def _browse_other_components(self):
        """Show dialog to select other component types"""
        # Get all available types
        all_types = self.component_library.get_component_types()
        common_types = ['cable', 'transmitter', 'amplifier', 'filter', 'isolator']
        other_types = [t for t in all_types if t not in common_types]

        if not other_types:
            messagebox.showinfo("No Other Types", "No additional component types available")
            return

        # Create selection dialog
        select_dialog = tk.Toplevel(self.dialog)
        select_dialog.title("Select Component Type")
        select_dialog.geometry("300x200")
        select_dialog.transient(self.dialog)

        ttk.Label(select_dialog, text="Select component type:",
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)

        type_var = tk.StringVar()
        type_listbox = tk.Listbox(select_dialog, height=6,
                                  bg='#252526', fg='#cccccc',
                                  selectbackground='#0078d4')
        for t in other_types:
            type_listbox.insert(tk.END, t.replace('_', ' ').title())
        type_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def on_select():
            sel = type_listbox.curselection()
            if sel:
                selected_type = other_types[sel[0]]
                select_dialog.destroy()
                self._browse_components(selected_type)

        ttk.Button(select_dialog, text="Browse",
                  command=on_select, style='Accent.TButton').pack(pady=10)

    def _browse_antennas(self):
        """Open antenna browser dialog"""
        from gui.component_browser import ComponentBrowserDialog

        def on_antenna_selected(antenna_data, _):
            """Handle antenna selection from browser"""
            antenna_id = antenna_data.get('antenna_id')
            if antenna_id and antenna_id in self.antenna_ids:
                idx = self.antenna_ids.index(antenna_id)
                self.antenna_combo.current(idx)
                self.selected_antenna_id = antenna_id

                # Update bearing/downtilt if provided
                if 'bearing' in antenna_data:
                    self.antenna_bearing = antenna_data['bearing']
                    self.bearing_var.set(f"{self.antenna_bearing:.1f}")
                if 'downtilt' in antenna_data:
                    self.antenna_downtilt = antenna_data['downtilt']
                    self.downtilt_var.set(f"{self.antenna_downtilt:.1f}")

                self._update_antenna_display()
                self._update_chain_display()
                self._calculate_totals()

        ComponentBrowserDialog(
            self.dialog,
            'antenna',
            self.frequency_mhz,
            on_select=on_antenna_selected,
            on_ai_import=self._ai_import_antenna,
            on_manual_add=self._quick_add_component
        )

    def _update_antenna_display(self):
        """Update the antenna display label"""
        if not hasattr(self, 'antenna_display_var'):
            return

        if self.selected_antenna_id:
            antenna_data = self.antenna_library.antennas.get(self.selected_antenna_id, {})
            name = antenna_data.get('name', self.selected_antenna_id)
            gain = antenna_data.get('gain', 0)
            self.antenna_display_var.set(f"{name} ({gain:+.1f} dBi)")
        else:
            self.antenna_display_var.set("None selected")

    def _ai_import_antenna(self):
        """Open AI antenna import dialog"""
        # Use existing antenna import functionality from main window
        try:
            from gui.dialogs import AntennaImportDialog

            def on_antenna_imported(antenna_id):
                """Callback when antenna is imported"""
                self._refresh_antenna_list(antenna_id)

            AntennaImportDialog(self.dialog, on_antenna_imported)
        except ImportError:
            messagebox.showerror("Error", "Antenna import dialog not available")

    def _add_transmitter_with_power(self, component):
        """Add transmitter with power input dialog"""
        max_power = component.get('power_output_watts', 1000)

        power_dialog = tk.Toplevel(self.dialog)
        power_dialog.title("Set Transmitter Power")
        power_dialog.geometry("350x150")
        power_dialog.transient(self.dialog)
        power_dialog.grab_set()

        ttk.Label(power_dialog, text=f"Transmitter: {component.get('model', 'Unknown')}",
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)
        ttk.Label(power_dialog, text=f"Max Rated Power: {max_power} W").pack(pady=5)

        power_frame = ttk.Frame(power_dialog)
        power_frame.pack(pady=10)

        ttk.Label(power_frame, text="Transmit Power (W):").pack(side=tk.LEFT, padx=5)
        power_var = tk.StringVar(value=str(max_power))
        power_entry = ttk.Entry(power_frame, textvariable=power_var, width=10)
        power_entry.pack(side=tk.LEFT, padx=5)

        def on_ok():
            try:
                transmit_power = float(power_var.get())
                if transmit_power <= 0:
                    raise ValueError("Must be positive")
                if transmit_power > max_power * 1.1:
                    if not messagebox.askyesno("Power Warning",
                                             f"Transmit power ({transmit_power}W) exceeds rated maximum ({max_power}W).\nContinue anyway?"):
                        return
                component_copy = component.copy()
                component_copy['transmit_power_watts'] = transmit_power
                self.rf_chain.append((component_copy, 0))
                power_dialog.destroy()
                self._update_chain_display()
                self._calculate_totals()
            except ValueError:
                messagebox.showerror("Invalid Power", "Please enter a valid positive number")

        button_frame = ttk.Frame(power_dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=power_dialog.destroy).pack(side=tk.LEFT, padx=5)

        power_entry.focus()
        power_dialog.bind('<Return>', lambda e: on_ok())

    def _show_chain_context_menu(self, event):
        """Show context menu for RF chain treeview"""
        # Select item under cursor
        item = self.chain_tree.identify_row(event.y)
        if item:
            self.chain_tree.selection_set(item)

        # Show context menu
        try:
            self.chain_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.chain_context_menu.grab_release()

    def _search_components(self):
        """Search for components based on filters"""
        query = self.search_var.get()
        comp_type = self.comp_type_var.get()

        if comp_type == 'all':
            comp_type = None

        results = self.component_library.search_component(query, comp_type)

        # Update listbox
        self.results_listbox.delete(0, tk.END)
        self.search_results = results

        for component in results:
            model = component.get('model', 'Unknown')
            desc = component.get('description', '')
            source = component.get('source', '')
            display = f"{model} - {desc} ({source})"
            self.results_listbox.insert(tk.END, display)

    def _add_to_chain(self):
        """Add selected component to RF chain"""
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a component to add")
            return

        component = self.search_results[selection[0]]

        # Get length for cables
        length_ft = 0
        if component.get('component_type') == 'cable':
            try:
                length_ft = float(self.length_var.get())
            except ValueError:
                messagebox.showerror("Invalid Length", "Please enter a valid length in feet")
                return

        # For transmitters, get actual transmit power from user
        if component.get('component_type') == 'transmitter':
            max_power = component.get('power_output_watts', 1000)
            power_dialog = tk.Toplevel(self.dialog)
            power_dialog.title("Set Transmitter Power")
            power_dialog.geometry("350x150")
            power_dialog.transient(self.dialog)
            power_dialog.grab_set()

            ttk.Label(power_dialog, text=f"Transmitter: {component.get('model', 'Unknown')}",
                     font=('TkDefaultFont', 10, 'bold')).pack(pady=10)

            ttk.Label(power_dialog, text=f"Max Rated Power: {max_power} W").pack(pady=5)

            # Power input
            power_frame = ttk.Frame(power_dialog)
            power_frame.pack(pady=10)

            ttk.Label(power_frame, text="Transmit Power (W):").pack(side=tk.LEFT, padx=5)
            power_var = tk.StringVar(value=str(max_power))
            power_entry = ttk.Entry(power_frame, textvariable=power_var, width=10)
            power_entry.pack(side=tk.LEFT, padx=5)

            def on_ok():
                try:
                    transmit_power = float(power_var.get())
                    if transmit_power <= 0:
                        raise ValueError("Must be positive")
                    if transmit_power > max_power * 1.1:  # Allow 10% over max for flexibility
                        if not messagebox.askyesno("Power Warning",
                                                 f"Transmit power ({transmit_power}W) exceeds rated maximum ({max_power}W).\nContinue anyway?"):
                            return
                    # Store the user-set power in the component
                    component_copy = component.copy()
                    component_copy['transmit_power_watts'] = transmit_power
                    self.rf_chain.append((component_copy, length_ft))
                    power_dialog.destroy()
                    self._update_chain_display()
                    self._calculate_totals()
                except ValueError:
                    messagebox.showerror("Invalid Power", "Please enter a valid positive number for transmit power")

            def on_cancel():
                power_dialog.destroy()

            button_frame = ttk.Frame(power_dialog)
            button_frame.pack(pady=10)
            ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)

            power_entry.focus()
            power_dialog.bind('<Return>', lambda e: on_ok())
            power_dialog.bind('<Escape>', lambda e: on_cancel())
            return

        self.rf_chain.append((component, length_ft))
        self._update_chain_display()
        self._calculate_totals()

    def _remove_component(self):
        """Remove selected component from chain"""
        selection = self.chain_tree.selection()
        if not selection:
            return

        # Get index from item ID
        item_id = selection[0]
        index = int(item_id.replace('item_', ''))

        del self.rf_chain[index]
        self._update_chain_display()
        self._calculate_totals()

    def _move_up(self):
        """Move selected component up in chain"""
        selection = self.chain_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        index = int(item_id.replace('item_', ''))

        if index > 0:
            self.rf_chain[index], self.rf_chain[index - 1] = self.rf_chain[index - 1], self.rf_chain[index]
            self._update_chain_display()
            self._calculate_totals()

    def _move_down(self):
        """Move selected component down in chain"""
        selection = self.chain_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        index = int(item_id.replace('item_', ''))

        if index < len(self.rf_chain) - 1:
            self.rf_chain[index], self.rf_chain[index + 1] = self.rf_chain[index + 1], self.rf_chain[index]
            self._update_chain_display()
            self._calculate_totals()

    def _clear_chain(self):
        """Clear all components from chain"""
        if messagebox.askyesno("Clear Chain", "Remove all components from RF chain?"):
            self.rf_chain = []
            self._update_chain_display()
            self._calculate_totals()

    def _edit_component(self):
        """Edit selected component in chain"""
        selection = self.chain_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a component to edit")
            return

        item_id = selection[0]
        index = int(item_id.replace('item_', ''))
        component, current_length = self.rf_chain[index]

        # Create edit dialog
        edit_dialog = tk.Toplevel(self.dialog)
        edit_dialog.title("Edit Component")
        edit_dialog.geometry("400x200")

        ttk.Label(edit_dialog, text=f"Component: {component.get('model', 'Unknown')}",
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=10)

        # Allow editing length for cables or power for transmitters
        comp_type = component.get('component_type')
        if comp_type == 'cable':
            ttk.Label(edit_dialog, text="Length (ft):").pack(pady=5)
            length_var = tk.StringVar(value=str(current_length))
            length_entry = ttk.Entry(edit_dialog, textvariable=length_var, width=20)
            length_entry.pack(pady=5)

            def save_changes():
                try:
                    new_length = float(length_var.get())
                    self.rf_chain[index] = (component, new_length)
                    self._update_chain_display()
                    self._calculate_totals()
                    edit_dialog.destroy()
                except ValueError:
                    messagebox.showerror("Invalid Length", "Please enter a valid length in feet")

            ttk.Button(edit_dialog, text="Save", command=save_changes).pack(pady=10)
            ttk.Button(edit_dialog, text="Cancel", command=edit_dialog.destroy).pack()

        elif comp_type == 'transmitter':
            max_power = component.get('power_output_watts', 1000)
            current_power = component.get('transmit_power_watts', max_power)

            ttk.Label(edit_dialog, text=f"Max Rated Power: {max_power} W").pack(pady=5)
            ttk.Label(edit_dialog, text="Transmit Power (W):").pack(pady=5)

            power_var = tk.StringVar(value=str(current_power))
            power_entry = ttk.Entry(edit_dialog, textvariable=power_var, width=20)
            power_entry.pack(pady=5)

            def save_changes():
                try:
                    new_power = float(power_var.get())
                    if new_power <= 0:
                        raise ValueError("Must be positive")
                    if new_power > max_power * 1.1:  # Allow 10% over max
                        if not messagebox.askyesno("Power Warning",
                                                 f"Transmit power ({new_power}W) exceeds rated maximum ({max_power}W).\nContinue anyway?"):
                            return
                    # Update the component with new power
                    component_copy = component.copy()
                    component_copy['transmit_power_watts'] = new_power
                    self.rf_chain[index] = (component_copy, current_length)
                    self._update_chain_display()
                    self._calculate_totals()
                    edit_dialog.destroy()
                except ValueError:
                    messagebox.showerror("Invalid Power", "Please enter a valid positive number for transmit power")

            ttk.Button(edit_dialog, text="Save", command=save_changes).pack(pady=10)
            ttk.Button(edit_dialog, text="Cancel", command=edit_dialog.destroy).pack()

        else:
            ttk.Label(edit_dialog, text="This component type cannot be modified.\nYou can remove and re-add it if needed.").pack(pady=20)
            ttk.Button(edit_dialog, text="Close", command=edit_dialog.destroy).pack(pady=10)

    def _on_antenna_selected(self, event=None):
        """Handle antenna selection change"""
        selected_text = self.antenna_var.get()
        selected_index = 0

        # Find the index of selected antenna
        for i, antenna_id in enumerate(self.antenna_ids):
            if self.antenna_var.get().startswith(self.antenna_library.antennas.get(antenna_id, {}).get('name', '')) if antenna_id else selected_text.startswith("None"):
                selected_index = i
                break

        self.selected_antenna_id = self.antenna_ids[selected_index]

        # Update display to show antenna in chain
        self._update_chain_display()
        self._calculate_totals()

    def _on_bearing_changed(self, event=None):
        """Handle antenna bearing change"""
        try:
            bearing = float(self.bearing_var.get())
            # Normalize to 0-360
            bearing = bearing % 360
            self.antenna_bearing = bearing
            self.bearing_var.set(f"{bearing:.1f}")
        except ValueError:
            # Reset to current value if invalid
            self.bearing_var.set(f"{self.antenna_bearing:.1f}")

    def _on_downtilt_changed(self, event=None):
        """Handle antenna downtilt change"""
        try:
            downtilt = float(self.downtilt_var.get())
            # Clamp to reasonable range (-90 to 90)
            downtilt = max(-90, min(90, downtilt))
            self.antenna_downtilt = downtilt
            self.downtilt_var.set(f"{downtilt:.1f}")
        except ValueError:
            # Reset to current value if invalid
            self.downtilt_var.set(f"{self.antenna_downtilt:.1f}")

    def _ai_search_component(self):
        """Search for component using Ollama AI"""
        query = self.ai_search_var.get().strip()
        if not query:
            messagebox.showwarning("No Query", "Please enter a component name or model number")
            return

        # Show progress dialog
        progress_dialog = tk.Toplevel(self.dialog)
        progress_dialog.title("AI Search")
        progress_dialog.geometry("400x150")
        progress_dialog.transient(self.dialog)
        progress_dialog.grab_set()

        ttk.Label(progress_dialog, text="Searching with Ollama AI...",
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=20)
        ttk.Label(progress_dialog, text=f"Query: {query}").pack(pady=5)

        progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()

        status_label = ttk.Label(progress_dialog, text="Please wait...")
        status_label.pack(pady=5)

        def search_thread():
            try:
                component = self.component_library.ollama_search_component(query, self.frequency_mhz)
                progress_dialog.after(0, lambda: on_search_complete(component))
            except Exception as e:
                error_msg = str(e)
                progress_dialog.after(0, lambda: on_search_error(error_msg))

        def on_search_complete(component):
            progress_bar.stop()
            progress_dialog.destroy()

            if component:
                # Add to search results
                self.search_results.append(component)
                model = component.get('model', 'Unknown')
                desc = component.get('description', '')
                source = 'Ollama AI'
                display = f"{model} - {desc} ({source})"
                self.results_listbox.insert(tk.END, display)
                self.results_listbox.selection_clear(0, tk.END)
                self.results_listbox.selection_set(tk.END)
                self.results_listbox.see(tk.END)
                messagebox.showinfo("Success", f"Found component: {model}")
            else:
                messagebox.showwarning("Not Found", f"Could not find component: {query}")

        def on_search_error(error_msg):
            progress_bar.stop()
            progress_dialog.destroy()
            messagebox.showerror("AI Search Error", f"Error: {error_msg}")

        import threading
        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()

    def _upload_datasheet(self):
        """Upload and process datasheet with Ollama AI"""
        from tkinter import filedialog

        # Select PDF file
        file_path = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select Component Datasheet",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        # Show progress dialog
        progress_dialog = tk.Toplevel(self.dialog)
        progress_dialog.title("Processing Datasheet")
        progress_dialog.geometry("500x200")
        progress_dialog.transient(self.dialog)
        progress_dialog.grab_set()

        ttk.Label(progress_dialog, text="Processing datasheet with Ollama AI...",
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=20)
        ttk.Label(progress_dialog, text=f"File: {file_path.split('/')[-1]}").pack(pady=5)

        progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()

        status_label = ttk.Label(progress_dialog, text="Extracting specifications...")
        status_label.pack(pady=5)

        def process_thread():
            try:
                # Extract text from PDF
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()

                print(f"Extracted {len(text)} characters from PDF")
                print(f"First 500 chars: {text[:500]}")

                # Use Ollama to extract component specs
                component = self._extract_specs_with_ollama(text)
                progress_dialog.after(0, lambda: on_process_complete(component))
            except ImportError:
                progress_dialog.after(0, lambda: on_process_error(
                    "PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF"))
            except Exception as e:
                progress_dialog.after(0, lambda: on_process_error(str(e)))

        def on_process_complete(component):
            progress_bar.stop()
            progress_dialog.destroy()

            if component:
                # Show review dialog
                self._show_component_review_dialog(component)
            else:
                messagebox.showwarning("Extraction Failed", "Could not extract component specifications from datasheet")

        def on_process_error(error_msg):
            progress_bar.stop()
            progress_dialog.destroy()
            messagebox.showerror("Datasheet Processing Error", f"Error: {error_msg}")

        import threading
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()

    def _extract_specs_with_ollama(self, datasheet_text: str) -> dict:
        """Extract component specifications from datasheet text using Ollama"""
        import requests
        import json

        # Check if we have any text
        if not datasheet_text or len(datasheet_text.strip()) < 50:
            raise Exception("PDF appears empty or has insufficient text content")

        prompt = f"""You are an RF component specification extraction expert. Extract detailed specifications from this datasheet.

## EXAMPLE 1 - Cable:
INPUT: "Times Microwave LMR-400, 50 ohm, Velocity 85%, OD 0.405in, Loss: 0.7dB/100ft@150MHz, 1.3dB@450MHz, 1.9dB@900MHz, Power: 1800W@150MHz"
OUTPUT: {{"component_type":"cable","manufacturer":"Times Microwave Systems","model":"LMR-400","impedance_ohms":50,"velocity_factor":0.85,"outer_diameter_inches":0.405,"loss_db_per_100ft":{{"150":0.7,"450":1.3,"900":1.9}},"power_rating_watts":{{"150_mhz":1800}}}}

## EXAMPLE 2 - Antenna:
INPUT: "Jampro JCPV-4, FM Broadcast 88-108MHz, Gain 6dBi (4x dipole), Circular polarization, VSWR 1.08:1, 60kW, 1-5/8 EIA"
OUTPUT: {{"component_type":"antenna","manufacturer":"Jampro Antennas","model":"JCPV-4","gain_dbi":6.0,"frequency_range_mhz":[88,108],"polarization":"circular","vswr":1.08,"power_rating_watts":60000,"connector_type":"EIA 1-5/8\\" flange"}}

## EXAMPLE 3 - Lightning Arrestor:
INPUT: "PolyPhaser IS-B50LN-C0, Bulkhead N-F to N-F, 0.2dB loss, DC-1GHz, 5kV, DC Pass"
OUTPUT: {{"component_type":"lightning_arrestor","manufacturer":"PolyPhaser","model":"IS-B50LN-C0","insertion_loss_db":0.2,"frequency_range_mhz":[0,1000],"connector_type":"N-Female both ends","voltage_rating_kv":5,"dc_pass":true}}

## EXAMPLE 4 - Transmitter:
INPUT: "BW Broadcast TX1000, 1kW FM 87.5-108MHz, 75% efficiency, 230VAC 1800W, Harmonics -60dBc"
OUTPUT: {{"component_type":"transmitter","manufacturer":"BW Broadcast","model":"TX1000","power_output_watts":1000,"frequency_range_mhz":[87.5,108],"efficiency_percent":75,"mains_voltage":"230VAC","power_consumption_watts":1800,"harmonic_suppression_dbc":-60}}

## NOW EXTRACT FROM THIS DATASHEET:
{datasheet_text[:8000]}

RULES:
1. Return ONLY valid JSON - no markdown, no explanation
2. Use exact values from the datasheet
3. For gain: dBi = dBd + 2.15
4. For cables: include loss_db_per_100ft at multiple frequencies
5. If insufficient data, return: {{"error": "Insufficient data"}}
"""

        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'rf-component-extractor',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=120
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API returned status {response.status_code}")

            result = response.json()
            response_text = result.get('response', '').strip()

            if not response_text:
                raise Exception("Ollama returned empty response")

            # Parse JSON response (handle markdown code blocks)
            import re
            try:
                # Try to extract JSON from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    json_str = response_text.strip()
                component_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse Ollama JSON response: {str(e)}\nResponse preview: {response_text[:200]}")

            # Check if Ollama reported an error
            if 'error' in component_data:
                raise Exception(f"Ollama could not extract specs: {component_data['error']}")

            # Normalize field names (handle 'type' vs 'component_type')
            if 'type' in component_data and 'component_type' not in component_data:
                component_data['component_type'] = component_data.pop('type')

            # Validate required fields
            if 'component_type' not in component_data:
                raise Exception("Ollama response missing required field (component_type)")

            return component_data

        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Is Ollama running? (ollama serve)")
        except requests.exceptions.Timeout:
            raise Exception("Ollama request timed out (60s). Model may still be loading.")
        except Exception as e:
            # Re-raise with context if not already a custom exception
            if "Ollama" in str(e) or "PDF" in str(e):
                raise
            else:
                raise Exception(f"Ollama extraction failed: {str(e)}")

    def _show_component_review_dialog(self, component: dict):
        """Show dialog to review and edit extracted component data"""
        review_dialog = tk.Toplevel(self.dialog)
        review_dialog.title("Review Extracted Component")
        review_dialog.geometry("600x500")
        review_dialog.transient(self.dialog)

        # Header
        ttk.Label(review_dialog, text="Review Component Specifications",
                 font=('TkDefaultFont', 12, 'bold')).pack(pady=10)
        ttk.Label(review_dialog, text="Verify the extracted data and edit if needed",
                 font=('TkDefaultFont', 9)).pack(pady=5)

        # Scrollable frame for specs
        canvas = tk.Canvas(review_dialog)
        scrollbar = ttk.Scrollbar(review_dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Display editable fields
        fields = {}
        row = 0
        for key, value in component.items():
            if isinstance(value, (str, int, float)):
                ttk.Label(scrollable_frame, text=f"{key}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                var = tk.StringVar(value=str(value))
                entry = ttk.Entry(scrollable_frame, textvariable=var, width=40)
                entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
                fields[key] = var
                row += 1

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        button_frame = ttk.Frame(review_dialog)
        button_frame.pack(fill=tk.X, pady=10)

        def save_component():
            # Update component with edited values
            for key, var in fields.items():
                try:
                    # Try to convert to appropriate type
                    value = var.get()
                    if key in ['gain_dbi', 'insertion_loss_db', 'velocity_factor']:
                        component[key] = float(value)
                    elif key in ['impedance_ohms', 'power_rating_watts']:
                        component[key] = int(value)
                    else:
                        component[key] = value
                except:
                    component[key] = var.get()

            # Add to cache
            self.component_library.add_to_cache(component)

            # Add to search results
            self.search_results.append(component)
            model = component.get('model', 'Unknown')
            desc = component.get('description', '')
            display = f"{model} - {desc} (Imported)"
            self.results_listbox.insert(tk.END, display)
            self.results_listbox.selection_clear(0, tk.END)
            self.results_listbox.selection_set(tk.END)

            review_dialog.destroy()
            messagebox.showinfo("Success", f"Component saved: {model}")

        ttk.Button(button_frame, text="Save to Library", command=save_component).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=review_dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _update_chain_display(self):
        """Update chain tree view"""
        # Clear existing
        for item in self.chain_tree.get_children():
            self.chain_tree.delete(item)

        # Add components
        for idx, (component, length_ft) in enumerate(self.rf_chain):
            model = component.get('model', 'Unknown')
            comp_type = component.get('component_type', 'unknown')

            # Calculate loss/gain for this component
            loss_db = 0
            gain_db = 0

            if comp_type == 'cable':
                loss_db = self.component_library.interpolate_cable_loss(component, self.frequency_mhz, length_ft)
            elif 'insertion_loss_db' in component:
                loss_db = component['insertion_loss_db']
            elif 'gain_dbi' in component:
                gain_db = component['gain_dbi']

            length_str = f"{length_ft:.1f}" if length_ft > 0 else "-"
            loss_str = f"{loss_db:.2f}" if loss_db > 0 else "-"
            gain_str = f"{gain_db:.2f}" if gain_db > 0 else "-"

            self.chain_tree.insert('', tk.END, iid=f'item_{idx}',
                                   text=f"{idx + 1}",
                                   values=(model, comp_type, length_str, loss_str, gain_str))

        # Add antenna at the end if selected
        if self.selected_antenna_id:
            antenna_data = self.antenna_library.antennas.get(self.selected_antenna_id)
            if antenna_data:
                antenna_name = antenna_data.get('name', 'Unknown')
                antenna_gain = antenna_data.get('gain', 0)

                # Insert antenna as the last item
                antenna_idx = len(self.rf_chain)
                self.chain_tree.insert('', tk.END, iid=f'antenna_item',
                                       text=f"{antenna_idx + 1}",
                                       values=(antenna_name, 'antenna', '-', '-', f"{antenna_gain:.2f}"),
                                       tags=('antenna',))

                # Make antenna item visually distinct
                self.chain_tree.tag_configure('antenna', background='#e8f4f8')

    def _calculate_totals(self):
        """Calculate total loss and gain"""
        total_loss = 0
        total_gain = 0

        for component, length_ft in self.rf_chain:
            comp_type = component.get('component_type', 'unknown')

            if comp_type == 'cable':
                loss = self.component_library.interpolate_cable_loss(component, self.frequency_mhz, length_ft)
                total_loss += loss
            elif 'insertion_loss_db' in component:
                total_loss += component['insertion_loss_db']
            elif 'gain_dbi' in component:
                total_gain += component['gain_dbi']

        # Add antenna gain if selected
        if self.selected_antenna_id:
            antenna_data = self.antenna_library.antennas.get(self.selected_antenna_id)
            if antenna_data:
                antenna_gain = antenna_data.get('gain', 0)
                total_gain += antenna_gain

        net_change = total_gain - total_loss

        self.total_loss_var.set(f"{total_loss:.2f} dB")
        self.total_gain_var.set(f"{total_gain:.2f} dB")
        self.net_change_var.set(f"{net_change:+.2f} dB")

        # Color code net change
        if net_change > 0:
            self.net_label.config(foreground='green')
        elif net_change < 0:
            self.net_label.config(foreground='red')
        else:
            self.net_label.config(foreground='black')

    def _refresh_antenna_list(self, select_antenna_id=None):
        """Refresh antenna dropdown list

        Args:
            select_antenna_id: Optional antenna ID to auto-select
        """
        # Reload antenna library
        self.antenna_library = AntennaLibrary()

        # Rebuild antenna list
        antenna_list = ["None (Use ERP directly)"]
        self.antenna_ids = [None]
        for antenna_id, antenna_data in self.antenna_library.antennas.items():
            name = antenna_data.get('name', antenna_id)
            gain = antenna_data.get('gain', 0)
            antenna_list.append(f"{name} ({gain:+.1f} dBi)")
            self.antenna_ids.append(antenna_id)

        # Update the combobox with new values
        self.antenna_combo['values'] = antenna_list

        # Auto-select the new antenna if ID provided
        if select_antenna_id and select_antenna_id in self.antenna_ids:
            idx = self.antenna_ids.index(select_antenna_id)
            self.antenna_combo.set(antenna_list[idx])
            self.selected_antenna_id = select_antenna_id
            self._update_chain_display()
            self._calculate_totals()
        else:
            # If antenna list changed, reselect current selection if still valid
            if self.selected_antenna_id and self.selected_antenna_id in self.antenna_ids:
                idx = self.antenna_ids.index(self.selected_antenna_id)
                self.antenna_combo.set(antenna_list[idx])

    def _quick_add_component(self):
        """Quick add component dialog - easy manual entry"""
        from gui.quick_add_component_dialog import QuickAddComponentDialog

        def on_component_created(component_data):
            """Callback when component is created"""
            comp_type = component_data.get('component_type')

            # Add to component library
            self.component_library.add_custom_component(component_data)

            # If antenna was created, refresh the antenna dropdown
            if comp_type == 'antenna':
                self._refresh_antenna_list(component_data.get('antenna_id'))

            # Refresh search results
            self._search_components()

            # Auto-select the new component
            comp_name = component_data.get('model', 'New Component')
            for i in range(self.results_listbox.size()):
                if comp_name in self.results_listbox.get(i):
                    self.results_listbox.selection_clear(0, tk.END)
                    self.results_listbox.selection_set(i)
                    self.results_listbox.see(i)
                    break

        dialog = QuickAddComponentDialog(self.dialog, self.frequency_mhz, on_component_created)

    def _apply_changes(self):
        """Apply changes to station"""
        total_loss = 0
        total_gain = 0

        for component, length_ft in self.rf_chain:
            comp_type = component.get('component_type', 'unknown')

            if comp_type == 'cable':
                loss = self.component_library.interpolate_cable_loss(component, self.frequency_mhz, length_ft)
                total_loss += loss
            elif 'insertion_loss_db' in component:
                total_loss += component['insertion_loss_db']
            elif 'gain_dbi' in component:
                total_gain += component['gain_dbi']

        if self.callback:
            # Pass RF chain, antenna, bearing, and downtilt for saving to project
            self.callback(total_loss, total_gain, total_gain - total_loss,
                         self.rf_chain, self.selected_antenna_id,
                         self.antenna_bearing, self.antenna_downtilt)

        messagebox.showinfo("Applied", f"Station updated with {total_gain - total_loss:+.2f} dB system change")
        self.dialog.destroy()
