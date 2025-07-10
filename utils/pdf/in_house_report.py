import pandas as pd
from fpdf import XPos, YPos
import utils.pdf.chart as ct
from utils.pdf.base_pdf import BasePDFReport


class InHousePDFReport(BasePDFReport):
    """
    Specialized PDF report class for In-House reports.
    Inherits common functionality from BasePDFReport and implements
    In-House specific report generation.
    """
    
    def __init__(self, years, df_inhouse, boundaries):
        """
        Initialize the In-House PDF report.
        
        Args:
            years (list): A list containing start and end years for the report period.
            df_inhouse (pandas.DataFrame): DataFrame containing in-house data.
            boundaries (list): A list of boundary percentages for abnormality detection.
        """
        super().__init__()
        self.years = years
        self.df_inhouse = df_inhouse
        self.boundaries = boundaries
    
    def generate(self):
        """
        Generate the In-House PDF report.
        
        Returns:
            bytes: The generated PDF as bytes.
        """
        # Add a new page and report header
        self.pdf.add_page()
        self.add_date_to_header()
        
        # Add the "In House" section title
        self.add_section_title("In House")
        
        # Prepare data for the data section
        in_house_abnormal = self.df_inhouse["Status Abnormal"].value_counts()
        in_house_explanation = self.df_inhouse["Explanation Status"].value_counts()
        
        in_house_left_stats = [
            ("Approved", in_house_explanation.get("Approved", 0)),
            ("Disapproved", in_house_explanation.get("Disapproved", 0)),
            ("Awaiting", in_house_explanation.get("Awaiting", 0)),
        ]
        
        in_house_right_stats = [
            ("Abnormal", in_house_abnormal.get("Abnormal", 0)),
            ("Normal", in_house_abnormal.get("Normal", 0)),
        ]
        
        # Add the data section with explanation status and abnormal numbers
        self.add_data_section(in_house_left_stats, in_house_right_stats, self.boundaries[0])
        
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
        
        # Return the generated PDF
        return self.output()

