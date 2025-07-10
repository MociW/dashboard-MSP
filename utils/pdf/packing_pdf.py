
import pandas as pd
import warnings
from typing import List

# Import the new optimized implementation
from utils.pdf.pdf_factory import generate_report


def generate_pdf_report_packing(
        years: List[str],
        df_packing: pd.DataFrame,
        boundaries: List[int],
):
    """
    Generate a Packing PDF report.
    
    This function is deprecated and will be removed in a future version.
    Please use the new API instead:
    
    ```python
    from utils.pdf import generate_report
    
    pdf_bytes = generate_report(
        "packing",
        years=["2023", "2024"],
        df_packing=df_packing,
        boundaries=[7]
    )
    ```
    
    Args:
        years: A list containing start and end years for the report period.
        df_packing: DataFrame containing packing data.
        boundaries: A list of boundary percentages for abnormality detection.
            
    Returns:
        bytes: The generated PDF as bytes.
    """
    warnings.warn(
        "generate_pdf_report_packing is deprecated and will be removed in a future version. "
        "Please use from utils.pdf import generate_report instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to the new implementation
    return generate_report(
        "packing",
        years=years,
        df_packing=df_packing,
        boundaries=boundaries
    )

