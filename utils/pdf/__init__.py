"""
PDF Report Generation Package

This package provides functionality for generating various types of PDF reports
for the Toyota Dashboard MSP application, with a focus on abnormality data visualization.

Usage:
    ```python
    from utils.pdf import generate_report, ReportType
    
    # Generate a report with string-based report type (simplest approach)
    pdf_bytes = generate_report(
        'in_house',
        years=['2023', '2024'],
        df_inhouse=in_house_data,
        boundaries=[5]
    )
    
    # Or use the enum for report type (type-safe approach)
    pdf_bytes = generate_report(
        ReportType.COMPLETE,
        years=['2023', '2024'],
        df_inhouse=in_house_data,
        df_outhouse=out_house_data,
        df_packing=packing_data,
        boundaries=[5, 6, 7]
    )
    
    # Save to file
    with open('report.pdf', 'wb') as f:
        f.write(pdf_bytes)
    ```
"""

# Main entry point - facade function for generating reports
from utils.pdf.pdf_factory import generate_report

# ReportType enum for type-safe report selection
from utils.pdf.pdf_factory import ReportType

# Factory class for more advanced usage
from utils.pdf.pdf_factory import PDFReportFactory

# Report classes for direct access if needed
from utils.pdf.base_pdf import BasePDFReport
from utils.pdf.in_house_report import InHousePDFReport
from utils.pdf.out_house_report import OutHousePDFReport
from utils.pdf.packing_report import PackingPDFReport
from utils.pdf.complete_report import CompletePDFReport

# Export chart module
from utils.pdf import chart

# Define package exports explicitly
__all__ = [
    'generate_report',
    'ReportType',
    'PDFReportFactory',
    'BasePDFReport',
    'InHousePDFReport',
    'OutHousePDFReport',
    'PackingPDFReport',
    'CompletePDFReport',
    'chart'
]

