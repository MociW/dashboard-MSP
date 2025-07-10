import pandas as pd
from fpdf import XPos, YPos

import utils.pdf.chart as ct
from utils.pdf.base_pdf import BasePDFReport


class PackingPDFReport(BasePDFReport):
    """
    Specialized PDF report class for Packing reports.
    Inherits common functionality from BasePDFReport and implements
    Packing specific report generation.
    """
    
    def __init__(self, years, df_packing, boundaries):
        """
        Initialize the Packing PDF report.
        
        Args:
            years (list): A list containing start and end years for the report period.
            df_packing (pandas.DataFrame): DataFrame containing packing data.
            boundaries (list): A list of boundary percentages for abnormality detection.
        """
        super().__init__()
        self.years = years
        self.df_packing = df_packing
        self.boundaries = boundaries
    
    def split_by_destination_codes(self, df):
        """
        Split the destination codes into two groups for visualization.
        
        Args:
            df (pandas.DataFrame): DataFrame containing destination data.
            
        Returns:
            tuple: Two DataFrames, each containing a subset of destinations.
        """
        # Count items per destination
        destination_counts = df["destination"].value_counts().reset_index()
        destination_counts.columns = ["destination", "count"]
        
        # Sort destinations by count in descending order
        sorted_destinations = destination_counts["destination"].tolist()
        
        # Calculate how many destination codes should go in each group
        codes_per_group = len(sorted_destinations) // 2
        
        # Create the groups (ensuring all codes are distributed)
        group1_codes = sorted_destinations[:codes_per_group]
        group2_codes = sorted_destinations[codes_per_group: 2 * codes_per_group]
        
        # Create DataFrames for each group
        df1 = df[df["destination"].isin(group1_codes)]
        df2 = df[df["destination"].isin(group2_codes)]
        
        return df1, df2
    
    def generate(self):
        """
        Generate the Packing PDF report.
        
        Returns:
            bytes: The generated PDF as bytes.
        """
        # Add a new page and date to header
        self.pdf.add_page()
        self.add_date_to_header()
        
        # Add the "Packing" section title
        self.add_section_title("Packing")
        
        # Prepare data for the data section
        packing_abnormal = self.df_packing["Status"].value_counts()
        packing_explanation = self.df_packing["Explanation Status"].value_counts()
        
        packing_left_stats = [
            ("Approved", packing_explanation.get("Approved", 0)),
            ("Disapproved", packing_explanation.get("Disapproved", 0)),
            ("Awaiting", packing_explanation.get("Awaiting", 0)),
        ]
        
        packing_right_stats = [
            (f"Abnormal Below -{self.boundaries[2]}%", packing_abnormal.get(f"Abnormal Below -{self.boundaries[2]}%", 0)),
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
        
        # Split the destinations into two groups for better visualization
        dataset_packing_1, dataset_packing_2 = self.split_by_destination_codes(self.df_packing)
        
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

