"""
Component Browser Dialog
========================
Hierarchical component browser organized by Vendor > Type > Model
Supports cables, transmitters, antennas, and all other RF components.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, List
from models.component_library import ComponentLibrary
from models.antenna_library import AntennaLibrary


class ComponentBrowserDialog:
    """Hierarchical component browser dialog"""

    # Dark theme colors
    COLORS = {
        'bg': '#1e1e1e',
        'bg_medium': '#252526',
        'bg_light': '#2d2d30',
        'fg': '#cccccc',
        'fg_bright': '#ffffff',
        'accent': '#0078d4',
        'accent_light': '#4fc3f7',
        'border': '#3f3f46',
        'success': '#4caf50',
        'warning': '#ff9800'
    }

    def __init__(self, parent, component_type: str, frequency_mhz: float,
                 on_select: Callable, on_ai_import: Optional[Callable] = None,
                 on_manual_add: Optional[Callable] = None):
        """Initialize component browser

        Args:
            parent: Parent window
            component_type: Type of component to browse ('cable', 'transmitter', 'antenna', etc.)
            frequency_mhz: Operating frequency for loss calculations
            on_select: Callback when component selected - receives (component_dict, length_ft)
            on_ai_import: Optional callback to trigger AI import
            on_manual_add: Optional callback to trigger manual add
        """
        self.parent = parent
        self.component_type = component_type
        self.frequency_mhz = frequency_mhz
        self.on_select = on_select
        self.on_ai_import = on_ai_import
        self.on_manual_add = on_manual_add

        self.component_library = ComponentLibrary()
        self.antenna_library = AntennaLibrary()

        self.selected_component = None

        self._create_dialog()
        self._populate_tree()

    def _create_dialog(self):
        """Create the browser dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Browse {self.component_type.replace('_', ' ').title()}s")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)

        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text=f"Select {self.component_type.replace('_', ' ').title()}",
                 style='Title.TLabel').pack(side=tk.LEFT)

        # Search box
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._filter_tree())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Split pane: tree on left, details on right
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left side: Treeview
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=1)

        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set,
                                  selectmode='browse', show='tree')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind('<Double-1>', self._on_double_click)

        # Right side: Details panel
        details_frame = ttk.LabelFrame(paned, text="Component Details", padding=10)
        paned.add(details_frame, weight=1)

        # Details text with dark theme
        self.details_text = tk.Text(details_frame, width=40, height=20,
                                    wrap=tk.WORD, state='disabled',
                                    bg=self.COLORS['bg_medium'],
                                    fg=self.COLORS['fg'],
                                    font=('Consolas', 9),
                                    relief='flat', borderwidth=0)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # Length entry (for cables)
        if self.component_type == 'cable':
            length_frame = ttk.Frame(main_frame)
            length_frame.pack(fill=tk.X, pady=10)
            ttk.Label(length_frame, text="Cable Length (ft):").pack(side=tk.LEFT, padx=5)
            self.length_var = tk.StringVar(value="100")
            ttk.Entry(length_frame, textvariable=self.length_var, width=10).pack(side=tk.LEFT, padx=5)

            # Show calculated loss
            ttk.Label(length_frame, text="Estimated Loss:").pack(side=tk.LEFT, padx=(20, 5))
            self.loss_label = ttk.Label(length_frame, text="-- dB")
            self.loss_label.pack(side=tk.LEFT, padx=5)

            # Bind length change
            self.length_var.trace('w', lambda *args: self._update_loss_estimate())

        # Bottom button bar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Left side: AI and Manual add buttons
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)

        if self.on_ai_import:
            ttk.Button(left_buttons, text="AI Import...",
                      command=self._trigger_ai_import).pack(side=tk.LEFT, padx=5)

        if self.on_manual_add:
            ttk.Button(left_buttons, text="Add Manually...",
                      command=self._trigger_manual_add).pack(side=tk.LEFT, padx=5)

        # Right side: Select and Cancel
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)

        ttk.Button(right_buttons, text="Cancel",
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

        self.select_btn = ttk.Button(right_buttons, text="Select & Add to Chain",
                                     command=self._select_component,
                                     style='Accent.TButton')
        self.select_btn.pack(side=tk.RIGHT, padx=5)
        self.select_btn.state(['disabled'])

    def _populate_tree(self):
        """Populate the treeview with vendors and components"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Organize components by vendor, then by subtype
        vendors = {}  # vendor -> {subtype -> [components]}

        if self.component_type == 'antenna':
            # Handle antennas from antenna library
            for antenna_id, antenna_data in self.antenna_library.antennas.items():
                vendor = antenna_data.get('manufacturer', 'Unknown')
                subtype = antenna_data.get('type', 'General')

                if vendor not in vendors:
                    vendors[vendor] = {}
                if subtype not in vendors[vendor]:
                    vendors[vendor][subtype] = []

                vendors[vendor][subtype].append({
                    'id': antenna_id,
                    'name': antenna_data.get('name', antenna_id),
                    'gain': antenna_data.get('gain', 0),
                    'data': antenna_data,
                    'is_antenna': True
                })
        else:
            # Handle components from component library
            for catalog_id, catalog in self.component_library.catalogs.items():
                vendor = catalog.get('manufacturer', catalog_id)

                for component in catalog.get('components', []):
                    if component.get('component_type') != self.component_type:
                        continue

                    # Determine subtype based on component type
                    if self.component_type == 'cable':
                        # Group by cable size/model family
                        model = component.get('model', '')
                        if 'LMR' in model:
                            subtype = 'LMR Series'
                        elif 'HELIAX' in model or 'AVA' in model:
                            subtype = 'HELIAX'
                        else:
                            subtype = 'Other'
                    elif self.component_type == 'transmitter':
                        # Group by power range
                        power = component.get('power_output_watts', 0)
                        if power <= 100:
                            subtype = 'Low Power (<100W)'
                        elif power <= 1000:
                            subtype = 'Medium Power (100W-1kW)'
                        elif power <= 10000:
                            subtype = 'High Power (1kW-10kW)'
                        else:
                            subtype = 'Broadcast (>10kW)'
                    else:
                        subtype = component.get('description', 'General')[:30]

                    if vendor not in vendors:
                        vendors[vendor] = {}
                    if subtype not in vendors[vendor]:
                        vendors[vendor][subtype] = []

                    vendors[vendor][subtype].append({
                        'model': component.get('model', 'Unknown'),
                        'description': component.get('description', ''),
                        'data': component,
                        'is_antenna': False
                    })

            # Also add cached components
            for cached_id, component in self.component_library.cache.items():
                if not isinstance(component, dict):
                    continue
                if component.get('component_type') != self.component_type:
                    continue

                vendor = component.get('manufacturer', 'Custom/Cached')
                subtype = 'Imported'

                if vendor not in vendors:
                    vendors[vendor] = {}
                if subtype not in vendors[vendor]:
                    vendors[vendor][subtype] = []

                vendors[vendor][subtype].append({
                    'model': component.get('model', cached_id),
                    'description': component.get('description', ''),
                    'data': component,
                    'is_antenna': False
                })

        # Build tree structure
        for vendor in sorted(vendors.keys()):
            vendor_id = self.tree.insert('', tk.END, text=f"  {vendor}",
                                         tags=('vendor',), open=False)

            for subtype in sorted(vendors[vendor].keys()):
                subtype_id = self.tree.insert(vendor_id, tk.END, text=f"  {subtype}",
                                              tags=('subtype',), open=False)

                for comp in sorted(vendors[vendor][subtype],
                                   key=lambda x: x.get('model', x.get('name', ''))):
                    if comp.get('is_antenna'):
                        display = f"  {comp['name']} ({comp['gain']:+.1f} dBi)"
                        self.tree.insert(subtype_id, tk.END, text=display,
                                        tags=('component',),
                                        values=(comp['id'], 'antenna'))
                    else:
                        display = f"  {comp['model']}"
                        self.tree.insert(subtype_id, tk.END, text=display,
                                        tags=('component',),
                                        values=(comp['model'], self.component_type))

        # Store component lookup for quick access
        self._build_component_lookup()

        # Style tags
        self.tree.tag_configure('vendor', font=('Segoe UI', 10, 'bold'))
        self.tree.tag_configure('subtype', font=('Segoe UI', 9, 'italic'))
        self.tree.tag_configure('component', font=('Segoe UI', 9))

    def _build_component_lookup(self):
        """Build lookup dict for quick component access"""
        self.component_lookup = {}

        if self.component_type == 'antenna':
            for antenna_id, antenna_data in self.antenna_library.antennas.items():
                self.component_lookup[antenna_id] = {
                    **antenna_data,
                    'is_antenna': True,
                    'antenna_id': antenna_id
                }
        else:
            for catalog in self.component_library.catalogs.values():
                for component in catalog.get('components', []):
                    if component.get('component_type') == self.component_type:
                        model = component.get('model')
                        if model:
                            self.component_lookup[model] = {
                                **component,
                                'is_antenna': False
                            }

            for cached_id, component in self.component_library.cache.items():
                if isinstance(component, dict) and component.get('component_type') == self.component_type:
                    model = component.get('model', cached_id)
                    self.component_lookup[model] = {
                        **component,
                        'is_antenna': False
                    }

    def _filter_tree(self):
        """Filter tree based on search text"""
        query = self.search_var.get().lower().strip()

        if not query:
            # Show all items
            for vendor_item in self.tree.get_children():
                self.tree.item(vendor_item, open=False)
                for subtype_item in self.tree.get_children(vendor_item):
                    self.tree.item(subtype_item, open=False)
            return

        # Hide/show items based on search
        for vendor_item in self.tree.get_children():
            vendor_has_match = False

            for subtype_item in self.tree.get_children(vendor_item):
                subtype_has_match = False

                for comp_item in self.tree.get_children(subtype_item):
                    comp_text = self.tree.item(comp_item, 'text').lower()
                    values = self.tree.item(comp_item, 'values')

                    # Check if component matches
                    if values:
                        comp_id = values[0].lower() if values[0] else ''
                        matches = query in comp_text or query in comp_id
                    else:
                        matches = query in comp_text

                    if matches:
                        subtype_has_match = True
                        vendor_has_match = True

                # Expand subtype if has matches
                if subtype_has_match:
                    self.tree.item(subtype_item, open=True)

            # Expand vendor if has matches
            if vendor_has_match:
                self.tree.item(vendor_item, open=True)

    def _on_tree_select(self, event=None):
        """Handle tree selection"""
        selection = self.tree.selection()
        if not selection:
            self.selected_component = None
            self.select_btn.state(['disabled'])
            self._update_details(None)
            return

        item = selection[0]
        tags = self.tree.item(item, 'tags')

        if 'component' not in tags:
            # Selected a vendor or subtype, not a component
            self.selected_component = None
            self.select_btn.state(['disabled'])
            self._update_details(None)
            return

        # Get component data
        values = self.tree.item(item, 'values')
        if values:
            comp_id = values[0]
            self.selected_component = self.component_lookup.get(comp_id)

            if self.selected_component:
                self.select_btn.state(['!disabled'])
                self._update_details(self.selected_component)
                self._update_loss_estimate()

    def _on_double_click(self, event):
        """Handle double-click to select"""
        if self.selected_component:
            self._select_component()

    def _update_details(self, component: Optional[Dict]):
        """Update the details panel"""
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)

        if not component:
            self.details_text.insert('1.0', "Select a component to view details")
            self.details_text.config(state='disabled')
            return

        # Build details display
        lines = []

        if component.get('is_antenna'):
            lines.append(f"ANTENNA: {component.get('name', 'Unknown')}")
            lines.append("=" * 40)
            lines.append(f"Manufacturer: {component.get('manufacturer', 'N/A')}")
            lines.append(f"Part Number:  {component.get('part_number', 'N/A')}")
            lines.append(f"Type:         {component.get('type', 'N/A')}")
            lines.append(f"Gain:         {component.get('gain', 0):+.1f} dBi")
            lines.append(f"Band:         {component.get('band', 'N/A')}")

            freq_range = component.get('frequency_range')
            if freq_range:
                lines.append(f"Freq Range:   {freq_range}")

            lines.append("")
            lines.append("Pattern Data:")
            pattern = component.get('pattern', {})
            if pattern:
                lines.append(f"  Azimuth points: {len(pattern)}")
            else:
                lines.append("  (Default omni pattern)")
        else:
            model = component.get('model', 'Unknown')
            lines.append(f"MODEL: {model}")
            lines.append("=" * 40)
            lines.append(f"Manufacturer: {component.get('manufacturer', 'N/A')}")
            lines.append(f"Part Number:  {component.get('part_number', model)}")
            lines.append(f"Type:         {component.get('component_type', 'N/A')}")

            desc = component.get('description', '')
            if desc:
                lines.append(f"Description:  {desc}")

            # Type-specific details
            comp_type = component.get('component_type')

            if comp_type == 'cable':
                lines.append("")
                lines.append("Cable Specifications:")
                lines.append(f"  Impedance:    {component.get('impedance_ohms', 50)} ohms")
                lines.append(f"  Velocity:     {component.get('velocity_factor', 0.85):.2f}")
                lines.append(f"  OD:           {component.get('outer_diameter_inches', 'N/A')} in")

                loss_data = component.get('loss_db_per_100ft', {})
                if loss_data:
                    lines.append("")
                    lines.append("Loss per 100ft:")
                    for freq in sorted(loss_data.keys(), key=float):
                        lines.append(f"  {freq} MHz: {loss_data[freq]:.2f} dB")

            elif comp_type == 'transmitter':
                lines.append("")
                lines.append("Transmitter Specifications:")
                lines.append(f"  Max Power:    {component.get('power_output_watts', 'N/A')} W")
                lines.append(f"  Efficiency:   {component.get('efficiency_percent', 'N/A')}%")

                freq_range = component.get('frequency_range_mhz', [])
                if freq_range:
                    lines.append(f"  Freq Range:   {freq_range[0]}-{freq_range[1]} MHz")

            elif 'insertion_loss_db' in component:
                lines.append("")
                lines.append(f"Insertion Loss: {component.get('insertion_loss_db', 0):.2f} dB")

            elif 'gain_dbi' in component:
                lines.append("")
                lines.append(f"Gain: {component.get('gain_dbi', 0):+.1f} dBi")

        self.details_text.insert('1.0', '\n'.join(lines))
        self.details_text.config(state='disabled')

    def _update_loss_estimate(self):
        """Update loss estimate for cables"""
        if self.component_type != 'cable' or not self.selected_component:
            return

        try:
            length_ft = float(self.length_var.get())
            loss = self.component_library.interpolate_cable_loss(
                self.selected_component, self.frequency_mhz, length_ft
            )
            self.loss_label.config(text=f"{loss:.2f} dB")
        except (ValueError, AttributeError):
            self.loss_label.config(text="-- dB")

    def _select_component(self):
        """Select current component and close dialog"""
        if not self.selected_component:
            return

        # Get length for cables
        length_ft = 0
        if self.component_type == 'cable':
            try:
                length_ft = float(self.length_var.get())
            except ValueError:
                messagebox.showerror("Invalid Length", "Please enter a valid cable length")
                return

        # Call the callback
        self.on_select(self.selected_component, length_ft)
        self.dialog.destroy()

    def _trigger_ai_import(self):
        """Trigger AI import callback"""
        if self.on_ai_import:
            self.dialog.destroy()
            self.on_ai_import()

    def _trigger_manual_add(self):
        """Trigger manual add callback"""
        if self.on_manual_add:
            self.dialog.destroy()
            self.on_manual_add()


class AntennaBrowserDialog(ComponentBrowserDialog):
    """Specialized browser for antennas with apply-to-station support"""

    def __init__(self, parent, frequency_mhz: float,
                 on_select: Callable, on_apply: Optional[Callable] = None,
                 on_ai_import: Optional[Callable] = None,
                 on_manual_add: Optional[Callable] = None):
        """Initialize antenna browser

        Args:
            parent: Parent window
            frequency_mhz: Operating frequency
            on_select: Callback when antenna selected
            on_apply: Callback to apply antenna to station
            on_ai_import: Callback for AI import
            on_manual_add: Callback for manual add
        """
        self.on_apply = on_apply
        super().__init__(parent, 'antenna', frequency_mhz, on_select,
                        on_ai_import, on_manual_add)

    def _create_dialog(self):
        """Create dialog with antenna-specific options"""
        super()._create_dialog()

        # Add bearing and downtilt fields
        orient_frame = ttk.Frame(self.dialog)
        orient_frame.pack(fill=tk.X, padx=10, pady=5, before=self.dialog.winfo_children()[-1])

        ttk.Label(orient_frame, text="Bearing (0°=N):").pack(side=tk.LEFT, padx=5)
        self.bearing_var = tk.StringVar(value="0.0")
        ttk.Entry(orient_frame, textvariable=self.bearing_var, width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(orient_frame, text="Downtilt (+down):").pack(side=tk.LEFT, padx=(20, 5))
        self.downtilt_var = tk.StringVar(value="0.0")
        ttk.Entry(orient_frame, textvariable=self.downtilt_var, width=8).pack(side=tk.LEFT, padx=5)

        # Rename select button
        self.select_btn.config(text="Select Antenna")

        # Add Apply to Station button if callback provided
        if self.on_apply:
            # Find the button frame
            for child in self.dialog.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            # This might be button_frame
                            pass

    def _select_component(self):
        """Select antenna with bearing/downtilt"""
        if not self.selected_component:
            return

        try:
            bearing = float(self.bearing_var.get()) % 360
            downtilt = float(self.downtilt_var.get())
            downtilt = max(-90, min(90, downtilt))
        except ValueError:
            bearing = 0.0
            downtilt = 0.0

        # Add orientation to component data
        result = {
            **self.selected_component,
            'bearing': bearing,
            'downtilt': downtilt
        }

        self.on_select(result, 0)
        self.dialog.destroy()
