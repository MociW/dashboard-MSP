from openpyxl import Workbook
from io import BytesIO
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


def convert_to_excel_in_house(df, var_previous, var_current, bounderies):
    # Initialize workbook and worksheet
    wb = Workbook()

    default_sheet = wb.active
    wb.remove(default_sheet)

    positive_threshold_fill = PatternFill(
        start_color="FFCCCC", end_color="FFCCCC", fill_type="solid"
    )  # Light red for values Above bounderies
    negative_threshold_fill = PatternFill(start_color="CCCCFF", end_color="CCCCFF", fill_type="solid")

    ws = wb.create_sheet(title="In House")

    # Populate the worksheet with data from the DataFrame, starting from row 2
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), 3):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)

            # LVA
            if c_idx == 5 and isinstance(value, (int, float)):
                if value > bounderies:
                    cell.fill = positive_threshold_fill
                elif value < -bounderies:
                    cell.fill = negative_threshold_fill
            # Non LVA
            if c_idx == 8 and isinstance(value, (int, float)):
                if value > bounderies:
                    cell.fill = positive_threshold_fill
                elif value < -bounderies:
                    cell.fill = negative_threshold_fill

            # Tooling
            if c_idx == 11 and isinstance(value, (int, float)):
                if value > bounderies:
                    cell.fill = positive_threshold_fill
                elif value < -bounderies:
                    cell.fill = negative_threshold_fill

            # Process Cost
            if c_idx == 14 and isinstance(value, (int, float)):
                if value > bounderies:
                    cell.fill = positive_threshold_fill
                elif value < -bounderies:
                    cell.fill = negative_threshold_fill

            # Total Cost
            if c_idx == 17 and isinstance(value, (int, float)):
                if value > bounderies:
                    cell.fill = positive_threshold_fill
                elif value < -bounderies:
                    cell.fill = negative_threshold_fill

    # Alignment style for headers
    alignment_center = Alignment(horizontal="center", vertical="center")
    bold_font = Font(bold=True)
    header_fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")  # Light green color

    # Helper function to style and merge cells
    def create_header(value, start_row, start_col, end_row, end_col):
        ws.cell(row=start_row, column=start_col, value=value).alignment = alignment_center
        ws.cell(row=start_row, column=start_col).font = bold_font
        ws.cell(row=start_row, column=start_col).fill = header_fill
        if start_row != end_row or start_col != end_col:
            ws.merge_cells(
                start_row=start_row,
                start_column=start_col,
                end_row=end_row,
                end_column=end_col,
            )

    create_header("Part No", 1, 1, 2, 1)
    create_header("Part Name", 1, 2, 2, 2)

    create_header("LVA", 1, 3, 1, 5)
    create_header(f"{var_previous}", 2, 3, 2, 3)
    create_header(f"{var_current}", 2, 4, 2, 4)
    create_header("Gap (%)", 2, 5, 2, 5)

    create_header("Non LVA", 1, 6, 1, 8)
    create_header(f"{var_previous}", 2, 6, 2, 6)
    create_header(f"{var_current}", 2, 7, 2, 7)
    create_header("Gap (%)", 2, 8, 2, 8)

    create_header("Tooling", 1, 9, 1, 11)
    create_header(f"{var_previous}", 2, 9, 2, 9)
    create_header(f"{var_current}", 2, 10, 2, 10)
    create_header("Gap (%)", 2, 11, 2, 11)

    create_header("Process Cost", 1, 12, 1, 14)
    create_header(f"{var_previous}", 2, 12, 2, 12)
    create_header(f"{var_current}", 2, 13, 2, 13)
    create_header("Gap (%)", 2, 14, 2, 14)

    create_header("Total Cost", 1, 15, 1, 17)
    create_header(f"{var_previous}", 2, 15, 2, 15)
    create_header(f"{var_current}", 2, 16, 2, 16)
    create_header("Gap (%)", 2, 17, 2, 17)

    create_header("Reason", 1, 18, 2, 18)

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    def apply_border(ws, start_row, start_col, end_row, end_col):
        for row in ws.iter_rows(min_row=start_row, min_col=start_col, max_row=end_row, max_col=end_col):
            for cell in row:
                cell.border = thin_border

    apply_border(ws, 1, 1, 1, 18)
    apply_border(ws, 2, 1, len(df) + 2, 18)

    excel_file = BytesIO()

    # Save the workbook
    wb.save(excel_file)
    excel_file.seek(0)

    return excel_file


def convert_to_excel_format_out_house(df, var_previous, var_current, bounderies):
    # Initialize workbook
    wb = Workbook()

    # Remove the default sheet created by default
    default_sheet = wb.active
    wb.remove(default_sheet)

    # Get unique sources
    unique_sources = df["source"].unique()

    # Define color fills for highlighting
    positive_threshold_fill = PatternFill(
        start_color="FFCCCC", end_color="FFCCCC", fill_type="solid"
    )  # Light red for values Above bounderies
    negative_threshold_fill = PatternFill(
        start_color="CCCCFF", end_color="CCCCFF", fill_type="solid"
    )  # Light blue for values Below bounderies

    # Create a sheet for each unique source
    for source in unique_sources:
        # Filter dataframe for the current source
        source_df = df[df["source"] == source]

        # Create a new worksheet for this source
        ws = wb.create_sheet(title=str(source))

        # Populate the worksheet with data from the filtered DataFrame, starting from row 3
        for r_idx, row in enumerate(dataframe_to_rows(source_df, index=False, header=False), 3):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)

                # Check if this is the Gap (%) column (column 6) and apply conditional formatting
                if c_idx == 6 and isinstance(value, (int, float)):
                    if value > bounderies:
                        cell.fill = positive_threshold_fill
                    elif value < -bounderies:
                        cell.fill = negative_threshold_fill

        # Alignment style for headers
        alignment_center = Alignment(horizontal="center", vertical="center")
        bold_font = Font(bold=True)
        header_fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")  # Light green color

        # Helper function to style and merge cells
        def create_header(value, start_row, start_col, end_row, end_col):
            ws.cell(row=start_row, column=start_col, value=value).alignment = alignment_center
            ws.cell(row=start_row, column=start_col).font = bold_font
            ws.cell(row=start_row, column=start_col).fill = header_fill
            if start_row != end_row or start_col != end_col:
                ws.merge_cells(
                    start_row=start_row,
                    start_column=start_col,
                    end_row=end_row,
                    end_column=end_col,
                )

        # Create headers for each sheet
        create_header("Part No", 1, 1, 2, 1)
        create_header("Part Name", 1, 2, 2, 2)
        create_header("Source", 1, 3, 2, 3)
        create_header("Price", 1, 4, 1, 6)
        create_header(f"{var_previous}", 2, 4, 2, 4)
        create_header(f"{var_current}", 2, 5, 2, 5)
        create_header("Gap (%)", 2, 6, 2, 6)
        create_header("Reason", 1, 7, 2, 7)

        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Function to apply border to a range of cells
        def apply_border(ws, start_row, start_col, end_row, end_col):
            for row in ws.iter_rows(min_row=start_row, min_col=start_col, max_row=end_row, max_col=end_col):
                for cell in row:
                    cell.border = thin_border

        # Apply borders
        apply_border(ws, 1, 1, 1, 7)  # Header border
        apply_border(ws, 2, 1, len(source_df) + 2, 7)  # Data rows border

    # Save the workbook to BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    return excel_file


def convert_to_excel_format_packaging(df, var_previous, var_current, bounderies):
    df = df[
        [
            "part_no",
            "part_name",
            "destination",
            "Labor Cost 2023",
            "Labor Cost 2024",
            "Material Cost 2023",
            "Material Cost 2024",
            "Inland Cost 2023",
            "Inland Cost 2024",
            "Max Total Cost 2023",
            "Max Total Cost 2024",
            "Gap Total Cost",
        ]
    ]
    # Initialize workbook
    wb = Workbook()

    # Remove the default sheet created by default
    default_sheet = wb.active
    wb.remove(default_sheet)

    # Get unique sources
    unique_sources = df["destination"].unique()

    # Define color fills for highlighting
    positive_threshold_fill = PatternFill(
        start_color="FFCCCC", end_color="FFCCCC", fill_type="solid"
    )  # Light red for values Above bounderies
    negative_threshold_fill = PatternFill(
        start_color="CCCCFF", end_color="CCCCFF", fill_type="solid"
    )  # Light blue for values Below bounderies

    # Create a sheet for each unique source
    for source in unique_sources:
        # Filter dataframe for the current source
        source_df = df[df["destination"] == source]

        # Create a new worksheet for this source
        ws = wb.create_sheet(title=str(source))

        # Populate the worksheet with data from the filtered DataFrame, starting from row 3
        for r_idx, row in enumerate(dataframe_to_rows(source_df, index=False, header=False), 3):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)

                # Gap Price Total
                if c_idx == 12 and isinstance(value, (int, float)):
                    if value > bounderies:
                        cell.fill = positive_threshold_fill
                    elif value < -bounderies:
                        cell.fill = negative_threshold_fill

        # Alignment style for headers
        alignment_center = Alignment(horizontal="center", vertical="center")
        bold_font = Font(bold=True)
        header_fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")  # Light green color

        # Helper function to style and merge cells
        def create_header(value, start_row, start_col, end_row, end_col):
            ws.cell(row=start_row, column=start_col, value=value).alignment = alignment_center
            ws.cell(row=start_row, column=start_col).font = bold_font
            ws.cell(row=start_row, column=start_col).fill = header_fill
            if start_row != end_row or start_col != end_col:
                ws.merge_cells(
                    start_row=start_row,
                    start_column=start_col,
                    end_row=end_row,
                    end_column=end_col,
                )

        # Create headers for each sheet
        create_header("Part No", 1, 1, 2, 1)
        create_header("Part Name", 1, 2, 2, 2)
        create_header("Destination", 1, 3, 2, 3)

        create_header("Labor Cost", 1, 4, 1, 5)
        create_header(f"{var_previous}", 2, 4, 2, 4)
        create_header(f"{var_current}", 2, 5, 2, 5)

        create_header("Material Cost", 1, 6, 1, 7)
        create_header(f"{var_previous}", 2, 6, 2, 6)
        create_header(f"{var_current}", 2, 7, 2, 7)

        create_header("Inland Cost", 1, 8, 1, 9)
        create_header(f"{var_previous}", 2, 8, 2, 8)
        create_header(f"{var_current}", 2, 9, 2, 9)

        create_header("Total Cost", 1, 10, 1, 11)
        create_header(f"{var_previous}", 2, 10, 2, 10)
        create_header(f"{var_current}", 2, 11, 2, 11)

        create_header("Gap Total Cost (%)", 1, 12, 2, 12)
        create_header("Reason", 1, 13, 2, 13)

        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Function to apply border to a range of cells
        def apply_border(ws, start_row, start_col, end_row, end_col):
            for row in ws.iter_rows(min_row=start_row, min_col=start_col, max_row=end_row, max_col=end_col):
                for cell in row:
                    cell.border = thin_border

        # Apply borders
        apply_border(ws, 1, 1, 1, 13)  # Header border
        apply_border(ws, 2, 1, len(source_df) + 2, 13)  # Data rows border

    # Save the workbook to BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    return excel_file
