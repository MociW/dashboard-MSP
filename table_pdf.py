from fpdf import FPDF, XPos, YPos
import datetime

class BalanceSheetPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.bg_top = None
        self.bg_bottom = None
        self.set_auto_page_break(auto=False)
        self.add_page()
        self.set_font('helvetica', '', 10)

        # Define column colors (R,G,B)
        self.col_colors = [
            (252, 229, 205),  # Light gray for first column
            (255, 255, 255),  # Light blue for second column
            (252, 229, 205),  # Light green for third column
            (255, 255, 255)   # Light orange for fourth column
        ]

        # Define column widths and positions
        self.col_width = [70, 40, 40, 40]
        self.content_start_y = 0  # Will be set after header is drawn

    def _draw_horizontal_line(self):
        """Helper method to draw a horizontal line at current position"""
        self.set_draw_color(0, 0, 0)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

    def create_table_header(self,rows):
        # Use the pre-defined column widths
        start_y = self.get_y()
        self.bg_top = self.get_y()

        # Draw top border
        self._draw_horizontal_line()

        # Calculate total height needed for header
        header_total_height = 20  # Adjust this value as needed for your text

        # Draw background colors first
        for i in range(len(self.col_width)):
            start_x = self.l_margin + sum(self.col_width[:i])
            self.set_fill_color(*self.col_colors[i])
            self.rect(start_x, start_y, self.col_width[i], header_total_height, style='F')

        # Now add the text on top of the backgrounds
        self.ln(6)

        # Save current position
        x_start = self.get_x()
        y_start = self.get_y()

        # Set font for headers
        self.set_font('helvetica', '', 10)
        self.set_text_color(0, 0, 0)  # Ensure text is visible on colored background

        # Header texts
        rows = [
            '',
            'Movement (Apr 2024 - Oct 2024)',
            'Movement (Oct 2024 - Apr 2025)',
            'Commodity represent'
        ]

        # First column
        self.multi_cell(self.col_width[0], 4, rows[0], border=0, align='L')
        self.set_xy(x_start + self.col_width[0], y_start)  # Reset position for next column

        # Second column
        self.multi_cell(self.col_width[1], 4, rows[1], border=0, align='L')
        self.set_xy(x_start + self.col_width[0] + self.col_width[1], y_start)  # Reset position

        # Third column
        self.multi_cell(self.col_width[2], 4, rows[2], border=0, align='L')
        self.set_xy(x_start + self.col_width[0] + self.col_width[1] + self.col_width[2], y_start)  # Reset position

        # Fourth column (will move to next line automatically)
        self.multi_cell(self.col_width[3], 4, rows[3], border=0, align='L')

        # Position cursor for the next content
        self.set_y(start_y + header_total_height)

        # Draw bottom borderline
        self._draw_horizontal_line()

    def add_section(self, title, rows, is_final_section=False):
        row_height = 5
        start_y = self.get_y()

        # Calculate total height needed for section
        header_total_height = len(rows) * 10 + 6  # Adjust this value as needed for your text

        # Draw background colors first
        for i in range(len(self.col_width)):
            start_x = self.l_margin + sum(self.col_width[:i])
            self.set_fill_color(*self.col_colors[i])
            self.rect(start_x, start_y, self.col_width[i], header_total_height, style='F')

        # Section title
        self.ln(4)
        if title:
            self.set_font('helvetica', 'B', 10)
            self.cell(0, row_height, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)

        # Data rows
        for row in rows:
            self.set_font('helvetica', '', 10)

            # Print cell text on top of the background
            self.cell(self.col_width[0], row_height, row[0], align='L', border=0)
            self.cell(self.col_width[1], row_height, row[1] if len(row) > 1 else '', align='C', border=0)
            self.cell(self.col_width[2], row_height, row[2] if len(row) > 2 else '', align='C', border=0)
            self.cell(self.col_width[3], row_height, row[3] if len(row) > 3 else '', align='L', border=0,
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Draw a line after the section
        self.ln(4)

    def add_section_with_subtitle(self, title, rows, is_final_section=False):
        row_height = 5
        start_y = self.get_y()

        # Calculate total height needed for section
        header_total_height = len(rows) * 10 + len(set([row[0] for row in rows])) +1 # Adjust this value as needed for your text

        # Draw background colors first
        for i in range(len(self.col_width)):
            start_x = self.l_margin + sum(self.col_width[:i])
            self.set_fill_color(*self.col_colors[i])
            self.rect(start_x, start_y, self.col_width[i], header_total_height, style='F')

        # Section title
        self.ln(4)
        if title:
            self.set_font('helvetica', 'B', 10)
            self.cell(0, row_height, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(3)

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
            # Material name (bold) with background
            x_start = self.l_margin
            y_start = self.get_y()

            self.set_font('helvetica', 'B', 10)
            self.cell(0, row_height, material, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Save initial y position to calculate note placement
            initial_y = self.get_y()

            # Items under this material
            self.set_font('helvetica', '', 10)
            for item in group['items']:
                self.cell(self.col_width[0], row_height, item[0], align='L', border=0)  # Item name
                self.cell(self.col_width[1], row_height, item[1] if len(item) > 1 else '', align='C', border=0)
                self.cell(self.col_width[2], row_height, item[2] if len(item) > 2 else '', align='C', border=0)

                # Empty last column (will be used for the note later)
                self.cell(self.col_width[3], row_height, '', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # If there's a note, place it beside the group spanning from the first to last item
            if group['note']:
                # Calculate the height used by the items
                final_y = self.get_y()
                total_items_height = final_y - initial_y

                # Move back up to the start of the group items
                self.set_y(initial_y)

                # Move to the position for the note
                self.set_x(self.l_margin + self.col_width[0] + self.col_width[1] + self.col_width[2])

                # Add the note using multi_cell with appropriate height
                self.set_font('helvetica', '', 9)
                self.multi_cell(self.col_width[3], 4, group['note'], align='L')

                # Reset position to continue after the group
                self.set_y(final_y)

            self.ln(4)  # Extra space after each material group

    def create_balance_sheet(self):
        self.cell(self.content_start_y, 5, "LSP General Movement")
        self.content_start_y = self.get_y()
        # Header with top border
        self.ln(7)

        headers = [
            '',
            'Movement (Apr 2024 - Oct 2024)',
            'Movement (Oct 2024 - Apr 2025)',
            'Commodity represent'
        ]
        self.create_table_header(headers)
        # Assets section
        exchange_rate = [
            ['IDR/USD', '3.22%', '-0.75%', ''],
            ['IDR/JPY', '-0.73%', '0.11%', ''],
            ['IDR/TB', '1.06%', '4.33%', '']
        ]
        self.add_section('Exchange Rate', exchange_rate)
        self._draw_horizontal_line()

        # Non-financial assets section
        material_rate = [
            ['Steel', 'HRC', '3.21%', '-5.70%', 'Press parts : reinforce, brackets, seat set, steel wheel disc, etc'],
            ['Steel', 'CRC', '1.79%', '-5.70%', 'Press parts : reinforce, brackets, seat set, steel wheel disc, etc'],
            ['Steel', 'GALV', '3.21%', '-5.70%', 'Press parts : reinforce, brackets, seat set, steel wheel disc, etc'],
            ['RESIN', 'Global', '3.21%', '-5.70%',
             'Bumper, Instrument panels, Garnish, Covers, Lamps, Grille, Switches, etc'],
            ['RESIN', 'Non-Global', '3.21%', '-5.70%',
             'Bumper, Instrument panels, Garnish, Covers, Lamps, Grille, Switches, etc'],
            ['ALUMINIUM', 'ADC12', '3.21%', '-5.70%',
             'Alloy Wheel disc, knuckle, hub assy'],
            ['ALUMINIUM', 'AC2C', '3.21%', '-5.70%',
             'Alloy Wheel disc, knuckle, hub assy'],
        ]
        self.add_section_with_subtitle('Material', material_rate, is_final_section=True)
        self._draw_horizontal_line()


def main():
    pdf = BalanceSheetPDF()
    pdf.create_balance_sheet()

    # Save PDF
    pdf.output('balance_sheet.pdf')
    print("Balance sheet PDF created successfully!")


if __name__ == '__main__':
    main()