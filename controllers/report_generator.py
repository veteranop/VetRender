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


class ReportGenerator:
    """Generates PDF reports for RF coverage analysis"""

    def __init__(self, config_manager, fcc_api_handler):
        """Initialize report generator

        Args:
            config_manager: Configuration manager instance
            fcc_api_handler: FCC API handler instance
        """
        self.config = config_manager
        self.fcc_api = fcc_api_handler
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
            ['ERP:', f"{erp} dBW"],
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
        """Build FCC information section"""
        content = []

        content.append(Paragraph("FCC Filing Information", self.styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))

        # Query FCC database
        tx_lat = self.config.get('tx_lat', 0)
        tx_lon = self.config.get('tx_lon', 0)
        frequency = self.config.get('frequency', 0)

        # Determine service type based on frequency
        if 88 <= frequency <= 108:
            service = 'FM'
        elif 535 <= frequency <= 1705:
            service = 'AM'
        else:
            service = 'FM'  # Default

        # Try to query FCC API - handle gracefully if it fails
        facilities = None
        try:
            facilities = self.fcc_api.search_by_coordinates_and_frequency(
                tx_lat, tx_lon, frequency, service=service, radius_km=5
            )
        except Exception as e:
            print(f"FCC API query failed: {e}")
            # Continue - we'll show the manual lookup message instead

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
                    ['Service:', facility.get('service', 'N/A')],
                    ['Frequency:', f"{facility.get('frequency', 'N/A')} MHz"],
                    ['City:', facility.get('city', 'N/A')],
                    ['State:', facility.get('state', 'N/A')],
                    ['Licensee:', facility.get('licensee', 'N/A')],
                ]

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
            # No facilities found or API unavailable
            content.append(Paragraph(
                "<b>Note:</b> FCC database query did not return results. "
                "The FCC Public Files API may be unavailable or the facility may not be in the database.",
                self.styles['Normal']
            ))
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(
                f"<b>Search Parameters:</b> Coordinates {tx_lat:.6f}, {tx_lon:.6f}, "
                f"Frequency {frequency} MHz, Service {service}",
                self.styles['Normal']
            ))
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(
                "<b>Manual Lookup:</b> Visit <font color='blue'><u>https://publicfiles.fcc.gov</u></font> "
                "or <font color='blue'><u>https://fccdata.org</u></font> to search for FCC filing information.",
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
        height = self.config.get('height', 0)
        max_distance = self.config.get('max_distance', 50)
        pattern_name = self.config.get('pattern_name', 'N/A')

        station_data = [
            ['Frequency:', f"{frequency} MHz"],
            ['ERP:', f"{erp} dBW ({10**(erp/10):.2f} watts)"],
            ['Antenna Height:', f"{height} meters AGL"],
            ['Coverage Radius:', f"{max_distance} km"],
            ['Antenna Pattern:', pattern_name],
            ['Transmitter Location:', f"{tx_lat:.6f}°, {tx_lon:.6f}°"],
        ]

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

        if not rf_chain:
            content.append(Paragraph("No RF chain configured.", self.styles['Normal']))
            return content

        # Build RF chain summary
        for i, (component, quantity) in enumerate(rf_chain):
            component_type = component.get('component_type', 'Unknown')
            model = component.get('model', 'N/A')

            content.append(Paragraph(f"{i+1}. {component_type.title()}: {model}",
                                   self.styles['SubsectionHeading']))

            # Component details
            details = []

            if component_type == 'transmitter':
                details.append(['Power Output:', f"{component.get('power_output_watts', 'N/A')} watts"])
                details.append(['Efficiency:', f"{component.get('efficiency_percent', 'N/A')}%"])
                details.append(['Frequency Range:', f"{component.get('frequency_range_mhz', ['N/A', 'N/A'])[0]}-{component.get('frequency_range_mhz', ['N/A', 'N/A'])[1]} MHz"])

            elif component_type == 'cable':
                details.append(['Type:', component.get('model', 'N/A')])
                details.append(['Length:', f"{component.get('length_feet', 0)} feet"])
                details.append(['Loss @ Frequency:', f"{component.get('loss_db', 'N/A')} dB"])

            elif component_type == 'antenna':
                details.append(['Gain:', f"{component.get('gain_dbi', 'N/A')} dBi"])
                details.append(['Pattern:', component.get('pattern', 'N/A')])
                details.append(['Frequency Range:', f"{component.get('frequency_range_mhz', ['N/A', 'N/A'])[0]}-{component.get('frequency_range_mhz', ['N/A', 'N/A'])[1]} MHz"])

            if details:
                details_table = Table(details, colWidths=[1.5*inch, 4*inch])
                details_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                    ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                content.append(details_table)

            content.append(Spacer(1, 0.15*inch))

        # Add loss budget if requested
        if sections.get('loss_budget'):
            content.append(Paragraph("Loss Budget", self.styles['SubsectionHeading']))

            # Calculate total losses
            total_cable_loss = 0
            total_gain = 0

            for component, quantity in rf_chain:
                if component.get('component_type') == 'cable':
                    total_cable_loss += component.get('loss_db', 0)
                elif component.get('component_type') == 'antenna':
                    total_gain += component.get('gain_dbi', 0)

            budget_data = [
                ['Cable Loss:', f"-{total_cable_loss:.2f} dB"],
                ['Antenna Gain:', f"+{total_gain:.2f} dB"],
                ['Net Gain:', f"{total_gain - total_cable_loss:.2f} dB"],
            ]

            budget_table = Table(budget_data, colWidths=[2*inch, 2*inch])
            budget_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
            ]))

            content.append(budget_table)

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
