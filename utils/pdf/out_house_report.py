import pandas as pd
from fpdf import XPos, YPos

import utils.pdf.chart as ct
from utils.pdf.base_pdf import BasePDFReport


class OutHousePDFReport(BasePDFReport):
    """
    Specialized PDF report class for Out-House reports.
    Inherits common functionality from BasePDFReport and implements
    Out-House specific report generation.
    """
    
    def __init__(self, years, df_outhouse, boundaries):
        """
        Initialize the Out-House PDF report.
        
        Args:
            years (list): A list containing start and end years for the report period.
            df_outhouse (pandas.DataFrame): DataFrame containing out-house data.
            boundaries (list): A list of boundary percentages for abnormality detection.
        """
        super().__init__()
        self.years = years
        self.df_outhouse = df_outhouse
        self.boundaries = boundaries
    
    def generate(self):
        """
        Generate the Out-House PDF report.
        
        Returns:
            bytes: The generated PDF as bytes.
        """
        # Add a new page and date to header
        self.pdf.add_page()
        self.add_date_to_header()
        
        # Add the "Out House" section title
        self.add_section_title("Out House")
        
        # Prepare data for the data section
        out_house_abnormal = self.df_outhouse["Status"].value_counts()
        out_house_explanation = self.df_outhouse["Explanation Status"].value_counts()
        
        out_house_left_stats = [
            ("Approved", out_house_explanation.get("Approved", 0)),
            ("Disapproved", out_house_explanation.get("Disapproved", 0)),
            ("Awaiting", out_house_explanation.get("Awaiting", 0)),
        ]
        
        out_house_right_stats = [
            (f"Abnormal Below -{self.boundaries[1]}%", out_house_abnormal.get(f"Abnormal Below -{self.boundaries[1]}%", 0)),
            ("Normal", out_house_abnormal.get("Normal", 0)),
            (f"Abnormal Above {self.boundaries[1]}%", out_house_abnormal.get(f"Abnormal Above {self.boundaries[1]}%", 0)),
        ]
        
        # Add the data section with explanation status and abnormal numbers
        self.add_data_section(out_house_left_stats, out_house_right_stats, self.boundaries[1])
        
        # Add the distribution section
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
        
        # Return the generated PDF
        return self.output()

