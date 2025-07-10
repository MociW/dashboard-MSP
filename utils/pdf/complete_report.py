import pandas as pd
import io
from fpdf import XPos, YPos

import utils.pdf.chart as ct
from utils.pdf.base_pdf import BasePDFReport
from utils.pdf.in_house_report import InHousePDFReport
from utils.pdf.out_house_report import OutHousePDFReport
from utils.pdf.packing_report import PackingPDFReport


class CompletePDFReport(BasePDFReport):
    """
    Comprehensive PDF report class that combines In-House, Out-House, and Packing reports.
    Inherits common functionality from BasePDFReport and reuses the specialized report classes
    to create a complete report with all sections.
    """

    def __init__(self, years, df_inhouse, df_outhouse, df_packing, boundaries):
        """
        Initialize the Complete PDF report.

        Args:
            years (list): A list containing start and end years for the report period.
            df_inhouse (pandas.DataFrame): DataFrame containing in-house data.
            df_outhouse (pandas.DataFrame): DataFrame containing out-house data.
            df_packing (pandas.DataFrame): DataFrame containing packing data.
            boundaries (list): A list of boundary percentages for abnormality detection.
        """
        super().__init__()
        self.years = years
        self.df_inhouse = df_inhouse
        self.df_outhouse = df_outhouse
        self.df_packing = df_packing
        self.boundaries = boundaries

        # Initialize report generators
        self.in_house_report = InHousePDFReport(years, df_inhouse, boundaries)
        self.out_house_report = OutHousePDFReport(years, df_outhouse, boundaries)
        self.packing_report = PackingPDFReport(years, df_packing, boundaries)

    def generate(self):
        """
        Generate the complete PDF report with all sections.

        Returns:
            bytes: The generated PDF as bytes.
        """
        # Add the In-House section (first page with report header)
        self.pdf.add_page()

        self.add_report_header(self.years)
        self.add_section_title("General Movement")

        self.pdf.ln(4)
        self.pdf.set_text_color(*self.colors["primary_text"])
        self.pdf.set_font('montserrat', '', 10)
        self.pdf.cell(self.content_start_y, 5, "LSP & In House General Movement")
        self.content_start_y = self.pdf.get_y()
        # Header with top border
        self.pdf.ln(7)

        headers = [
            '',
            'Apr 2024 - Oct 2024 Movement',
            'Oct 2024 - Apr 2025 Movement',
            'Commodity represent'
        ]
        self.create_table_header(headers, 12)
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
            ['Steel', 'CRC', '1.79%', '-5.50%', 'Press parts : reinforce, brackets, seat set, steel wheel disc, etc'],
            ['Steel', 'GALV', '0.43%', '-4.30%', 'Press parts : reinforce, brackets, seat set, steel wheel disc, etc'],
            ['RESIN', 'Global', '5.00%', '2.80%',
             'Bumper, Instrument panels, Garnish, Covers, Lamps, Grille, Switches, etc'],
            ['RESIN', 'Non-Global', '4.80%', '2.70%',
             'Bumper, Instrument panels, Garnish, Covers, Lamps, Grille, Switches, etc'],
            ['ALUMINIUM', 'ADC12', '16.20%', '2.17%',
             'Alloy Wheel disc, knuckle, hub assy'],
            ['ALUMINIUM', 'AC2C', '15.20%', '2.04%',
             'Alloy Wheel disc, knuckle, hub assy'],
            ['ALUMINIUM', 'A356', '10.30%', '10.00%',
             'Alloy Wheel disc, knuckle, hub assy'],
            ['RUBBER', 'Rubber', '10.00%', '2.00%',
             'Weatherstrips, Plugs, Anti-vibration'],
            ['LEAD', 'Lead', '-1.10%', '-4.60%',
             'Battery (non HEV)'],
            ['COPPER', 'Copper', '10.10%', '1.03%',
             'Wire Harness, Switches,'],
        ]
        self.add_section_with_subtitle('Material', material_rate)
        self._draw_horizontal_line()
        self.pdf.ln(7)
        self.pdf.cell(self.content_start_y, 5, "Packing General Movement")
        self.content_start_y = self.pdf.get_y()
        self.pdf.ln(7)

        headers = [
            '',
            'Ratio',
            'Movement',
            ''
        ]
        self.create_table_header(headers, 8)

        exchange_rate = [
            ['Material', '61%', '2%', ''],
            ['Labor', '16%', '12%', ''],
            ['Inland', '22%', '1%', ''],
            ['Total', '', '3%', '']
        ]
        self.add_section('Packing', exchange_rate)
        self._draw_horizontal_line()

        self.pdf.add_page()
        self.add_date_to_header()
        self.add_section_title("In House")

        # Prepare data for the In-House section
        in_house_abnormal = self.df_inhouse["Total Cost Status"].value_counts()
        in_house_explanation = self.df_inhouse["Explanation Status"].value_counts()

        in_house_left_stats = [
            ("Approved", in_house_explanation.get("Approved", 0)),
            ("Disapproved", in_house_explanation.get("Disapproved", 0)),
            ("Awaiting", in_house_explanation.get("Awaiting", 0)),
        ]

        in_house_right_stats = [
            (f"Abnormal Below -{self.boundaries[0]}%",
             in_house_abnormal.get(f"Abnormal Below -{self.boundaries[0]}%", 0)),
            ("Normal", in_house_abnormal.get("Normal", 0)),
            (f"Abnormal Above {self.boundaries[0]}%",
             in_house_abnormal.get(f"Abnormal Above {self.boundaries[0]}%", 0)),
        ]

        # Add the data section with explanation status and abnormal numbers
        self.add_data_section(in_house_left_stats, in_house_right_stats, self.boundaries[0])

        # Add the In-House charts using the in_house_report methods
        # We need to refactor the individual methods to avoid PDF generation - for now we'll
        # duplicate the needed code, but ideally we'd refactor the specialized report classes

        # Add the distribution section
        self.pdf.ln(8)
        self.pdf.set_font("montserrat", "B", 12)
        self.pdf.set_text_color(*self.colors["primary_text"])
        distribution_title = "Distribution Abnormal Number"
        self.pdf.cell(0, 10, distribution_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Add the single pie chart
        single_pie_chart = ct.single_pie_chart(
            df=self.df_inhouse,
            boundaries=self.boundaries[0],
            column_status="Total Cost Status",
            title="Total Cost"
        )
        x_position = (self.pdf.epw - self.pdf.eph / 4) / 2
        self.pdf.image(single_pie_chart, x=x_position, w=self.pdf.epw / 2.5)

        # Add the grouped pie charts
        grouped_pie_charts = ct.grouped_pie_chart(df=self.df_inhouse, boundaries=self.boundaries[0])
        self.pdf.image(grouped_pie_charts, w=self.pdf.epw)

        # Add the distribution description
        distribution_description = "This pie chart displays the proportion of Normal entries versus Abnormal entries in the dataset, helping to visualize the overall data quality and identify potential areas requiring further investigation."
        self.pdf.set_font("montserrat", "", 7)
        self.pdf.set_text_color(self.colors["light_text"])
        self.pdf.set_y(self.pdf.get_y() + 5)
        self.pdf.set_x(self.page_params["margin"]["left"])
        self.pdf.multi_cell(self.page_params["width"] - 60, 3, distribution_description)

        # Add the Out-House section
        self.pdf.add_page()
        self.add_date_to_header()
        self.add_section_title("Out House")

        # Prepare data for the Out-House section
        out_house_abnormal = self.df_outhouse["Status"].value_counts()
        out_house_explanation = self.df_outhouse["Explanation Status"].value_counts()

        out_house_left_stats = [
            ("Approved", out_house_explanation.get("Approved", 0)),
            ("Disapproved", out_house_explanation.get("Disapproved", 0)),
            ("Awaiting", out_house_explanation.get("Awaiting", 0)),
        ]

        out_house_right_stats = [
            (f"Abnormal Below -{self.boundaries[1]}%",
             out_house_abnormal.get(f"Abnormal Below -{self.boundaries[1]}%", 0)),
            ("Normal", out_house_abnormal.get("Normal", 0)),
            (f"Abnormal Above {self.boundaries[1]}%",
             out_house_abnormal.get(f"Abnormal Above {self.boundaries[1]}%", 0)),
        ]

        # Add the data section with explanation status and abnormal numbers
        self.add_data_section(out_house_left_stats, out_house_right_stats, self.boundaries[1])

        # Add the Out-House charts and descriptions
        self.pdf.ln(8)
        self.pdf.set_font("montserrat", "B", 12)
        self.pdf.set_text_color(*self.colors["primary_text"])
        distribution_title = "Distribution Abnormal Number in Out House"
        self.pdf.cell(0, 10, distribution_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Add the pie chart with description
        start_y = self.pdf.get_y() + self.page_params["margin"]["top"]
        x_position = (self.column_width) / 4
        pie_chart_image = ct.single_pie_chart(
            df=self.df_outhouse,
            boundaries=self.boundaries[1],
            column_status="Status",
            title="Out House Cost",
            legend_param=True
        )
        self.pdf.image(pie_chart_image, w=self.pdf.eph / 4, x=x_position)

        # Add vertical divider
        section_end_y = self.pdf.get_y() - (self.page_params["margin"]["top"] * 2)
        divider_x = self.page_params["margin"]["left"] + self.column_width
        self.pdf.set_draw_color(*self.colors["divider"])
        self.pdf.line(divider_x, start_y, divider_x, section_end_y)

        # Add description for the pie chart
        self.pdf.set_font("montserrat", "", 7)
        self.pdf.set_text_color(self.colors["light_text"])
        self.pdf.set_y(start_y + 5)
        self.pdf.set_x(divider_x + 10)
        text_distribution_abnormal_out_house = "This pie chart illustrates the proportion of Normal versus Abnormal entries specifically for Out House inventory items. The visualization helps identify potential data quality issues in external storage locations by displaying the relative frequency of entries that meet expected standards compared to those requiring review. This information is crucial for maintaining accurate inventory records across all storage locations and prioritizing quality control efforts for out-of-facility items."
        self.pdf.multi_cell(self.column_width - 20, 3, text_distribution_abnormal_out_house)

        # Add the bar chart section
        self.pdf.ln(30)
        start_y = self.pdf.get_y()
        self.pdf.set_xy(self.page_params["margin"]["left"], start_y)

        self.pdf.set_font("montserrat", "B", 12)
        self.pdf.set_text_color(*self.colors["primary_text"])
        outhouse_distribution_title = "Number of Abnormal Distributions in Per Source"
        self.pdf.cell(0, 10, outhouse_distribution_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Add the bar chart
        bar_chart_group = ct.grouped_bar_chart(df=self.df_outhouse, source="source", boundaries=self.boundaries[1])
        x_position = (self.pdf.epw - self.pdf.eph / 2.3) / 2
        self.pdf.image(bar_chart_group, x=x_position, w=self.pdf.eph / 2)

        # Add description for the bar chart
        distribution_description = "This bar chart displays the breakdown of Normal and Abnormal entries across different data sources. By comparing the frequency of data quality issues by source, this visualization helps identify which input channels may have higher rates of problematic entries. This analysis enables targeted improvement efforts for specific sources with higher abnormality rates, ultimately improving overall data reliability."
        self.pdf.set_font("montserrat", "", 7)
        self.pdf.set_text_color(self.colors["light_text"])
        self.pdf.set_y(self.pdf.get_y())
        self.pdf.set_x(self.page_params["margin"]["left"])
        self.pdf.multi_cell(self.page_params["width"] - 30, 3, distribution_description)

        # Add the Packing section
        self.pdf.add_page()
        self.add_date_to_header()
        self.add_section_title("Packing")

        # Prepare data for the Packing section
        packing_abnormal = self.df_packing["Status"].value_counts()
        packing_explanation = self.df_packing["Explanation Status"].value_counts()

        packing_left_stats = [
            ("Approved", packing_explanation.get("Approved", 0)),
            ("Disapproved", packing_explanation.get("Disapproved", 0)),
            ("Awaiting", packing_explanation.get("Awaiting", 0)),
        ]

        packing_right_stats = [
            (f"Abnormal Below -{self.boundaries[2]}%",
             packing_abnormal.get(f"Abnormal Below -{self.boundaries[2]}%", 0)),
            ("Normal", packing_abnormal.get("Normal", 0)),
            (f"Abnormal Above {self.boundaries[2]}%", packing_abnormal.get(f"Abnormal Above {self.boundaries[2]}%", 0)),
        ]

        # Add the data section with explanation status and abnormal numbers
        self.add_data_section(packing_left_stats, packing_right_stats, self.boundaries[2])

        # Add the distribution by destination section
        self.pdf.ln(6)
        start_y = self.pdf.get_y()
        self.pdf.set_xy(self.page_params["margin"]["left"], start_y)

        self.pdf.set_font("montserrat", "B", 12)
        self.pdf.set_text_color(*self.colors["primary_text"])
        packing_distribution_title = "Number of Abnormal Distributions in Per Destination"
        self.pdf.cell(0, 10, packing_distribution_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Use the Packing helper function to split destinations
        split_by_destination_codes = self.packing_report.split_by_destination_codes
        dataset_packing_1, dataset_packing_2 = split_by_destination_codes(self.df_packing)

        # Add the first group of destination bar chart
        bar_chart_group_1 = ct.grouped_bar_chart_dest(
            df=dataset_packing_1,
            source="destination",
            boundaries=self.boundaries[2],
            legend_param=False
        )
        x_position = (self.pdf.epw - self.pdf.eph / 2.2) / 2
        self.pdf.image(bar_chart_group_1, x=x_position, w=self.pdf.epw / 1.4)

        # Add the second group of destination bar chart
        bar_chart_group_2 = ct.grouped_bar_chart_dest(
            df=dataset_packing_2,
            source="destination",
            boundaries=self.boundaries[2],
            legend_param=True
        )
        self.pdf.image(bar_chart_group_2, x=x_position, w=self.pdf.epw / 1.4)

        # Add description for the destination bar charts
        destination_bar_chart_description = "This chart shows data quality issues across different destination. It groups entries as Normal (meeting standards), Abnormal Above (too high), and Abnormal Below (too low). This helps spot which places have specific types of data problems."
        self.pdf.set_font("montserrat", "", 7)
        self.pdf.set_text_color(self.colors["light_text"])
        self.pdf.set_y(self.pdf.get_y())
        self.pdf.set_x(self.page_params["margin"]["left"])
        self.pdf.multi_cell(self.page_params["width"] - 30, 3, destination_bar_chart_description)

        # Return the generated PDF
        return self.output()
