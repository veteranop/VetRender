"""
FCC Query Dialog
===============
Dialog for managing FCC data queries, viewing results, and manual queries.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import datetime


class FCCDialog:
    """Dialog for FCC data management"""

    def __init__(self, parent, fcc_api, current_lat, current_lon, current_freq, fcc_data=None):
        """Initialize FCC dialog

        Args:
            parent: Parent window
            fcc_api: FCC API handler instance
            current_lat: Current transmitter latitude
            current_lon: Current transmitter longitude
            current_freq: Current frequency
            fcc_data: Reference to FCC data (will be updated)
        """
        print(f"FCC DIALOG: Initializing with lat={current_lat}, lon={current_lon}, freq={current_freq}")
        print(f"FCC DIALOG: fcc_data provided: {fcc_data is not None}")
        if fcc_data:
            print(f"FCC DIALOG: fcc_data keys: {list(fcc_data.keys()) if isinstance(fcc_data, dict) else 'not dict'}")

        self.parent = parent
        self.fcc_api = fcc_api
        self.current_lat = current_lat
        self.current_lon = current_lon
        self.current_freq = current_freq
        # Store reference to fcc_data for updates
        self.fcc_data_ref = fcc_data
        self.fcc_data = fcc_data  # Work directly with the reference

        print("FCC DIALOG: Creating Toplevel window")
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("FCC Data Management")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)

        # Status variables
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.StringVar(value="")

        print("FCC DIALOG: Setting up UI")
        self.setup_ui()
        print("FCC DIALOG: Initialization complete")

    def setup_ui(self):
        """Setup the dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="FCC Broadcast Facility Data",
                               font=('TkDefaultFont', 14, 'bold'))
        title_label.pack(pady=(0, 10))

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                font=('TkDefaultFont', 10, 'bold'))
        status_label.pack(side=tk.LEFT, padx=(5, 0))

        # Progress indicator
        progress_label = ttk.Label(status_frame, textvariable=self.progress_var,
                                  foreground='blue')
        progress_label.pack(side=tk.RIGHT)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(button_frame, text="Query Current Station",
                  command=self.query_current_station).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Manual Query",
                  command=lambda: self.notebook.select(self.manual_tab)).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Query by Call Sign",
                  command=self.query_by_call_sign).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Manual Entry",
                  command=self.manual_entry).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Purge Data",
                  command=self.purge_data).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Refresh Display",
                  command=self.update_display).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Close",
                  command=self.on_close).pack(side=tk.RIGHT)

        # Content area with notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Current Data tab
        self.current_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.current_tab, text="Current Data")

        # Manual Query tab
        self.manual_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.manual_tab, text="Manual Query")

        print("FCC DIALOG: Calling setup_current_tab")
        self.setup_current_tab()
        print("FCC DIALOG: Calling setup_manual_tab")
        self.setup_manual_tab()

        print("FCC DIALOG: Calling update_display")
        self.update_display()
        print("FCC DIALOG: UI setup complete")

    def setup_current_tab(self):
        """Setup the current data tab"""
        # Data display
        self.data_text = tk.Text(self.current_tab, wrap=tk.WORD,
                                font=('Courier', 9), state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(self.current_tab, orient=tk.VERTICAL,
                                 command=self.data_text.yview)
        self.data_text.configure(yscrollcommand=scrollbar.set)

        self.data_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        print("FCC DIALOG: setup_current_tab completed")

    def setup_manual_tab(self):
        """Setup the manual query tab"""
        # Input fields
        input_frame = ttk.LabelFrame(self.manual_tab, text="Query Parameters", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        # Row 0: Latitude
        ttk.Label(input_frame, text="Latitude:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.manual_lat_var = tk.StringVar(value=str(self.current_lat))
        ttk.Entry(input_frame, textvariable=self.manual_lat_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        # Row 1: Longitude
        ttk.Label(input_frame, text="Longitude:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.manual_lon_var = tk.StringVar(value=str(self.current_lon))
        ttk.Entry(input_frame, textvariable=self.manual_lon_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        # Row 2: Frequency
        ttk.Label(input_frame, text="Frequency (MHz):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.manual_freq_var = tk.StringVar(value=str(self.current_freq))
        ttk.Entry(input_frame, textvariable=self.manual_freq_var).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        # Row 3: Service
        ttk.Label(input_frame, text="Service:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.manual_service_var = tk.StringVar(value="FM")
        service_combo = ttk.Combobox(input_frame, textvariable=self.manual_service_var,
                                    values=["FM", "AM", "TV"], state="readonly")
        service_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)

        # Row 4: Radius
        ttk.Label(input_frame, text="Search Radius (km):").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.manual_radius_var = tk.StringVar(value="10")
        ttk.Entry(input_frame, textvariable=self.manual_radius_var).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2)

        input_frame.columnconfigure(1, weight=1)

        # Query button
        ttk.Button(input_frame, text="Execute Query",
                  command=self.execute_manual_query).grid(row=5, column=0, columnspan=2, pady=10)

        # Results display
        ttk.Label(self.manual_tab, text="Query Results:").pack(anchor=tk.W, pady=(10, 5))

        self.manual_text = tk.Text(self.manual_tab, wrap=tk.WORD,
                                  font=('Courier', 9), height=20, state=tk.DISABLED)
        manual_scrollbar = ttk.Scrollbar(self.manual_tab, orient=tk.VERTICAL,
                                        command=self.manual_text.yview)
        self.manual_text.configure(yscrollcommand=manual_scrollbar.set)

        self.manual_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        manual_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_close(self):
        """Handle dialog close - ensure data is properly updated"""
        # Since fcc_data is mutable, changes should be reflected in the original
        # But we'll explicitly update the reference to be safe
        if hasattr(self, 'fcc_data_ref') and self.fcc_data_ref is not None:
            # Clear and update the original dict
            self.fcc_data_ref.clear()
            if self.fcc_data:
                self.fcc_data_ref.update(self.fcc_data)
        elif hasattr(self, 'fcc_data_ref') and self.fcc_data:
            # If original was None but we have data now
            self.fcc_data_ref = self.fcc_data
        self.dialog.destroy()

    def query_current_station(self):
        """Query FCC for current station location"""
        print("FCC DIALOG: query_current_station() button clicked")
        def query_thread():
            try:
                print("FCC DIALOG: Starting query thread")
                self.status_var.set("Working...")
                self.progress_var.set("Querying FCC database...")

                # Determine service
                service = 'FM' if self.current_freq >= 88 and self.current_freq <= 108 else 'AM'
                print(f"FCC DIALOG: Using service={service}, freq={self.current_freq}, lat={self.current_lat}, lon={self.current_lon}")

                # Execute query
                facilities = self.fcc_api.search_by_coordinates_and_frequency(
                    self.current_lat, self.current_lon, self.current_freq,
                    service=service, radius_km=10
                )
                print(f"FCC DIALOG: API returned {len(facilities) if facilities else 0} facilities")

                # Store results
                if facilities:
                    print(f"FCC DIALOG: Query successful, storing {len(facilities)} facilities")
                    self.fcc_data = {
                        'query_time': datetime.datetime.now().isoformat(),
                        'query_params': {
                            'lat': self.current_lat,
                            'lon': self.current_lon,
                            'frequency': self.current_freq,
                            'service': service,
                            'radius_km': 10
                        },
                        'facilities': facilities
                    }
                    self.status_var.set("Success")
                    self.progress_var.set(f"Found {len(facilities)} facilities")
                else:
                    print("FCC DIALOG: Query returned no facilities")
                    self.fcc_data = {
                        'query_time': datetime.datetime.now().isoformat(),
                        'query_params': {
                            'lat': self.current_lat,
                            'lon': self.current_lon,
                            'frequency': self.current_freq,
                            'service': service,
                            'radius_km': 10
                        },
                        'facilities': [],
                        'error': 'No facilities found'
                    }
                    self.status_var.set("No Results")
                    self.progress_var.set("Query completed - no facilities found")

                print("FCC DIALOG: Updating display")
                self.update_display()

            except Exception as e:
                print(f"FCC DIALOG: Query failed with exception: {e}")
                import traceback
                traceback.print_exc()

                # Check if it's an API availability issue
                if "404" in str(e) or "Not Found" in str(e):
                    error_msg = "FCC APIs currently unavailable (404 errors)"
                    self.fcc_data = {
                        'query_time': datetime.datetime.now().isoformat(),
                        'error': error_msg,
                        'api_status': 'unavailable'
                    }
                else:
                    error_msg = str(e)
                    self.fcc_data = {
                        'query_time': datetime.datetime.now().isoformat(),
                        'error': error_msg
                    }

                self.status_var.set("API Unavailable")
                self.progress_var.set("FCC APIs are currently not accessible")
                self.update_display()

        # Run query in background thread
        thread = threading.Thread(target=query_thread, daemon=True)
        thread.start()

    def execute_manual_query(self):
        """Execute manual FCC query"""
        try:
            lat = float(self.manual_lat_var.get())
            lon = float(self.manual_lon_var.get())
            freq = float(self.manual_freq_var.get())
            service = self.manual_service_var.get()
            radius = float(self.manual_radius_var.get())

            def query_thread():
                try:
                    self.status_var.set("Working...")
                    self.progress_var.set("Executing manual query...")

                    facilities = self.fcc_api.search_by_coordinates_and_frequency(
                        lat, lon, freq, service=service, radius_km=radius
                    )

                    # Store results
                    self.fcc_data = {
                        'query_time': datetime.datetime.now().isoformat(),
                        'query_params': {
                            'lat': lat,
                            'lon': lon,
                            'frequency': freq,
                            'service': service,
                            'radius_km': radius
                        },
                        'facilities': facilities or []
                    }

                    if facilities:
                        self.status_var.set("Success")
                        self.progress_var.set(f"Found {len(facilities)} facilities")
                    else:
                        self.status_var.set("No Results")
                        self.progress_var.set("Query completed - no facilities found")

                    self.update_display()
                    self.notebook.select(self.current_tab)  # Switch to current data tab

                except Exception as e:
                    self.status_var.set("Error")
                    self.progress_var.set(f"Query failed: {str(e)}")

            thread = threading.Thread(target=query_thread, daemon=True)
            thread.start()

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values")

    def query_by_call_sign(self):
        """Query FCC by call sign using scraper"""
        # Ask for call sign
        call_sign_dialog = tk.Toplevel(self.dialog)
        call_sign_dialog.title("Query by Call Sign")
        call_sign_dialog.geometry("400x150")
        call_sign_dialog.transient(self.dialog)

        # Center dialog
        call_sign_dialog.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() // 2) - (call_sign_dialog.winfo_width() // 2)
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() // 2) - (call_sign_dialog.winfo_height() // 2)
        call_sign_dialog.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(call_sign_dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Enter Call Sign:", font=('TkDefaultFont', 12)).pack(pady=(0, 10))

        call_sign_var = tk.StringVar(value="KDPI")
        entry = ttk.Entry(main_frame, textvariable=call_sign_var, width=20, font=('TkDefaultFont', 12))
        entry.pack(pady=(0, 20))
        entry.select_range(0, tk.END)
        entry.focus()

        def do_query():
            call_sign = call_sign_var.get().strip().upper()
            if not call_sign:
                messagebox.showerror("Error", "Please enter a call sign")
                return

            call_sign_dialog.destroy()

            # Run query in background thread
            def query_thread():
                try:
                    self.status_var.set(f"Querying FCC for {call_sign}...")
                    self.progress_var.set("Using web scraper (this may take 10-15 seconds)")

                    # Use scraper
                    results = self.fcc_api.search_by_call_sign_scraper(call_sign)

                    if results and len(results) > 0:
                        # Store the data
                        self.fcc_data = {
                            'query_time': datetime.datetime.now().isoformat(),
                            'query_params': {
                                'call_sign': call_sign,
                                'method': 'scraper'
                            },
                            'facilities': results
                        }

                        self.status_var.set(f"Success - Retrieved data for {call_sign}")
                        self.progress_var.set("")
                        self.dialog.after(0, self.update_display)
                        self.dialog.after(0, lambda: self.notebook.select(self.current_tab))
                        self.dialog.after(0, lambda: messagebox.showinfo("Success",
                            f"Retrieved FCC data for {call_sign}"))
                    else:
                        self.status_var.set("No results found")
                        self.progress_var.set("")
                        self.dialog.after(0, lambda: messagebox.showwarning("No Results",
                            f"No FCC data found for {call_sign}"))

                except Exception as e:
                    self.status_var.set("Query failed")
                    self.progress_var.set("")
                    self.dialog.after(0, lambda: messagebox.showerror("Error",
                        f"Failed to query FCC:\n{str(e)}"))

            thread = threading.Thread(target=query_thread, daemon=True)
            thread.start()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack()

        ttk.Button(button_frame, text="Query", command=do_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=call_sign_dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Bind Enter key
        entry.bind('<Return>', lambda e: do_query())

    def manual_entry(self):
        """Manual FCC facility data entry"""
        manual_dialog = tk.Toplevel(self.dialog)
        manual_dialog.title("Manual FCC Data Entry")
        manual_dialog.geometry("600x500")
        manual_dialog.transient(self.dialog)
        manual_dialog.grab_set()

        ttk.Label(manual_dialog, text="Enter FCC Facility Data Manually",
                 font=('TkDefaultFont', 14, 'bold')).pack(pady=10)

        # Scrollable frame for form
        canvas = tk.Canvas(manual_dialog)
        scrollbar = ttk.Scrollbar(manual_dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Form fields
        fields = {}
        row = 0

        # Basic facility info
        ttk.Label(scrollable_frame, text="Facility Information", font=('TkDefaultFont', 11, 'bold')).grid(row=row, column=0, columnspan=2, pady=(0, 10))
        row += 1

        field_defs = [
            ("Call Sign:", "callSign", "KDPI"),
            ("Facility ID:", "facilityId", "66505"),
            ("Frequency (MHz):", "frequency", "88.5"),
            ("Service:", "service", "FM"),
            ("City:", "city", "KETCHUM"),
            ("State:", "state", "ID"),
            ("ERP (Watts):", "erp", "4000"),
            ("HAAT (Meters):", "haat", "595"),
            ("Latitude:", "latitude", "43.6807"),
            ("Longitude:", "longitude", "-114.3637"),
        ]

        for label_text, field_name, default_value in field_defs:
            ttk.Label(scrollable_frame, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=default_value)
            fields[field_name] = var
            ttk.Entry(scrollable_frame, textvariable=var, width=25).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
            row += 1

        # Instructions
        ttk.Label(scrollable_frame, text="\nInstructions:", font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, columnspan=2, pady=(20, 5))
        row += 1

        instructions = tk.Text(scrollable_frame, height=6, width=60, wrap=tk.WORD)
        instructions.insert(tk.END,
            "1. Visit https://www.fcc.gov/media/radio/am-fm-tv-and-translator-search\n"
            "2. Search for your station by call sign or location\n"
            "3. Copy the facility data from the results\n"
            "4. Fill in the fields above and click Save\n\n"
            "This allows accurate coverage calculations using official FCC data.")
        instructions.config(state=tk.DISABLED)
        instructions.grid(row=row, column=0, columnspan=2, pady=(0, 20))
        row += 1

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        def save_manual_data():
            """Save the manually entered FCC data"""
            try:
                # Validate required fields
                call_sign = fields['callSign'].get().strip()
                if not call_sign:
                    messagebox.showerror("Error", "Call sign is required")
                    return

                # Create facility data
                facility = {
                    'callSign': call_sign,
                    'facilityId': fields['facilityId'].get().strip(),
                    'frequency': float(fields['frequency'].get()),
                    'service': fields['service'].get().strip(),
                    'city': fields['city'].get().strip(),
                    'state': fields['state'].get().strip(),
                    'erp': int(fields['erp'].get()) if fields['erp'].get().strip() else 0,
                    'haat': int(fields['haat'].get()) if fields['haat'].get().strip() else 0,
                    'latitude': float(fields['latitude'].get()),
                    'longitude': float(fields['longitude'].get())
                }

                # Store the data
                self.fcc_data = {
                    'query_time': datetime.datetime.now().isoformat(),
                    'query_params': {
                        'manual_entry': True,
                        'call_sign': call_sign
                    },
                    'facilities': [facility]
                }

                manual_dialog.destroy()
                self.status_var.set("Manual Data Saved")
                self.progress_var.set(f"Added facility: {call_sign}")
                self.update_display()
                self.notebook.select(self.current_tab)

                messagebox.showinfo("Success", f"FCC data for {call_sign} has been saved successfully!")

            except ValueError as e:
                messagebox.showerror("Invalid Data", f"Please check your input values:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data:\n{str(e)}")

        def cancel():
            manual_dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(manual_dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save FCC Data", command=save_manual_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

    def purge_data(self):
        """Purge FCC data"""
        if messagebox.askyesno("Confirm Purge",
                              "Are you sure you want to clear all FCC data?\n\n"
                              "This cannot be undone."):
            self.fcc_data = None
            self.status_var.set("Data Cleared")
            self.progress_var.set("")
            self.update_display()

    def update_display(self):
        """Update the data display"""
        # Update current data tab
        self.data_text.config(state=tk.NORMAL)
        self.data_text.delete(1.0, tk.END)

        if not self.fcc_data:
            self.data_text.insert(tk.END, "No FCC data available.\n\n")
            self.data_text.insert(tk.END, "Use 'Query Current Station' to fetch FCC data for your transmitter location,\n")
            self.data_text.insert(tk.END, "or use 'Manual Query' to search for facilities at any location.\n\n")
            self.data_text.insert(tk.END, "FCC data will be saved with your project and included in reports.\n\n")
            self.data_text.insert(tk.END, "NOTE: FCC APIs appear to be currently unavailable. ")
            self.data_text.insert(tk.END, "You can still manually research station information using the links below.")
        else:
            # Display query info
            if 'error' in self.fcc_data:
                if self.fcc_data.get('api_status') == 'unavailable':
                    self.data_text.insert(tk.END, "FCC API UNAVAILABLE\n")
                    self.data_text.insert(tk.END, f"Error: {self.fcc_data['error']}\n\n")
                    self.data_text.insert(tk.END, "The FCC's public APIs are currently not accessible.\n")
                    self.data_text.insert(tk.END, "This may be due to API changes, maintenance, or access restrictions.\n\n")
                    self.data_text.insert(tk.END, "ALTERNATIVE METHODS:\n")
                    self.data_text.insert(tk.END, "• FCC Facility Search: https://www.fcc.gov/media/radio/am-fm-tv-and-translator-search\n")
                    self.data_text.insert(tk.END, "• FCC Data Portal: https://www.fccdata.org\n")
                    self.data_text.insert(tk.END, "• FCC Licensing Databases: https://www.fcc.gov/licensing-databases\n\n")
                else:
                    self.data_text.insert(tk.END, f"QUERY ERROR: {self.fcc_data['error']}\n\n")
            else:
                params = self.fcc_data.get('query_params', {})
                self.data_text.insert(tk.END, f"Query Time: {self.fcc_data.get('query_time', 'Unknown')[:19]}\n")
                self.data_text.insert(tk.END, f"Location: {params.get('lat', 0):.6f}°, {params.get('lon', 0):.6f}°\n")
                self.data_text.insert(tk.END, f"Frequency: {params.get('frequency', 0)} MHz\n")
                self.data_text.insert(tk.END, f"Service: {params.get('service', 'Unknown')}\n")
                self.data_text.insert(tk.END, f"Search Radius: {params.get('radius_km', 0)} km\n\n")

                facilities = self.fcc_data.get('facilities', [])
                if facilities:
                    self.data_text.insert(tk.END, f"FOUND {len(facilities)} FACILITY(IES):\n\n")
                    for i, facility in enumerate(facilities, 1):
                        self.data_text.insert(tk.END, f"FACILITY {i}:\n")
                        self.data_text.insert(tk.END, f"  Call Sign: {facility.get('callSign', 'N/A')}\n")
                        self.data_text.insert(tk.END, f"  Facility ID: {facility.get('facilityId', 'N/A')}\n")
                        self.data_text.insert(tk.END, f"  Frequency: {facility.get('frequency', 'N/A')} MHz\n")
                        self.data_text.insert(tk.END, f"  City: {facility.get('city', 'N/A')}\n")
                        self.data_text.insert(tk.END, f"  State: {facility.get('state', 'N/A')}\n")
                        self.data_text.insert(tk.END, f"  ERP: {facility.get('erp', 'N/A')} W\n")
                        self.data_text.insert(tk.END, f"  HAAT: {facility.get('haat', 'N/A')} m\n")
                        self.data_text.insert(tk.END, f"  Location: {facility.get('latitude', 0):.6f}°, {facility.get('longitude', 0):.6f}°\n")
                        self.data_text.insert(tk.END, "\n")
                else:
                    self.data_text.insert(tk.END, "NO FACILITIES FOUND\n")

        self.data_text.config(state=tk.DISABLED)

        # Update manual query tab
        self.manual_text.config(state=tk.NORMAL)
        self.manual_text.delete(1.0, tk.END)
        self.manual_text.insert(tk.END, "Manual query results will appear here after execution.\n\n")
        self.manual_text.insert(tk.END, "Use the form above to specify custom search parameters.")
        self.manual_text.config(state=tk.DISABLED)