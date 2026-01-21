"""
Station Builder Dialog
Build RF transmission chain and calculate system gain/loss
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, List, Dict
from models.component_library import ComponentLibrary


class StationBuilderDialog:
    """Dialog for building station RF chain"""

    def __init__(self, parent, frequency_mhz: float, callback: Optional[Callable] = None,
                 initial_chain: Optional[List] = None):
        """Initialize station builder

        Args:
            parent: Parent window
            frequency_mhz: Operating frequency
            callback: Callback function(total_loss_db, total_gain_db, erp_change_db, rf_chain)
            initial_chain: Optional initial RF chain to load
        """
        self.parent = parent
        self.frequency_mhz = frequency_mhz
        self.callback = callback
        self.component_library = ComponentLibrary()

        # RF chain components
        self.rf_chain = initial_chain if initial_chain else []  # List of (component, length_ft) tuples

        self._create_dialog()
        self._update_chain_display()
        self._calculate_totals()

    def _create_dialog(self):
        """Create dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Station Builder")
        self.dialog.geometry("900x700")

        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top section: Add components
        add_frame = ttk.LabelFrame(main_frame, text="Add Component", padding=10)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        # Component type selector
        ttk.Label(add_frame, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.comp_type_var = tk.StringVar(value="all")
        comp_types = ['all'] + self.component_library.get_component_types()
        type_combo = ttk.Combobox(add_frame, textvariable=self.comp_type_var,
                                   values=comp_types, width=15, state='readonly')
        type_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self._search_components())

        # Search box
        ttk.Label(add_frame, text="Search:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._search_components())
        search_entry = ttk.Entry(add_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=0, column=3, sticky=tk.W, padx=5)

        # Results list
        ttk.Label(add_frame, text="Results:").grid(row=1, column=0, sticky=tk.NW, padx=5, pady=5)

        results_frame = ttk.Frame(add_frame)
        results_frame.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.results_listbox = tk.Listbox(results_frame, height=5, width=70)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        self.results_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Length entry (for cables)
        ttk.Label(add_frame, text="Length (ft):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.length_var = tk.StringVar(value="100")
        length_entry = ttk.Entry(add_frame, textvariable=self.length_var, width=10)
        length_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Add button
        add_btn = ttk.Button(add_frame, text="Add to Chain", command=self._add_to_chain)
        add_btn.grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)

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

        # Chain controls
        chain_controls = ttk.Frame(chain_frame)
        chain_controls.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(chain_controls, text="Move Up", command=self._move_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Move Down", command=self._move_down).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Remove", command=self._remove_component).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Clear All", command=self._clear_chain).pack(side=tk.LEFT, padx=5)

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

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Apply to Station", command=self._apply_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

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
            # Pass RF chain for saving to project
            self.callback(total_loss, total_gain, total_gain - total_loss, self.rf_chain)

        messagebox.showinfo("Applied", f"Station updated with {total_gain - total_loss:+.2f} dB system change")
        self.dialog.destroy()
