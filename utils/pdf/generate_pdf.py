from fpdf import FPDF, XPos, YPos
import pandas as pd
from datetime import datetime

import utils.pdf.chart as ct
# import chart as ct


def generate_pdf_report(
    years: list,
    df_inhouse: pd.DataFrame,
    df_outhouse: pd.DataFrame,
    df_packing: pd.DataFrame,
    boundaries,
):
    class ReportPDF(FPDF):
        def header(self):
            self.image("images/toyota.png", 10, 10, 56)
            self.ln(15)

        def footer(self):
            # This method is called automatically for each page
            self.set_y(-15)  # Position at 15 mm from bottom
            self.set_font("montserrat", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f" {self.page_no()}", new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")

    page_params = {
        "format": "A4",
        "orientation": "portrait",
        "width": 210,  # A4 width in mm
        "height": 297,  # A4 height in mm
        "margin": {"left": 10, "right": 10, "top": 10, "bottom": 10},
        "column_gap": 4,
        "box_spacing": 3,
    }

    # Calculate derived layout parameters
    usable_width = page_params["width"] - page_params["margin"]["left"] - page_params["margin"]["right"]
    column_width = usable_width / 2

    # Stats box widths
    three_box_width = (column_width - 30) / 3  # Three stats side by side in left column
    two_box_width = (column_width - 5) / 2  # Two stats side by side for right column

    # Color definitions
    colors = {
        "primary_text": (34, 38, 63),
        "secondary_text": (57, 74, 86),
        "light_text": (150, 150, 150),
        "error_text": (207, 16, 32),
        "fill_color": (231, 232, 231),
        "header_bg": (34, 48, 63),
        "header_text": (231, 232, 231),
        "divider": (180, 180, 180),
    }

    # Create a PDF instance
    pdf = ReportPDF(orientation=page_params["orientation"], format=page_params["format"])
    pdf.set_fill_color(*colors["fill_color"])

    # Add font Style
    pdf.add_font("montserrat", "", "fonts/static/Montserrat-Regular.ttf")
    pdf.add_font("montserrat", "B", "fonts/static/Montserrat-Bold.ttf")
    pdf.add_font("montserrat-medium", "", "fonts/static/Montserrat-Medium.ttf")

    # Helper functions
    def format_large_number(number):
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

    def create_explanation_stat(x, y, title, value):
        pdf.set_xy(x, y + 8)
        pdf.set_font("montserrat", "", 7)
        pdf.set_text_color(*colors["light_text"])
        pdf.cell(three_box_width, 5, title, align="C")

        # Value text (large number with abbreviated suffix)
        pdf.set_xy(x, y + 10)
        pdf.set_font("montserrat", "B", 18)
        pdf.set_text_color(*colors["primary_text"])
        display_value = format_large_number(value)
        pdf.cell(three_box_width, 15, display_value, align="C")

    def create_abnormal_stat(x, y, title, value, box_num=3):
        # Title text (small caps)
        pdf.set_xy(x, y + 8)
        pdf.set_font("montserrat", "", 7)
        pdf.set_text_color(*colors["light_text"])
        if box_num == 3:
            pdf.cell(three_box_width, 5, title, align="C")
        else:
            pdf.cell(two_box_width, 5, title, align="C")

        pdf.set_xy(x, y + 10)
        pdf.set_font("montserrat", "B", 18)
        if value > 0 and (title == "Abnormal Below 5%" or title == "Abnormal Above 5%" or title == "Abnormal"):
            pdf.set_text_color(*colors["error_text"])
        else:
            pdf.set_text_color(*colors["primary_text"])

        display_value = format_large_number(value)
        if box_num == 3:
            pdf.cell(three_box_width, 15, display_value, align="C")
        else:
            pdf.cell(two_box_width, 15, display_value, align="C")

    def add_section_title(title, fill=True):
        pdf.set_font("montserrat", "B", 14)
        if fill:
            pdf.set_fill_color(*colors["header_bg"])
            pdf.set_text_color(*colors["header_text"])
            pdf.cell(0, 10, title, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C", fill=True)
        else:
            pdf.set_text_color(*colors["primary_text"])
            pdf.cell(0, 10, title, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    def add_data_section(left_stats, right_stats):
        pdf.ln(6)
        start_y = pdf.get_y()

        # LEFT COLUMN - Set the title
        left_x = page_params["margin"]["left"]
        pdf.set_xy(left_x, start_y)
        pdf.set_font("montserrat", "B", 12)
        pdf.set_text_color(*colors["primary_text"])
        pdf.cell(column_width, 0, "Explanation Status", border=0, align="C")

        # Create stats for left column
        stat_y = start_y
        for i, (title, value) in enumerate(left_stats):
            stat_x = left_x + i * (three_box_width + page_params["box_spacing"]) + 8
            create_explanation_stat(stat_x, stat_y, title, value)

        # RIGHT COLUMN - Set the title
        right_x = page_params["margin"]["left"] + column_width + page_params["column_gap"]
        pdf.set_xy(right_x, start_y)
        pdf.set_font("montserrat", "B", 12)
        pdf.set_text_color(*colors["primary_text"])
        pdf.cell(column_width, 0, "Abnormal Number", border=0, align="C")

        for i, (title, value) in enumerate(right_stats):
            if len(right_stats) == 2:  # First two stats side by side
                stat_x = right_x + i * (two_box_width + page_params["box_spacing"]) + 8
            if len(right_stats) == 3:  # Third stat below
                stat_x = right_x + i * (three_box_width + page_params["box_spacing"]) + 12
            create_abnormal_stat(stat_x, stat_y, title, value)

        abnormal_section_end_y = stat_y + 35
        pdf.set_xy(right_x, start_y + 30)
        pdf.set_font("montserrat", "", 7)
        pdf.set_text_color(*colors["light_text"])
        pdf.set_y(abnormal_section_end_y - 10)
        pdf.set_x(right_x + 5)
        abnormal_description = "Abnormal Number indicator shows Normal entries that meet expected data standards and Abnormal entries that require review due to unusual values or patterns."
        pdf.multi_cell(column_width - 15, 3, abnormal_description)

        status_section_end_y = stat_y + 35
        pdf.set_xy(page_params["margin"]["left"], stat_y + 30)
        pdf.set_font("montserrat", "", 7)
        pdf.set_text_color(*colors["light_text"])
        pdf.set_y(status_section_end_y - 10)
        pdf.set_x(page_params["margin"]["left"])
        status_description = "This indicator shows the approval status of item changes as Approved (authorized), Disapproved (rejected), or Awaiting (pending review), tracking how inventory modifications progress through the approval workflow."
        pdf.multi_cell(column_width - 10, 3, status_description)

        section_end_y = pdf.get_y() + 5
        divider_x = page_params["margin"]["left"] + column_width
        pdf.set_draw_color(*colors["divider"])
        pdf.line(divider_x, start_y, divider_x, section_end_y)

        return section_end_y

    # ==============In House======================
    pdf.add_page()

    pdf.ln(-15)
    pdf.set_text_color(*colors["primary_text"])
    pdf.set_font("montserrat", "B", 18)
    report_title = "ABNORMALITY DATA REPORT"
    pdf.cell(0, 32, report_title, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

    pdf.set_text_color(*colors["secondary_text"])
    pdf.set_font("montserrat", "B", 14)
    report_date_range = f"Aug {years[0]} - {years[1]}"
    pdf.ln(-10)
    pdf.cell(0, 0, report_date_range, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

    pdf.ln(4)
    pdf.set_font("montserrat", "", 8)
    pdf.set_text_color(*colors["light_text"])
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d %b %Y").upper()
    pdf.cell(0, 6, formatted_date, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    add_section_title("In House")

    in_house_abnormal = df_inhouse["Status Abnormal"].value_counts()
    in_house_explanation = df_inhouse["Explanation Status"].value_counts()

    in_house_left_stats = [
        ("Approved", in_house_explanation.get("Approved", 0)),
        ("Disapproved", in_house_explanation.get("Disapproved", 0)),
        ("Awaiting", in_house_explanation.get("Awaiting", 0)),
    ]

    in_house_right_stats = [
        ("Abnormal", in_house_abnormal.get("Abnormal", 0)),
        ("Normal", in_house_abnormal.get("Normal", 0)),
    ]

    add_data_section(in_house_left_stats, in_house_right_stats)

    pdf.ln(8)
    pdf.set_font("montserrat", "B", 12)
    pdf.set_text_color(34, 38, 63)
    distribution_title = "Distribution Abnormal Number"
    pdf.cell(0, 10, distribution_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    single_pie_chart = ct.single_pie_chart(
        df=df_inhouse, boundaries=boundaries, column_status="Total Cost Status", title="Total Cost"
    )
    x_position = (pdf.epw - pdf.eph / 4) / 2
    pdf.image(single_pie_chart, x=x_position, w=pdf.epw / 2.5)

    grouped_pie_charts = ct.grouped_pie_chart(df=df_inhouse, boundaries=boundaries)
    pdf.image(grouped_pie_charts, w=pdf.epw)

    distribution_description = "This pie chart displays the proportion of Normal entries versus Abnormal entries in the dataset, helping to visualize the overall data quality and identify potential areas requiring further investigation."
    pdf.set_font("montserrat", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.set_y(pdf.get_y() + 5)
    pdf.set_x(page_params["margin"]["left"])
    pdf.multi_cell(page_params["width"] - 60, 3, distribution_description)

    # ==============Out House======================
    pdf.add_page()

    pdf.set_font("montserrat", "", 8)
    pdf.set_text_color(*colors["light_text"])
    pdf.cell(0, 6, formatted_date, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    add_section_title("In House")

    out_house_abnormal = df_outhouse["Status"].value_counts()
    out_house_explanation = df_outhouse["Explanation Status"].value_counts()

    out_house_left_stats = [
        ("Approved", out_house_explanation.get("Approved", 0)),
        ("Disapproved", out_house_explanation.get("Disapproved", 0)),
        ("Awaiting", out_house_explanation.get("Awaiting", 0)),
    ]

    out_house_right_stats = [
        ("Abnormal Below -5%", out_house_abnormal.get("Abnormal Below -5%", 0)),
        ("Normal", out_house_abnormal.get("Normal", 0)),
        ("Abnormal Above 5%", out_house_abnormal.get("Abnormal Above 5%", 0)),
    ]

    add_data_section(out_house_left_stats, out_house_right_stats)

    pdf.ln(8)
    pdf.set_font("montserrat", "B", 12)
    pdf.set_text_color(34, 38, 63)
    distribution_title = "Distribution Abnormal Number in Out House"
    pdf.cell(0, 10, distribution_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    start_y = pdf.get_y() + page_params["margin"]["top"]
    x_position = (column_width) / 4
    pie_chart_image = ct.single_pie_chart(
        df=df_outhouse, boundaries=boundaries, column_status="Status", title="Out House Cost", legend_param=True
    )
    pdf.image(pie_chart_image, w=pdf.eph / 4, x=x_position)

    section_end_y = pdf.get_y() - (page_params["margin"]["top"] * 2)
    divider_x = page_params["margin"]["left"] + column_width
    pdf.set_draw_color(180, 180, 180)
    pdf.line(divider_x, start_y, divider_x, section_end_y)

    pdf.set_font("montserrat", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.set_y(start_y + 5)
    pdf.set_x(divider_x + 10)
    text_distribution_abnormal_out_house = "This pie chart illustrates the proportion of Normal versus Abnormal entries specifically for Out House inventory items. The visualization helps identify potential data quality issues in external storage locations by displaying the relative frequency of entries that meet expected standards compared to those requiring review. This information is crucial for maintaining accurate inventory records across all storage locations and prioritizing quality control efforts for out-of-facility items."
    pdf.multi_cell(column_width - 20, 3, text_distribution_abnormal_out_house)

    pdf.ln(30)
    start_y = pdf.get_y()
    pdf.set_xy(page_params["margin"]["left"], start_y)

    pdf.set_font("montserrat", "B", 12)
    pdf.set_text_color(34, 38, 63)
    outhouse_distribution_title = "Number of Abnormal Distributions in Per Source"
    pdf.cell(0, 10, outhouse_distribution_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    bar_chart_group = ct.grouped_bar_chart(df=df_outhouse, source="source", boundaries=boundaries)
    x_position = (pdf.epw - pdf.eph / 2.3) / 2
    pdf.image(bar_chart_group, x=x_position, w=pdf.eph / 2)

    distribution_description = "This bar chart displays the breakdown of Normal and Abnormal entries across different data sources. By comparing the frequency of data quality issues by source, this visualization helps identify which input channels may have higher rates of problematic entries. This analysis enables targeted improvement efforts for specific sources with higher abnormality rates, ultimately improving overall data reliability."
    pdf.set_font("montserrat", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.set_y(pdf.get_y())
    pdf.set_x(page_params["margin"]["left"])
    pdf.multi_cell(page_params["width"] - 30, 3, distribution_description)

    # ======================= Packing ==================================
    pdf.add_page()

    pdf.set_font("montserrat", "", 8)
    pdf.set_text_color(*colors["light_text"])
    pdf.cell(0, 6, formatted_date, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    add_section_title("Packing")

    packing_abnormal = df_packing["Status"].value_counts()
    packing_explanation = df_packing["Explanation Status"].value_counts()

    out_house_left_stats = [
        ("Approved", packing_explanation.get("Approved", 0)),
        ("Disapproved", packing_explanation.get("Disapproved", 0)),
        ("Awaiting", packing_explanation.get("Awaiting", 0)),
    ]

    out_house_right_stats = [
        ("Abnormal Below -5%", packing_abnormal.get("Abnormal Below -5%", 0)),
        ("Normal", packing_abnormal.get("Normal", 0)),
        ("Abnormal Above 5%", packing_abnormal.get("Abnormal Above 5%", 0)),
    ]

    add_data_section(out_house_left_stats, out_house_right_stats)

    pdf.ln(6)
    start_y = pdf.get_y()
    pdf.set_xy(page_params["margin"]["left"], start_y)

    pdf.set_font("montserrat", "B", 12)
    pdf.set_text_color(34, 38, 63)
    outhouse_distribution_title = "Number of Abnormal Distributions in Per Destination"
    pdf.cell(0, 10, outhouse_distribution_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def split_by_destination_codes(df):
        # Count items per destination
        destination_counts = df["destination"].value_counts().reset_index()
        destination_counts.columns = ["destination", "count"]

        # Sort destinations by count in descending order
        sorted_destinations = destination_counts["destination"].tolist()

        # Calculate how many destination codes should go in each group
        codes_per_group = len(sorted_destinations) // 3

        # Create the groups (ensuring all codes are distributed)
        group1_codes = sorted_destinations[:codes_per_group]
        group2_codes = sorted_destinations[codes_per_group : 2 * codes_per_group]
        group3_codes = sorted_destinations[2 * codes_per_group :]  # This will take any remainder

        # Create DataFrames for each group
        df1 = df[df["destination"].isin(group1_codes)]
        df2 = df[df["destination"].isin(group2_codes)]
        df3 = df[df["destination"].isin(group3_codes)]

        return df1, df2, df3

    dataset_packing_1, dataset_packing_2, dataset_packing_3 = split_by_destination_codes(df_packing)

    bar_chart_group = ct.grouped_bar_chart(
        df=dataset_packing_1, source="destination", boundaries=boundaries, legend_param=False
    )
    x_position = (pdf.epw - pdf.eph / 2.1) / 2
    # x_position = page_params["margin"]["left"]

    pdf.image(bar_chart_group, x=x_position, w=pdf.epw / 1.3)

    bar_chart_group = ct.grouped_bar_chart(
        df=dataset_packing_2, source="destination", boundaries=boundaries, legend_param=False
    )
    pdf.image(bar_chart_group, x=x_position, w=pdf.epw / 1.3)

    bar_chart_group = ct.grouped_bar_chart(df=dataset_packing_3, source="destination", boundaries=boundaries)
    pdf.image(bar_chart_group, x=x_position, w=pdf.epw / 1.3)

    destination_bar_chart = "This chart shows data quality issues across different destination. It groups entries as Normal (meeting standards), Abnormal Above (too high), and Abnormal Below (too low). This helps spot which places have specific types of data problems."
    pdf.set_font("montserrat", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.set_y(pdf.get_y())
    pdf.set_x(page_params["margin"]["left"])
    pdf.multi_cell(page_params["width"] - 30, 3, destination_bar_chart)

    return pdf.output(dest="S")
    # pdf.output("abnomal.pdf")


# =====================================================================================================================
# years = ["2023", "2024"]
# full_abnormal_cal_impl = pd.read_excel("in_house_data.xlsx")
# abnormal_cal_out = pd.read_excel("out_house_data.xlsx")
# abnormal_cal_packing = pd.read_excel("packing_data.xlsx")

# generate_pdf_report(
#     years=years,
#     df_inhouse=full_abnormal_cal_impl,
#     df_outhouse=abnormal_cal_out,
#     df_packing=abnormal_cal_packing,
#     boundaries="5",
# )

# primary=(34,48,63)
# secondary=(57,74,86)
# third=(44,100,133)
# fourth=(143,191,218)
# background=(231,232,231)
