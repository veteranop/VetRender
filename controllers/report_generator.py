"""
Report Generator Module
=======================
Generates professional PDF reports with station information, RF chain details,
coverage maps, and FCC filing information.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from tkinter import filedialog, messagebox
from models.component_library import ComponentLibrary
from models.antenna_library import AntennaLibrary


class ReportGenerator:
    """Generates PDF reports for RF coverage analysis"""

    def __init__(self, config_manager, fcc_api_handler, antenna_pattern=None):
        """Initialize report generator

        Args:
            config_manager: Configuration manager instance
            fcc_api_handler: FCC API handler instance
            antenna_pattern: AntennaPattern instance (optional)
        """
        self.config = config_manager
        self.fcc_api = fcc_api_handler
        self.antenna_pattern = antenna_pattern
        self.component_library = ComponentLibrary()
        self.antenna_library = AntennaLibrary()
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))

        # Subsection heading style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=12,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))

    def generate_report(self, report_config, coverage_images=None):
        """Generate PDF report

        Args:
            report_config: Dictionary with report configuration
            coverage_images: List of coverage image paths

        Returns:
            Path to generated report or None
        """
        try:
            # Ask user where to save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"Cellfire_RF_Report_{timestamp}.pdf"

            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=default_filename,
                title="Save Report"
            )

            if not save_path:
                return None

            # Create PDF document
            doc = SimpleDocTemplate(save_path, pagesize=letter,
                                   rightMargin=0.75*inch, leftMargin=0.75*inch,
                                   topMargin=0.75*inch, bottomMargin=0.75*inch)

            # Build story (content)
            story = []

            # Add cover page
            story.extend(self._build_cover_page())
            story.append(PageBreak())

            # Get report sections configuration
            sections = report_config.get('sections', {})

            # Add FCC information if requested
            if sections.get('fcc_info'):
                fcc_content = self._build_fcc_section()
                if fcc_content:
                    story.extend(fcc_content)
                    story.append(PageBreak())

            # Add station information if requested
            if sections.get('station_info') or sections.get('transmitter_info') or sections.get('frequency_info'):
                story.extend(self._build_station_section(sections))
                story.append(Spacer(1, 0.3*inch))

            # Add RF chain information if requested
            if sections.get('rf_chain') or sections.get('cable_report') or sections.get('loss_budget'):
                story.extend(self._build_rf_chain_section(sections))
                story.append(PageBreak())

            # Add antenna information if requested
            if sections.get('antenna_info'):
                story.extend(self._build_antenna_section())
                story.append(PageBreak())

            # Add coverage maps if requested
            if sections.get('coverage_maps') and coverage_images:
                story.extend(self._build_coverage_section(coverage_images,
                                                         report_config.get('zoom_levels', [])))

            # Build PDF
            doc.build(story)

            messagebox.showinfo("Report Generated",
                              f"Report successfully generated:\n{save_path}")

            return save_path

        except Exception as e:
            messagebox.showerror("Report Generation Error",
                               f"Failed to generate report:\n{str(e)}")
            return None

    def _build_cover_page(self):
        """Build cover page content"""
        content = []

        # Add logo space (placeholder for future branding)
        content.append(Spacer(1, 1.5*inch))

        # Title
        title = Paragraph("RF Coverage Analysis Report", self.styles['CustomTitle'])
        content.append(title)
        content.append(Spacer(1, 0.3*inch))

        # Subtitle
        subtitle = Paragraph("Generated by Cellfire RF Studio", self.styles['Heading3'])
        content.append(subtitle)
        content.append(Spacer(1, 1*inch))

        # Report metadata table
        tx_lat = self.config.get('tx_lat', 0)
        tx_lon = self.config.get('tx_lon', 0)
        frequency = self.config.get('frequency', 0)
        erp = self.config.get('erp', 0)

        metadata = [
            ['Report Date:', datetime.now().strftime("%B %d, %Y")],
            ['Report Time:', datetime.now().strftime("%I:%M %p")],
            ['', ''],
            ['Frequency:', f"{frequency} MHz"],
            ['ERP:', f"{erp} dBm ({10**((erp-30)/10):.1f} W)"],
            ['Location:', f"{tx_lat:.6f}°, {tx_lon:.6f}°"],
        ]

        metadata_table = Table(metadata, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        content.append(metadata_table)
        content.append(Spacer(1, 1*inch))

        # Footer note
        footer = Paragraph(
            "This report contains RF propagation analysis, station information, "
            "and technical specifications for the configured broadcast facility.",
            self.styles['Normal']
        )
        content.append(footer)

        return content

    def _build_fcc_section(self):
        """Build FCC information section using stored project data"""
        content = []

        content.append(Paragraph("FCC Filing Information", self.styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))

        # Check for FCC Downloads folder
        fcc_downloads_dir = os.path.join(os.getcwd(), 'FCC_Downloads')
        fcc_pdfs = []
        if os.path.exists(fcc_downloads_dir):
            fcc_pdfs = [f for f in os.listdir(fcc_downloads_dir) if f.endswith('.pdf')]
            fcc_pdfs.sort(reverse=True)  # Most recent first

        if fcc_pdfs:
            content.append(Paragraph(
                f"<b>FCC Documentation:</b> {len(fcc_pdfs)} FCC query report(s) available in FCC_Downloads folder",
                self.styles['Normal']
            ))
            content.append(Spacer(1, 0.1*inch))

            # List recent FCC PDFs
            for pdf in fcc_pdfs[:3]:  # Show up to 3 most recent
                content.append(Paragraph(
                    f"• {pdf}",
                    self.styles['Normal']
                ))

            if len(fcc_pdfs) > 3:
                content.append(Paragraph(
                    f"• ... and {len(fcc_pdfs) - 3} more",
                    self.styles['Normal']
                ))

            content.append(Spacer(1, 0.2*inch))

        # Get stored FCC data from project
        fcc_data = self.config.get('fcc_data')

        if not fcc_data:
            # No FCC data stored in project
            content.append(Paragraph(
                "<b>Note:</b> No FCC data has been retrieved for this project. "
                "Use the 'Query FCC' menu to pull FCC information before generating reports.",
                self.styles['Normal']
            ))
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(
                "<b>To get FCC data:</b> Go to Query FCC → Pull Report for Current Station",
                self.styles['Normal']
            ))
            content.append(Spacer(1, 0.3*inch))
            return content

        # Check if there was an error in the stored data
        if 'error' in fcc_data:
            if fcc_data.get('api_status') == 'unavailable':
                content.append(Paragraph(
                    "<b>FCC API Unavailable:</b> The FCC's public APIs are currently not accessible (returning 404 errors).",
                    self.styles['Normal']
                ))
                content.append(Spacer(1, 0.1*inch))
                content.append(Paragraph(
                    "This may be due to API changes, maintenance, or access restrictions by the FCC.",
                    self.styles['Normal']
                ))
                content.append(Spacer(1, 0.1*inch))
                content.append(Paragraph(
                    "<b>Alternative Methods:</b>",
                    self.styles['Normal']
                ))
                content.append(Paragraph(
                    "• Visit https://www.fcc.gov/media/radio/am-fm-tv-and-translator-search for facility search",
                    self.styles['Normal']
                ))
                content.append(Paragraph(
                    "• Use https://www.fccdata.org for FCC database access",
                    self.styles['Normal']
                ))
                content.append(Paragraph(
                    "• Check https://www.fcc.gov/licensing-databases for database downloads",
                    self.styles['Normal']
                ))
            else:
                content.append(Paragraph(
                    f"<b>FCC Query Error:</b> {fcc_data['error']}",
                    self.styles['Normal']
                ))
                content.append(Spacer(1, 0.1*inch))
                query_params = fcc_data.get('query_params', {})
                content.append(Paragraph(
                    f"<b>Query Parameters:</b> {query_params.get('lat', 0):.6f}, {query_params.get('lon', 0):.6f} "
                    f"@ {query_params.get('frequency', 0)} MHz ({query_params.get('service', 'Unknown')})",
                    self.styles['Normal']
                ))
            content.append(Spacer(1, 0.3*inch))
            return content

        # Display query information
        query_params = fcc_data.get('query_params', {})
        content.append(Paragraph(
            f"Query performed on {fcc_data.get('query_time', 'Unknown')[:19]}",
            self.styles['Normal']
        ))
        content.append(Paragraph(
            f"Search: {query_params.get('lat', 0):.6f}°, {query_params.get('lon', 0):.6f}° "
            f"@ {query_params.get('frequency', 0)} MHz ({query_params.get('service', 'Unknown')}) "
            f"within {query_params.get('radius_km', 0)} km",
            self.styles['Normal']
        ))
        content.append(Spacer(1, 0.2*inch))

        # Display facilities
        facilities = fcc_data.get('facilities', [])
        if facilities and len(facilities) > 0:
            # Found matching facilities
            for i, facility in enumerate(facilities[:3]):  # Limit to 3 results
                if i > 0:
                    content.append(Spacer(1, 0.2*inch))

                content.append(Paragraph(f"Facility {i+1}", self.styles['SubsectionHeading']))

                # Build facility info table
                facility_data = [
                    ['Call Sign:', facility.get('callSign', 'N/A')],
                    ['Facility ID:', str(facility.get('facilityId', 'N/A'))],
                ]

                # License status fields
                if 'lmsFileNumber' in facility:
                    facility_data.append(['LMS File No:', facility.get('lmsFileNumber', 'N/A')])
                if 'licensedDate' in facility:
                    facility_data.append(['Licensed Date:', facility.get('licensedDate', 'N/A')])
                if 'lmsApplicationId' in facility:
                    facility_data.append(['LMS Application ID:', facility.get('lmsApplicationId', 'N/A')])
                if 'licenseStatus' in facility:
                    facility_data.append(['License Status:', facility.get('licenseStatus', 'N/A')])

                facility_data.extend([
                    ['Frequency:', f"{facility.get('frequency', 'N/A')} MHz"],
                    ['City:', facility.get('city', 'N/A')],
                    ['State:', facility.get('state', 'N/A')],
                ])

                # ERP with multiple units
                if 'erp' in facility:
                    erp_val = facility.get('erp', 'N/A')
                    erp_unit = facility.get('erpUnit', 'W')
                    erp_display = f"{erp_val} {erp_unit}"

                    if 'erpWatts' in facility:
                        erp_w = facility['erpWatts']
                        erp_dbm = facility.get('erpDbm', 'N/A')
                        erp_display += f" ({erp_w:.0f} W, {erp_dbm:.1f} dBm)"

                    facility_data.append(['ERP:', erp_display])

                # HAAT
                if 'haat' in facility:
                    haat_val = facility.get('haat', 'N/A')
                    haat_unit = facility.get('haatUnit', 'm')
                    facility_data.append(['HAAT:', f"{haat_val} {haat_unit}"])

                # AGL (if available)
                if 'agl' in facility:
                    agl_m = facility.get('agl', 0)
                    agl_ft = facility.get('aglFeet', 0)
                    facility_data.append(['AGL:', f"{agl_m} m ({agl_ft:.1f} ft)"])

                # Coordinates
                if 'latitude' in facility and 'longitude' in facility:
                    facility_data.append(['Coordinates:', f"{facility.get('latitude', 0):.6f}°, {facility.get('longitude', 0):.6f}°"])

                # FCC URL
                if 'fccUrl' in facility:
                    facility_data.append(['FCC Record:', facility['fccUrl']])

                facility_table = Table(facility_data, colWidths=[1.5*inch, 4*inch])
                facility_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                    ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))

                content.append(facility_table)

        else:
            content.append(Paragraph(
                "<b>No Facilities Found:</b> The FCC database query did not return any matching facilities.",
                self.styles['Normal']
            ))

        content.append(Spacer(1, 0.3*inch))

        return content

    def _build_station_section(self, sections):
        """Build station information section"""
        content = []

        content.append(Paragraph("Station Information", self.styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))

        # Get configuration
        tx_lat = self.config.get('tx_lat', 0)
        tx_lon = self.config.get('tx_lon', 0)
        frequency = self.config.get('frequency', 0)
        erp = self.config.get('erp', 0)
        tx_power = self.config.get('tx_power', 40)
        system_loss_db = self.config.get('system_loss_db', 0)
        system_gain_db = self.config.get('system_gain_db', 0)
        height = self.config.get('height', 0)
        max_distance = self.config.get('max_distance', 50)
        pattern_name = self.config.get('pattern_name', 'N/A')
        current_antenna_id = self.config.get('current_antenna_id', None)

        # Calculate effective ERP (tx_power already in dBm, gains/losses in dB)
        effective_erp = tx_power + system_gain_db - system_loss_db

        # Calculate total system loss (positive value)
        total_loss_db = system_loss_db

        # Build station data
        station_data = [
            ['Frequency:', f"{frequency} MHz"],
            ['Transmitter Power:', f"{tx_power} dBm ({10**((tx_power-30)/10):.1f} W)"],
            ['Total System Loss:', f"{total_loss_db:.2f} dB"],
            ['ERP:', f"{effective_erp:.2f} dBm ({10**((effective_erp-30)/10):.1f} W)"],
            ['Antenna Height:', f"{height} meters AGL"],
            ['Coverage Radius:', f"{max_distance} km"],
        ]

        # Add antenna information if available
        if current_antenna_id:
            from models.antenna_library import AntennaLibrary
            antenna_library = AntennaLibrary()
            antenna_data = antenna_library.get_antenna(current_antenna_id)

            if antenna_data:
                antenna_name = antenna_data.get('name', 'N/A')
                antenna_manufacturer = antenna_data.get('manufacturer', 'N/A')
                antenna_part_number = antenna_data.get('part_number', 'N/A')
                antenna_gain = antenna_data.get('gain', 0)
                antenna_type = antenna_data.get('type', 'N/A')

                station_data.extend([
                    ['Antenna:', f"{antenna_name}"],
                    ['Antenna Manufacturer:', f"{antenna_manufacturer}"],
                    ['Antenna Part Number:', f"{antenna_part_number}"],
                    ['Antenna Gain:', f"{antenna_gain:+.1f} dBi"],
                    ['Antenna Type:', f"{antenna_type}"],
                ])
        else:
            station_data.append(['Antenna Pattern:', pattern_name])

        station_data.append(['Transmitter Location:', f"{tx_lat:.6f}°, {tx_lon:.6f}°"])

        station_table = Table(station_data, colWidths=[2*inch, 4*inch])
        station_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))

        content.append(station_table)

        return content

    def _build_rf_chain_section(self, sections):
        """Build RF chain information section"""
        content = []

        content.append(Paragraph("RF System Configuration", self.styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))

        # Get RF chain from config
        rf_chain = self.config.get('rf_chain', [])
        frequency = self.config.get('frequency', 88.5)  # For cable loss calculation

        if not rf_chain:
            content.append(Paragraph("No RF chain configured.", self.styles['Normal']))
            return content

        # Build RF chain table
        table_data = [['Part Name', 'Manufacturer', 'Type', 'Specs', 'dB Change']]

        total_loss = 0
        total_gain = 0

        for component, length_ft in rf_chain:
            component_type = component.get('component_type', 'Unknown')
            model = component.get('model', 'N/A')
            manufacturer = component.get('manufacturer', 'N/A')

            # Calculate specs and dB change based on component type
            specs = 'N/A'
            db_change = 0

            if component_type == 'cable':
                loss_db = self.component_library.interpolate_cable_loss(component, frequency, length_ft)
                specs = f"{length_ft:.1f} ft"
                db_change = -loss_db  # Loss is negative change
                total_loss += loss_db
            elif component_type == 'transmitter':
                power_watts = component.get('transmit_power_watts', component.get('power_output_watts', 0))
                efficiency = component.get('efficiency_percent', 'N/A')
                specs = f"{power_watts}W"
                if efficiency != 'N/A':
                    specs += f" @ {efficiency}%"
                db_change = 0  # No dB change from transmitter
            elif component_type == 'antenna':
                # Antennas provide gain
                gain = component.get('gain_dbi', 0)
                specs = f"{gain} dBi"
                db_change = gain  # Gain is positive change
                total_gain += gain
            elif component_type in ['isolator', 'circulator']:
                # Isolators and circulators
                isolation = component.get('isolation_db', 'N/A')
                insertion_loss = component.get('insertion_loss_db', 0)
                port_config = component.get('port_configuration', '')
                specs = f"ISO: {isolation} dB, IL: {insertion_loss} dB"
                if port_config:
                    specs += f" ({port_config})"
                db_change = -insertion_loss  # Loss is negative change
                total_loss += insertion_loss
            elif component_type in ['combiner', 'filter', 'passive']:
                # Combiners, filters, and other passive components
                if 'insertion_loss_db' in component:
                    loss_db = component['insertion_loss_db']
                    rejection = component.get('rejection_db', '')
                    specs = f"IL: {loss_db} dB"
                    if rejection:
                        specs += f", REJ: {rejection} dB"
                    db_change = -loss_db  # Loss is negative change
                    total_loss += loss_db
                else:
                    specs = "N/A"
                    db_change = 0
            elif component_type == 'amplifier':
                # Amplifiers provide gain
                gain = component.get('gain_dbi', 0)
                specs = f"{gain} dBi"
                db_change = gain  # Gain is positive change
                total_gain += gain
            elif 'insertion_loss_db' in component:
                # Generic fallback for any component with insertion loss
                loss_db = component['insertion_loss_db']
                specs = f"IL: {loss_db} dB"
                db_change = -loss_db  # Loss is negative change
                total_loss += loss_db

            table_data.append([model, manufacturer, component_type.title(), specs, f"{db_change:+.2f}"])

        # Add antenna at the end if selected
        current_antenna_id = self.config.get('current_antenna_id', None)
        if current_antenna_id:
            from models.antenna_library import AntennaLibrary
            antenna_library = AntennaLibrary()
            antenna_data = antenna_library.get_antenna(current_antenna_id)

            if antenna_data:
                antenna_name = antenna_data.get('name', 'N/A')
                antenna_manufacturer = antenna_data.get('manufacturer', 'N/A')
                antenna_gain = antenna_data.get('gain', 0)
                antenna_type = antenna_data.get('type', 'N/A')

                table_data.append([
                    antenna_name,
                    antenna_manufacturer,
                    'Antenna',
                    f"{antenna_type}, {antenna_gain:+.1f} dBi",
                    f"{antenna_gain:+.2f}"
                ])
                total_gain += antenna_gain

        # Add totals row
        net_change = total_gain - total_loss
        table_data.append(['TOTAL SYSTEM', '', '', '', f"{net_change:+.2f}"])

        # Create table
        rf_table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1.5*inch, 1*inch])
        rf_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),  # Header row
            ('FONT', (-1, 0), (-1, -1), 'Helvetica-Bold', 9),  # Total row
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),  # dB Change column
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
            ('BACKGROUND', (-1, 0), (-1, -1), colors.lightgrey),  # Total background
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        content.append(rf_table)

        # Add summary note
        if sections.get('loss_budget'):
            content.append(Spacer(1, 0.2*inch))
            content.append(Paragraph(
                f"System Summary: {total_loss:.2f} dB loss, {total_gain:.2f} dB gain, "
                f"Net {net_change:+.2f} dB change from reference.",
                self.styles['Normal']
            ))

        return content

    def _build_antenna_section(self):
        """Build antenna information section with azimuth gain/loss data"""
        content = []

        content.append(Paragraph("Antenna Information", self.styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))

        # Get antenna information
        pattern_name = self.config.get('pattern_name', 'N/A')
        current_antenna_id = self.config.get('current_antenna_id', None)

        # Basic antenna info
        antenna_info = [
            ['Antenna Pattern:', pattern_name],
            ['Type:', 'Directional' if current_antenna_id else 'Omnidirectional'],
        ]

        # Try to get detailed antenna data from library
        antenna_details = None
        if current_antenna_id:
            antenna_details = self.antenna_library.get_antenna(current_antenna_id)

        if antenna_details:
            antenna_info.extend([
                ['Manufacturer:', antenna_details.get('manufacturer', 'N/A')],
                ['Model:', antenna_details.get('model', 'N/A')],
                ['Gain:', f"{antenna_details.get('gain', 0)} dBi"],
                ['Frequency Range:', f"{antenna_details.get('frequency_range', 'N/A')}"],
            ])

        # Create basic info table
        info_table = Table(antenna_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 0.2*inch))

        # Check if we have actual imported antenna pattern data
        has_pattern_data = (self.antenna_pattern and
                           hasattr(self.antenna_pattern, 'azimuth_pattern') and
                           self.antenna_pattern.azimuth_pattern)

        if has_pattern_data:
            # Use actual imported radial loss breakdown
            content.append(Paragraph("Azimuth Pattern - Imported Radial Loss Breakdown", self.styles['SubsectionHeading']))
            content.append(Spacer(1, 0.1*inch))

            # Get all angles from the imported pattern, sorted
            all_angles = sorted(self.antenna_pattern.azimuth_pattern.keys())
            max_gain = max(self.antenna_pattern.azimuth_pattern.values()) if all_angles else 0

            # Sample every 10 degrees for the table (to keep it manageable)
            azimuth_angles = [angle for angle in range(0, 360, 10)]
            azimuth_data = [['Azimuth (°)', 'Gain (dBi)', 'Relative Loss (dB)']]

            for az in azimuth_angles:
                # Get interpolated gain from actual pattern
                gain = self.antenna_pattern.get_gain(az)
                relative_loss = max_gain - gain if max_gain > 0 else 0
                azimuth_data.append([str(az), f"{gain:.1f}", f"-{relative_loss:.1f}" if relative_loss > 0 else "0.0"])

            azimuth_table = Table(azimuth_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
            azimuth_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            content.append(azimuth_table)

            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(
                f"<b>Pattern Data:</b> Imported antenna pattern with {len(all_angles)} data points. "
                f"Maximum gain: {max_gain:.1f} dBi. "
                "Gain values shown are relative to isotropic (dBi). "
                "Relative Loss shows dB below maximum gain.",
                self.styles['Normal']
            ))
        else:
            # No imported pattern data available
            content.append(Paragraph("Azimuth Pattern (Horizontal Gain/Loss)", self.styles['SubsectionHeading']))
            content.append(Spacer(1, 0.1*inch))

            content.append(Paragraph(
                "<b>Note:</b> No imported antenna pattern data available for this project. "
                "To include detailed radial loss breakdown, import an antenna pattern using "
                "Antenna → Import Antenna Pattern.",
                self.styles['Normal']
            ))
            content.append(Spacer(1, 0.1*inch))

            # Show simplified pattern for basic antennas
            azimuth_angles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
            azimuth_data = [['Azimuth (°)', 'Gain (dBi)', 'Relative Loss (dB)']]

            max_gain = antenna_details.get('gain', 0) if antenna_details else 0

            for az in azimuth_angles:
                # Simplified pattern
                if current_antenna_id and antenna_details:
                    if az == 0:
                        gain = max_gain
                    else:
                        gain = max_gain - 10 - (az % 180) * 0.1
                        gain = max(0, gain)
                else:
                    # Omnidirectional
                    gain = 0

                relative_loss = max_gain - gain if max_gain > 0 else 0
                azimuth_data.append([str(az), f"{gain:.1f}", f"-{relative_loss:.1f}" if relative_loss > 0 else "0.0"])

            azimuth_table = Table(azimuth_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
            azimuth_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            content.append(azimuth_table)

            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(
                "Note: Values shown are approximations. Import actual antenna pattern for precise data.",
                self.styles['Normal']
            ))

        return content

    def _build_coverage_section(self, coverage_images, zoom_levels):
        """Build coverage maps section"""
        content = []

        content.append(Paragraph("Coverage Analysis", self.styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))

        # Add each coverage image
        for img_path in coverage_images:
            # Extract zoom level from filename if possible
            filename = os.path.basename(img_path)

            content.append(Paragraph(f"Coverage Map: {filename}", self.styles['SubsectionHeading']))

            # Add image (resize to fit page)
            try:
                img = Image(img_path, width=6*inch, height=4.5*inch)
                content.append(img)
                content.append(Spacer(1, 0.2*inch))
            except Exception as e:
                content.append(Paragraph(f"Error loading image: {str(e)}", self.styles['Normal']))

            content.append(PageBreak())

        return content
