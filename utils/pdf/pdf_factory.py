import pandas as pd
from enum import Enum, auto
from typing import List, Union, Literal

from utils.pdf.in_house_report import InHousePDFReport
from utils.pdf.out_house_report import OutHousePDFReport
from utils.pdf.packing_report import PackingPDFReport
from utils.pdf.complete_report import CompletePDFReport


class ReportType(Enum):
    """Enum defining the types of reports that can be generated."""
    IN_HOUSE = auto()
    OUT_HOUSE = auto()
    PACKING = auto()
    COMPLETE = auto()


class PDFReportFactory:
    """
    Factory class for creating PDF report objects.
    Follows the Factory Method pattern to create appropriate report instances.
    """
    
    @classmethod
    def create_report(cls, 
                     report_type: ReportType, 
                     years: List[str], 
                     df_inhouse: pd.DataFrame = None, 
                     df_outhouse: pd.DataFrame = None, 
                     df_packing: pd.DataFrame = None, 
                     boundaries: List[int] = None):
        """
        Create a report based on the specified report type.
        
        Args:
            report_type (ReportType): The type of report to create.
            years (List[str]): A list containing start and end years for the report period.
            df_inhouse (pandas.DataFrame, optional): DataFrame containing in-house data.
            df_outhouse (pandas.DataFrame, optional): DataFrame containing out-house data.
            df_packing (pandas.DataFrame, optional): DataFrame containing packing data.
            boundaries (List[int], optional): A list of boundary percentages for abnormality detection.
                
        Returns:
            Union[InHousePDFReport, OutHousePDFReport, PackingPDFReport, CompletePDFReport]: 
                An instance of the appropriate report class.
                
        Raises:
            ValueError: If required DataFrames for the specified report type are not provided.
        """
        # Default boundaries if none provided
        if boundaries is None:
            boundaries = [5, 6, 7]  # Default boundaries for each report type
        
        # Create the appropriate report based on the report type
        if report_type == ReportType.IN_HOUSE:
            if df_inhouse is None:
                raise ValueError("In-house data (df_inhouse) is required for IN_HOUSE report type")
            return InHousePDFReport(years, df_inhouse, boundaries)
            
        elif report_type == ReportType.OUT_HOUSE:
            if df_outhouse is None:
                raise ValueError("Out-house data (df_outhouse) is required for OUT_HOUSE report type")
            return OutHousePDFReport(years, df_outhouse, boundaries)
            
        elif report_type == ReportType.PACKING:
            if df_packing is None:
                raise ValueError("Packing data (df_packing) is required for PACKING report type")
            return PackingPDFReport(years, df_packing, boundaries)
            
        elif report_type == ReportType.COMPLETE:
            if any(df is None for df in [df_inhouse, df_outhouse, df_packing]):
                raise ValueError("All DataFrames (df_inhouse, df_outhouse, df_packing) are required for COMPLETE report type")
            return CompletePDFReport(years, df_inhouse, df_outhouse, df_packing, boundaries)
            
        else:
            raise ValueError(f"Unknown report type: {report_type}")


def generate_report(
    report_type: Union[ReportType, str],
    years: List[str],
    df_inhouse: pd.DataFrame = None,
    df_outhouse: pd.DataFrame = None,
    df_packing: pd.DataFrame = None,
    boundaries: List[int] = None,
) -> bytes:
    """
    Simple facade function to generate a PDF report.
    
    Args:
        report_type (Union[ReportType, str]): The type of report to generate.
            Can be a ReportType enum value or a string ('in_house', 'out_house', 'packing', 'complete').
        years (List[str]): A list containing start and end years for the report period.
        df_inhouse (pandas.DataFrame, optional): DataFrame containing in-house data.
        df_outhouse (pandas.DataFrame, optional): DataFrame containing out-house data.
        df_packing (pandas.DataFrame, optional): DataFrame containing packing data.
        boundaries (List[int], optional): A list of boundary percentages for abnormality detection.
            
    Returns:
        bytes: The generated PDF as bytes.
        
    Example:
        ```
        # Generate an in-house report
        pdf_bytes = generate_report(
            'in_house',
            years=['2023', '2024'],
            df_inhouse=in_house_data,
            boundaries=[5]
        )
        
        # Write the PDF to a file
        with open('in_house_report.pdf', 'wb') as f:
            f.write(pdf_bytes)
        ```
    """
    # Convert string report_type to enum if needed
    if isinstance(report_type, str):
        report_type_map = {
            'in_house': ReportType.IN_HOUSE,
            'out_house': ReportType.OUT_HOUSE,
            'packing': ReportType.PACKING,
            'complete': ReportType.COMPLETE
        }
        if report_type.lower() not in report_type_map:
            valid_types = list(report_type_map.keys())
            raise ValueError(f"Invalid report type string: '{report_type}'. Valid types are: {valid_types}")
        report_type = report_type_map[report_type.lower()]
    
    # Create the report using the factory
    report = PDFReportFactory.create_report(
        report_type,
        years,
        df_inhouse,
        df_outhouse,
        df_packing,
        boundaries
    )
    
    # Generate and return the PDF
    return report.generate()

