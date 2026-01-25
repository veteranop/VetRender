"""
Smart Import Dialog
===================
Unified PDF/URL import that auto-detects component type (antenna vs other RF components)
and routes to appropriate processing logic.

Supports:
- Single component PDFs
- Multi-model PDFs (like antenna datasheets with multiple models)
- Automatic antenna vs component detection
- URL scraping for specifications
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import threading
from typing import Optional, Callable, Dict, List

# Try imports - will be checked at runtime
try:
    import requests
except ImportError:
    requests = None

try:
    import fitz  # PyMuPDF - better for text+images
except ImportError:
    fitz = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


class SmartImportDialog:
    """Smart import dialog that detects component type and processes accordingly"""

    COLORS = {
        'bg': '#1e1e1e',
        'bg_medium': '#252526',
        'fg': '#cccccc',
        'accent': '#0078d4',
        'success': '#4caf50',
        'warning': '#ff9800',
        'error': '#f44336'
    }

    def __init__(self, parent, frequency_mhz: float,
                 on_component_imported: Optional[Callable] = None,
                 on_antenna_imported: Optional[Callable] = None):
        """Initialize smart import dialog

        Args:
            parent: Parent window
            frequency_mhz: Operating frequency for component calculations
            on_component_imported: Callback for non-antenna components (component_dict)
            on_antenna_imported: Callback for antennas (antenna_id)
        """
        self.parent = parent
        self.frequency_mhz = frequency_mhz
        self.on_component_imported = on_component_imported
        self.on_antenna_imported = on_antenna_imported

        # Import libraries
        from models.component_library import ComponentLibrary
        from models.antenna_library import AntennaLibrary
        self.component_library = ComponentLibrary()
        self.antenna_library = AntennaLibrary()

        # Results storage
        self.extracted_items = []  # List of extracted components/antennas
        self.pdf_text = ""

        self._create_dialog()

    def _create_dialog(self):
        """Create the import dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Smart Import - PDF or URL")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Main container
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(main_frame, text="Import RF Component or Antenna",
                 style='Title.TLabel').pack(pady=(0, 15))

        ttk.Label(main_frame, text="Drop a PDF datasheet or enter a URL. The system will automatically\n"
                                   "detect if it's an antenna or other RF component and process accordingly.",
                 font=('Segoe UI', 9)).pack(pady=(0, 15))

        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input Source", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        # PDF file
        pdf_row = ttk.Frame(input_frame)
        pdf_row.pack(fill=tk.X, pady=5)
        ttk.Label(pdf_row, text="PDF File:").pack(side=tk.LEFT, padx=5)
        self.pdf_var = tk.StringVar()
        ttk.Entry(pdf_row, textvariable=self.pdf_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(pdf_row, text="Browse...", command=self._browse_pdf).pack(side=tk.LEFT, padx=5)

        # URL
        url_row = ttk.Frame(input_frame)
        url_row.pack(fill=tk.X, pady=5)
        ttk.Label(url_row, text="Or URL:").pack(side=tk.LEFT, padx=5)
        self.url_var = tk.StringVar()
        ttk.Entry(url_row, textvariable=self.url_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Manual query (for AI search without PDF)
        query_row = ttk.Frame(input_frame)
        query_row.pack(fill=tk.X, pady=5)
        ttk.Label(query_row, text="Or Search:").pack(side=tk.LEFT, padx=5)
        self.query_var = tk.StringVar()
        ttk.Entry(query_row, textvariable=self.query_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(query_row, text="(model/part number)", font=('Segoe UI', 8, 'italic')).pack(side=tk.LEFT)

        # Process button
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)

        self.process_btn = ttk.Button(btn_frame, text="Process & Detect Type",
                                       command=self._process_input,
                                       style='Accent.TButton')
        self.process_btn.pack(side=tk.LEFT, padx=5)

        # Status
        self.status_var = tk.StringVar(value="Ready - provide a PDF, URL, or search query")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)

        # Results section (hidden initially)
        self.results_frame = ttk.LabelFrame(main_frame, text="Detected Items", padding=10)

        # Results treeview
        columns = ('type', 'model', 'manufacturer', 'details')
        self.results_tree = ttk.Treeview(self.results_frame, columns=columns,
                                          show='headings', height=6)
        self.results_tree.heading('type', text='Type')
        self.results_tree.heading('model', text='Model')
        self.results_tree.heading('manufacturer', text='Manufacturer')
        self.results_tree.heading('details', text='Details')

        self.results_tree.column('type', width=80)
        self.results_tree.column('model', width=150)
        self.results_tree.column('manufacturer', width=120)
        self.results_tree.column('details', width=200)

        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.config(yscrollcommand=scrollbar.set)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Import buttons (hidden initially)
        self.import_btn_frame = ttk.Frame(main_frame)
        ttk.Button(self.import_btn_frame, text="Import Selected",
                  command=self._import_selected,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(self.import_btn_frame, text="Import All",
                  command=self._import_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.import_btn_frame, text="Edit Before Import...",
                  command=self._edit_before_import).pack(side=tk.LEFT, padx=5)

        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(15, 0), side=tk.BOTTOM)
        ttk.Button(bottom_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _browse_pdf(self):
        """Browse for PDF file"""
        filepath = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select Datasheet PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filepath:
            self.pdf_var.set(filepath)
            # Clear other inputs
            self.url_var.set("")
            self.query_var.set("")

    def _process_input(self):
        """Process the input (PDF, URL, or query)"""
        pdf_path = self.pdf_var.get().strip()
        url = self.url_var.get().strip()
        query = self.query_var.get().strip()

        if not pdf_path and not url and not query:
            messagebox.showwarning("No Input", "Please provide a PDF file, URL, or search query")
            return

        # Start processing
        self.process_btn.state(['disabled'])
        self.progress.start()
        self.status_var.set("Processing...")

        def process_thread():
            try:
                if pdf_path:
                    self._process_pdf(pdf_path)
                elif url:
                    self._process_url(url)
                else:
                    self._process_query(query)

                self.dialog.after(0, self._on_processing_complete)
            except Exception as e:
                error_msg = str(e)
                self.dialog.after(0, lambda: self._on_processing_error(error_msg))

        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()

    def _process_pdf(self, pdf_path: str):
        """Process a PDF file"""
        self.dialog.after(0, lambda: self.status_var.set("Extracting text from PDF..."))

        # Extract text
        text = self._extract_pdf_text(pdf_path)
        if not text or len(text.strip()) < 50:
            raise Exception("PDF appears empty or has insufficient text content")

        self.pdf_text = text
        print(f"Extracted {len(text)} characters from PDF")

        # Detect type and extract items
        self.dialog.after(0, lambda: self.status_var.set("Detecting component type..."))
        self._detect_and_extract(text)

    def _process_url(self, url: str):
        """Process a URL"""
        if not requests:
            raise Exception("requests library not installed. Install with: pip install requests")

        self.dialog.after(0, lambda: self.status_var.set("Fetching URL content..."))

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            # Try to extract text from HTML
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
            except ImportError:
                text = response.text

            self.pdf_text = text
            self._detect_and_extract(text)

        except Exception as e:
            raise Exception(f"Failed to fetch URL: {e}")

    def _process_query(self, query: str):
        """Process a search query using Ollama"""
        self.dialog.after(0, lambda: self.status_var.set(f"Searching for '{query}' with AI..."))

        # Use component library's Ollama search
        component = self.component_library.ollama_search_component(query, self.frequency_mhz)

        if component:
            # Determine if it's an antenna
            comp_type = component.get('component_type', '').lower()
            if comp_type == 'antenna':
                self.extracted_items = [{
                    'type': 'antenna',
                    'data': component,
                    'model': component.get('model', query),
                    'manufacturer': component.get('manufacturer', 'Unknown'),
                    'details': f"Gain: {component.get('gain_dbi', 0)} dBi"
                }]
            else:
                self.extracted_items = [{
                    'type': comp_type or 'component',
                    'data': component,
                    'model': component.get('model', query),
                    'manufacturer': component.get('manufacturer', 'Unknown'),
                    'details': self._get_component_details(component)
                }]
        else:
            self.extracted_items = []

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF using available library"""
        if fitz:
            # Use PyMuPDF (better quality)
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text
        elif PyPDF2:
            # Use PyPDF2 (fallback)
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        else:
            raise Exception("No PDF library available. Install with: pip install PyMuPDF")

    def _detect_and_extract(self, text: str):
        """Detect component type and extract items from text"""
        self.dialog.after(0, lambda: self.status_var.set("Analyzing with AI..."))

        # Use Ollama to detect type and extract components
        items = self._ollama_extract_components(text)
        self.extracted_items = items

    def _ollama_extract_components(self, text: str) -> List[Dict]:
        """Use Ollama to extract components from text"""
        import requests
        import json

        prompt = f"""Analyze this RF equipment datasheet and extract ALL components/products listed.

IMPORTANT: Determine if this is an ANTENNA datasheet or OTHER RF component (cable, transmitter, amplifier, filter, etc.)

For EACH product found, provide:
- component_type: "antenna" OR specific type like "cable", "transmitter", "amplifier", "filter", "isolator", etc.
- model: The model/part number
- manufacturer: The manufacturer name
- For antennas: gain_dbi, frequency_range, beamwidth, type (omni/directional)
- For cables: loss_db_per_100ft at various frequencies, impedance_ohms, velocity_factor
- For transmitters: power_output_watts, frequency_range_mhz, efficiency_percent
- For other: insertion_loss_db, gain_dbi as applicable

Return JSON array of ALL products found. Example:
[
  {{"component_type": "antenna", "model": "ABC-123", "manufacturer": "Acme", "gain_dbi": 6.0, "frequency_range": "88-108 MHz"}},
  {{"component_type": "cable", "model": "LMR-400", "manufacturer": "Times", "loss_db_per_100ft": {{"100": 0.7, "400": 1.3}}, "impedance_ohms": 50}}
]

If only ONE product is found, still return it as an array with one element.
Return ONLY valid JSON - no markdown, no explanation.

DATASHEET TEXT:
{text[:12000]}
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
                # Try llama3.2 as fallback
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': 'llama3.2',
                        'prompt': prompt,
                        'stream': False
                    },
                    timeout=120
                )

            result = response.json()
            response_text = result.get('response', '').strip()

            if not response_text:
                raise Exception("Ollama returned empty response")

            # Parse JSON
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response_text.strip()

            items_data = json.loads(json_str)

            # Ensure it's a list
            if isinstance(items_data, dict):
                items_data = [items_data]

            # Convert to our format and normalize data
            items = []
            for item in items_data:
                comp_type = item.get('component_type', item.get('type', 'component')).lower()

                # Normalize loss_db_per_100ft to dict if it's a list
                if 'loss_db_per_100ft' in item:
                    loss_data = item['loss_db_per_100ft']
                    if isinstance(loss_data, list):
                        # Convert list to dict
                        if loss_data and isinstance(loss_data[0], dict):
                            item['loss_db_per_100ft'] = {
                                str(d.get('freq', d.get('frequency', i*100))): d.get('loss', d.get('value', 0))
                                for i, d in enumerate(loss_data)
                            }
                        else:
                            # Just values - assume standard frequencies
                            std_freqs = [100, 200, 400, 900, 1800]
                            item['loss_db_per_100ft'] = {
                                str(std_freqs[i] if i < len(std_freqs) else (i+1)*100): v
                                for i, v in enumerate(loss_data)
                            }

                # Ensure component_type is set
                item['component_type'] = comp_type

                items.append({
                    'type': comp_type,
                    'data': item,
                    'model': item.get('model', 'Unknown'),
                    'manufacturer': item.get('manufacturer', 'Unknown'),
                    'details': self._get_component_details(item)
                })

            return items

        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Is Ollama running? (ollama serve)")
        except requests.exceptions.Timeout:
            raise Exception("Ollama request timed out. Model may still be loading.")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response: {e}")

    def _get_component_details(self, component: Dict) -> str:
        """Get a summary of component details for display"""
        comp_type = component.get('component_type', '').lower()

        if comp_type == 'antenna':
            gain = component.get('gain_dbi', component.get('gain', 'N/A'))
            freq = component.get('frequency_range', 'N/A')
            return f"Gain: {gain} dBi, Freq: {freq}"
        elif comp_type == 'cable':
            impedance = component.get('impedance_ohms', 50)
            loss = component.get('loss_db_per_100ft', {})
            if loss and isinstance(loss, dict):
                first_freq = list(loss.keys())[0] if loss else 'N/A'
                first_loss = list(loss.values())[0] if loss else 'N/A'
                return f"{impedance}Ω, Loss: {first_loss} dB/100ft @ {first_freq} MHz"
            elif loss and isinstance(loss, list) and loss:
                return f"{impedance}Ω, Loss data available"
            return f"{impedance}Ω"
        elif comp_type == 'transmitter':
            power = component.get('power_output_watts', 'N/A')
            return f"Power: {power} W"
        elif 'insertion_loss_db' in component:
            return f"Loss: {component.get('insertion_loss_db')} dB"
        elif 'gain_dbi' in component:
            return f"Gain: {component.get('gain_dbi')} dBi"
        else:
            desc = component.get('description', '')
            return desc[:50] if desc else 'N/A'

    def _on_processing_complete(self):
        """Handle processing completion"""
        self.progress.stop()
        self.process_btn.state(['!disabled'])

        if not self.extracted_items:
            self.status_var.set("No components found in the input")
            messagebox.showwarning("No Results", "Could not extract any components from the input.\n"
                                               "Try a different PDF or search query.")
            return

        # Show results
        self.status_var.set(f"Found {len(self.extracted_items)} item(s)")

        # Populate treeview
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        for i, item in enumerate(self.extracted_items):
            self.results_tree.insert('', tk.END, iid=str(i), values=(
                item['type'].title(),
                item['model'],
                item['manufacturer'],
                item['details']
            ))

        # Select first item
        if self.extracted_items:
            self.results_tree.selection_set('0')

        # Show results frame and import buttons
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.import_btn_frame.pack(fill=tk.X, pady=10)

    def _on_processing_error(self, error_msg: str):
        """Handle processing error"""
        self.progress.stop()
        self.process_btn.state(['!disabled'])
        self.status_var.set(f"Error: {error_msg[:50]}...")
        messagebox.showerror("Processing Error", f"Error processing input:\n\n{error_msg}")

    def _import_selected(self):
        """Import the selected item"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to import")
            return

        idx = int(selection[0])
        item = self.extracted_items[idx]
        self._import_item(item)

    def _import_all(self):
        """Import all extracted items"""
        if not self.extracted_items:
            return

        count = 0
        for item in self.extracted_items:
            try:
                self._import_item(item, show_message=False)
                count += 1
            except Exception as e:
                print(f"Failed to import {item['model']}: {e}")

        messagebox.showinfo("Import Complete", f"Successfully imported {count} of {len(self.extracted_items)} items")
        self.dialog.destroy()

    def _import_item(self, item: Dict, show_message: bool = True):
        """Import a single item"""
        comp_type = item['type'].lower()
        data = item['data']

        if comp_type == 'antenna':
            self._import_antenna(data, show_message)
        else:
            self._import_component(data, show_message)

    def _import_antenna(self, data: Dict, show_message: bool = True):
        """Import an antenna to the antenna library"""
        from models.antenna_library import AntennaLibrary

        # Generate antenna ID
        model = data.get('model', 'Imported_Antenna')
        antenna_id = model.replace(' ', '_').replace('/', '_')

        # Check for duplicates
        existing_ids = list(self.antenna_library.antennas.keys())
        base_id = antenna_id
        counter = 0
        while antenna_id in existing_ids:
            counter += 1
            antenna_id = f"{base_id}_{counter}"

        # Create antenna data for library
        antenna_data = {
            'name': data.get('model', 'Imported Antenna'),
            'manufacturer': data.get('manufacturer', 'Unknown'),
            'part_number': data.get('model', ''),
            'gain': float(data.get('gain_dbi', data.get('gain', 0))),
            'band': data.get('band', ''),
            'frequency_range': data.get('frequency_range', ''),
            'type': data.get('type', 'Directional'),
            'pattern': {}  # Default pattern - can be enhanced later
        }

        # Add to library
        self.antenna_library.antennas[antenna_id] = antenna_data

        # Save to XML file
        self.antenna_library.save_antenna(antenna_id)

        if show_message:
            messagebox.showinfo("Antenna Imported",
                              f"Antenna '{antenna_data['name']}' has been imported to the library.")

        # Call callback
        if self.on_antenna_imported:
            self.on_antenna_imported(antenna_id)

    def _import_component(self, data: Dict, show_message: bool = True):
        """Import a component to the component library"""
        # Add to component library cache
        self.component_library.add_to_cache(data)

        if show_message:
            messagebox.showinfo("Component Imported",
                              f"Component '{data.get('model', 'Unknown')}' has been imported to the library.")

        # Call callback
        if self.on_component_imported:
            self.on_component_imported(data)

    def _edit_before_import(self):
        """Open edit dialog for selected item before importing"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to edit")
            return

        idx = int(selection[0])
        item = self.extracted_items[idx]

        # Open edit dialog
        from gui.component_browser import EditComponentDialog

        def on_save(updated_data):
            # Update our item
            self.extracted_items[idx]['data'] = updated_data
            self.extracted_items[idx]['model'] = updated_data.get('model', item['model'])
            self.extracted_items[idx]['manufacturer'] = updated_data.get('manufacturer', item['manufacturer'])
            self.extracted_items[idx]['details'] = self._get_component_details(updated_data)

            # Update treeview
            self.results_tree.item(str(idx), values=(
                item['type'].title(),
                self.extracted_items[idx]['model'],
                self.extracted_items[idx]['manufacturer'],
                self.extracted_items[idx]['details']
            ))

        EditComponentDialog(
            self.dialog,
            item['data'],
            item['type'],
            self.component_library,
            self.antenna_library,
            on_save=on_save
        )
