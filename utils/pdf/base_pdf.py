from fpdf import FPDF, XPos, YPos
import pandas as pd
from datetime import datetime
import io


class BasePDFReport:
    """
    Base class for PDF report generation with common functionality for all report types.
    This class handles PDF initialization, layout, styling, and common helper methods.
    """

    def __init__(self):
        """Initialize the PDF report with default settings."""
        # Define the PDF page parameters
        self.page_params = {
            "format": "A4",
            "orientation": "portrait",
            "width": 210,  # A4 width in mm
            "height": 297,  # A4 height in mm
            "margin": {"left": 10, "right": 10, "top": 10, "bottom": 10},
            "column_gap": 4,
            "box_spacing": 3,
        }

        # Calculate derived layout parameters
        self.usable_width = self.page_params["width"] - self.page_params["margin"]["left"] - self.page_params["margin"][
            "right"]
        self.column_width = self.usable_width / 2

        # Stats box widths
        self.three_box_width = (self.column_width - 30) / 3  # Three stats side by side in left column
        self.two_box_width = (self.column_width - 5) / 2  # Two stats side by side for right column

        # Color definitions
        self.colors = {
            "primary_text": (34, 38, 63),
            "secondary_text": (57, 74, 86),
            "light_text": (0, 0, 0),
            "error_text": (207, 16, 32),
            "fill_color": (231, 232, 231),
            "header_bg": (34, 48, 63),
            "header_text": (231, 232, 231),
            "divider": (180, 180, 180),
        }

        # Create the PDF instance with custom header and footer
        self.pdf = self._create_pdf_instance()
        self.pdf.set_fill_color(*self.colors["fill_color"])

        self.col_colors = [
            (252, 229, 205),  # Light gray for first column
            (255, 255, 255),  # Light blue for second column
            (252, 229, 205),  # Light green for third column
            (255, 255, 255)  # Light orange for fourth column
        ]

        # Define column widths and positions
        self.col_width = [70, 40, 40, 40]
        self.content_start_y = 0

        # Add font styles
        self._add_fonts()

    def _create_pdf_instance(self):
        """Create and return a PDF instance with custom header and footer."""

        class ReportPDF(FPDF):
            def header(self):
                # Use the Toyota logo for the header
                self.image("images/toyota.png", 10, 10, 56)
                self.ln(15)

            def footer(self):
                # This method is called automatically for each page
                self.set_y(-15)  # Position at 15 mm from bottom
                self.set_font("montserrat", "", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f" {self.page_no()}", new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")

        return ReportPDF(orientation=self.page_params["orientation"], format=self.page_params["format"])

    def _add_fonts(self):
        """Add required fonts to the PDF."""
        self.pdf.add_font("montserrat", "", "fonts/static/Montserrat-Regular.ttf")
        self.pdf.add_font("montserrat", "B", "fonts/static/Montserrat-Bold.ttf")
        self.pdf.add_font("montserrat-medium", "", "fonts/static/Montserrat-Medium.ttf")

    def format_large_number(self, number):
        """Format large numbers with K, M, B, T suffixes"""
        if abs(number) >= 1_000_000_000_000:
            return f"{number / 1_000_000_000_000:.2f}T"
        elif abs(number) >= 1_000_000_000:
            return f"{number / 1_000_000_000:.2f}B"
        elif abs(number) >= 1_000_000:
            return f"{number / 1_000_000:.2f}M"
        elif abs(number) >= 100_000:
            return f"{number / 1_000:.1f}K"
        else:
            return f"{number:,.0f}"

    def create_explanation_stat(self, x, y, title, value):
        """Create a statistic box for explanation status."""
        self.pdf.set_xy(x, y + 8)
        self.pdf.set_font("montserrat", "", 7)
        self.pdf.set_text_color(*self.colors["light_text"])
        self.pdf.cell(self.three_box_width, 5, title, align="C")

        # Value text (large number with abbreviated suffix)
        self.pdf.set_xy(x, y + 10)
        self.pdf.set_font("montserrat", "B", 18)
        self.pdf.set_text_color(*self.colors["primary_text"])
        display_value = self.format_large_number(value)
        self.pdf.cell(self.three_box_width, 15, display_value, align="C")

    def create_abnormal_stat(self, x, y, title, value, boundary, box_num=3):
        """Create a statistic box for abnormal data."""
        # Title text (small caps)
        self.pdf.set_xy(x, y + 8)
        self.pdf.set_font("montserrat", "", 7)
        self.pdf.set_text_color(*self.colors["light_text"])
        if box_num == 3:
            self.pdf.cell(self.three_box_width, 5, title, align="C")
        else:
            self.pdf.cell(self.two_box_width, 5, title, align="C")

        self.pdf.set_xy(x, y + 10)
        self.pdf.set_font("montserrat", "B", 18)
        if value > 0 and (
                title == f"Abnormal Below -{boundary}%" or title == f"Abnormal Above {boundary}%" or title == "Abnormal"
        ):
            self.pdf.set_text_color(*self.colors["error_text"])
        else:
            self.pdf.set_text_color(*self.colors["primary_text"])

        display_value = self.format_large_number(value)
        if box_num == 3:
            self.pdf.cell(self.three_box_width, 15, display_value, align="C")
        else:
            self.pdf.cell(self.two_box_width, 15, display_value, align="C")

    def add_section_title(self, title, fill=True):
        """Add a section title to the PDF."""
        self.pdf.set_font("montserrat", "B", 14)
        if fill:
            self.pdf.set_fill_color(*self.colors["header_bg"])
            self.pdf.set_text_color(*self.colors["header_text"])
            self.pdf.cell(0, 10, title, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C", fill=True)
        else:
            self.pdf.set_text_color(*self.colors["primary_text"])
            self.pdf.cell(0, 10, title, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    def add_data_section(self, left_stats, right_stats, boundary):
        """Add a data section with explanation status and abnormal numbers."""
        self.pdf.ln(6)
        start_y = self.pdf.get_y()

        # LEFT COLUMN - Set the title
        left_x = self.page_params["margin"]["left"]
        self.pdf.set_xy(left_x, start_y)
        self.pdf.set_font("montserrat", "B", 12)
        self.pdf.set_text_color(*self.colors["primary_text"])
        self.pdf.cell(self.column_width, 0, "Explanation Status", border=0, align="C")

        # Create stats for left column
        stat_y = start_y
        stat_x = 0
        for i, (title, value) in enumerate(left_stats):
            stat_x = left_x + i * (self.three_box_width + self.page_params["box_spacing"]) + 8
            self.create_explanation_stat(stat_x, stat_y, title, value)

        # RIGHT COLUMN - Set the title
        right_x = self.page_params["margin"]["left"] + self.column_width + self.page_params["column_gap"]
        self.pdf.set_xy(right_x, start_y)
        self.pdf.set_font("montserrat", "B", 12)
        self.pdf.set_text_color(*self.colors["primary_text"])
        self.pdf.cell(self.column_width, 0, "Abnormal Number", border=0, align="C")

        for i, (title, value) in enumerate(right_stats):
            if len(right_stats) == 2:  # First two stats side by side
                stat_x = right_x + i * (self.two_box_width + self.page_params["box_spacing"]) + 8
            if len(right_stats) == 3:  # Third stat below
                stat_x = right_x + i * (self.three_box_width + self.page_params["box_spacing"]) + 12
            self.create_abnormal_stat(stat_x, stat_y, title, value, boundary)

        abnormal_section_end_y = stat_y + 35
        self.pdf.set_xy(right_x, start_y + 30)
        self.pdf.set_font("montserrat", "", 7)
        self.pdf.set_text_color(*self.colors["light_text"])
        self.pdf.set_y(abnormal_section_end_y - 10)
        self.pdf.set_x(right_x + 5)
        abnormal_description = "Abnormal Number indicator shows Normal entries that meet expected data standards and Abnormal entries that require review due to unusual values or patterns."
        self.pdf.multi_cell(self.column_width - 15, 3, abnormal_description)

        status_section_end_y = stat_y + 35
        self.pdf.set_xy(self.page_params["margin"]["left"], stat_y + 30)
        self.pdf.set_font("montserrat", "", 7)
        self.pdf.set_text_color(*self.colors["light_text"])
        self.pdf.set_y(status_section_end_y - 10)
        self.pdf.set_x(self.page_params["margin"]["left"])
        status_description = "This indicator shows the approval status of item changes as Approved (authorized), Disapproved (rejected), or Awaiting (pending review), tracking how inventory modifications progress through the approval workflow."
        self.pdf.multi_cell(self.column_width - 10, 3, status_description)

        section_end_y = self.pdf.get_y() + 5
        divider_x = self.page_params["margin"]["left"] + self.column_width
        self.pdf.set_draw_color(*self.colors["divider"])
        self.pdf.line(divider_x, start_y, divider_x, section_end_y)

        return section_end_y

    def add_report_header(self, years):
        """Add the standard report header with title and date range."""
        self.pdf.ln(-15)
        self.pdf.set_text_color(*self.colors["primary_text"])
        self.pdf.set_font("montserrat", "B", 18)
        report_title = "ABNORMALITY DATA REPORT"
        self.pdf.cell(0, 32, report_title, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

        self.pdf.set_text_color(*self.colors["secondary_text"])
        self.pdf.set_font("montserrat", "B", 14)
        report_date_range = f"Aug {years[0]} - {years[1]}"
        self.pdf.ln(-10)
        self.pdf.cell(0, 0, report_date_range, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

        self.pdf.ln(4)
        self.pdf.set_font("montserrat", "", 8)
        self.pdf.set_text_color(*self.colors["light_text"])
        current_date = datetime.now()
        formatted_date = current_date.strftime("%d %b %Y").upper()
        self.pdf.cell(0, 6, formatted_date, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    def add_date_to_header(self):
        """Add the current date to the page header."""
        current_date = datetime.now()
        formatted_date = current_date.strftime("%d %b %Y").upper()

        self.pdf.set_font("montserrat", "", 8)
        self.pdf.set_text_color(*self.colors["light_text"])
        self.pdf.cell(0, 6, formatted_date, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    def _draw_horizontal_line(self):
        """Helper method to draw a horizontal line at current position"""
        self.pdf.set_draw_color(0, 0, 0)
        self.pdf.line(self.pdf.l_margin, self.pdf.get_y(), self.pdf.w - self.pdf.r_margin, self.pdf.get_y())

    def create_table_header(self, rows, total_height):
        # Use the pre-defined column widths
        start_y = self.pdf.get_y()

        # Draw top border
        self._draw_horizontal_line()

        # Calculate total height needed for header
        header_total_height = total_height  # Adjust this value as needed for your text

        # Draw background colors first
        for i in range(len(self.col_width)):
            start_x = self.pdf.l_margin + sum(self.col_width[:i])
            self.pdf.set_fill_color(*self.col_colors[i])
            self.pdf.rect(start_x, start_y, self.col_width[i], header_total_height, style='F')

        # Now add the text on top of the backgrounds
        self.pdf.ln(2)

        # Save current position
        x_start = self.pdf.get_x()
        y_start = self.pdf.get_y()

        # Set font for headers
        self.pdf.set_font('montserrat-medium', '', 10)
        self.pdf.set_text_color(0, 0, 0)  # Ensure text is visible on colored background

        # First column
        self.pdf.multi_cell(self.col_width[0], 4, rows[0], border=0, align='C')
        self.pdf.set_xy(x_start + self.col_width[0], y_start)  # Reset position for next column

        # Second column
        self.pdf.multi_cell(self.col_width[1], 4, rows[1], border=0, align='C')
        self.pdf.set_xy(x_start + self.col_width[0] + self.col_width[1], y_start)  # Reset position

        # Third column
        self.pdf.multi_cell(self.col_width[2], 4, rows[2], border=0, align='C')
        self.pdf.set_xy(x_start + self.col_width[0] + self.col_width[1] + self.col_width[2], y_start)  # Reset position

        # Fourth column (will move to next line automatically)
        self.pdf.multi_cell(self.col_width[3], 4, rows[3], border=0, align='C')

        # Position cursor for the next content
        self.pdf.set_y(start_y + header_total_height)

        # Draw bottom borderline
        self._draw_horizontal_line()

    def add_section(self, title, rows, is_final_section=False):
        row_height = 4
        start_y = self.pdf.get_y()

        # Calculate total height needed for section
        header_total_height = len(rows) * 8  # Adjust this value as needed for your text

        # Draw background colors first
        for i in range(len(self.col_width)):
            start_x = self.pdf.l_margin + sum(self.col_width[:i])
            self.pdf.set_fill_color(*self.col_colors[i])
            self.pdf.rect(start_x, start_y, self.col_width[i], header_total_height, style='F')

        # Section title
        self.pdf.ln(4)
        if title:
            self.pdf.set_font('montserrat', 'B', 10)
            self.pdf.cell(0, row_height, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(1)

        # Data rows
        for row in rows:
            self.pdf.set_font('montserrat', '', 10)

            # Print cell text on top of the background
            self.pdf.cell(self.col_width[0], row_height, row[0], align='L', border=0)
            self.pdf.cell(self.col_width[1], row_height, row[1] if len(row) > 1 else '', align='C', border=0)
            self.pdf.cell(self.col_width[2], row_height, row[2] if len(row) > 2 else '', align='C', border=0)
            self.pdf.cell(self.col_width[3], row_height, row[3] if len(row) > 3 else '', align='L', border=0,
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Draw a line after the section
        self.pdf.ln(4)

    def add_section_with_subtitle(self, title, rows):
        row_height = 4
        start_y = self.pdf.get_y()

        # Calculate total height needed for section
        header_total_height = len(rows) * 9 + len(
            set([row[0] for row in rows]))

        # Draw background colors first
        for i in range(len(self.col_width)):
            start_x = self.pdf.l_margin + sum(self.col_width[:i])
            self.pdf.set_fill_color(*self.col_colors[i])
            self.pdf.rect(start_x, start_y, self.col_width[i], header_total_height, style='F')

        # Section title
        self.pdf.ln(4)
        if title:
            self.pdf.set_font('montserrat', 'B', 10)
            self.pdf.cell(0, row_height, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(3)

        # Process rows to group by material
        material_groups = {}
        for row in rows:
            material = row[0]
            if material not in material_groups:
                material_groups[material] = {
                    'note': row[4] if len(row) > 4 else '',
                    'items': []
                }
            # Store just the item details (excluding material name)
            material_groups[material]['items'].append(row[1:4])

        # Display data in the requested format
        for material, group in material_groups.items():

            self.pdf.set_font('montserrat', 'B', 10)
            self.pdf.cell(0, row_height, material, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Save initial y position to calculate note placement
            initial_y = self.pdf.get_y()

            # Items under this material
            self.pdf.set_font('montserrat-medium', '', 10)
            for item in group['items']:
                self.pdf.cell(self.col_width[0], row_height, item[0], align='L', border=0)  # Item name
                self.pdf.cell(self.col_width[1], row_height, item[1] if len(item) > 1 else '', align='C', border=0)
                self.pdf.cell(self.col_width[2], row_height, item[2] if len(item) > 2 else '', align='C', border=0)

                # Empty last column (will be used for the note later)
                self.pdf.cell(self.col_width[3], row_height, '', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # If there's a note, place it beside the group spanning from the first to last item
            if group['note']:
                # Calculate the height used by the items
                final_y = self.pdf.get_y()
                total_items_height = final_y - initial_y

                # Move back up to the start of the group items
                self.pdf.set_y(initial_y)

                # Move to the position for the note
                self.pdf.set_x(self.pdf.l_margin + self.col_width[0] + self.col_width[1] + self.col_width[2])

                # Add the note using multi_cell with appropriate height
                self.pdf.set_font('montserrat-medium', '', 9)
                self.pdf.multi_cell(self.col_width[3], 4, group['note'], align='L')

                # Reset position to continue after the group
                self.pdf.set_y(final_y)

            self.pdf.ln(4)  # Extra space after each material group

    def output(self):
        """Generate and return the PDF output."""
        return self.pdf.output()
