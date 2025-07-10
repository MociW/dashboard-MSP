

import pandas as pd
import warnings
from typing import List

# Import the new optimized implementation
from utils.pdf.pdf_factory import generate_report


def generate_pdf_report_in_house(
        years: List[str],
        df_inhouse: pd.DataFrame,
        boundaries: List[int],
):
    """
    Generate an In-House PDF report.
    
    This function is deprecated and will be removed in a future version.
    Please use the new API instead:
    
    ```python
    from utils.pdf import generate_report
    
    pdf_bytes = generate_report(
        "in_house",
        years=["2023", "2024"],
        df_inhouse=df_inhouse,
        boundaries=[5]
    )
    ```
    
    Args:
        years: A list containing start and end years for the report period.
        df_inhouse: DataFrame containing in-house data.
        boundaries: A list of boundary percentages for abnormality detection.
            
    Returns:
        bytes: The generated PDF as bytes.
    """
    warnings.warn(
        "generate_pdf_report_in_house is deprecated and will be removed in a future version. "
        "Please use from utils.pdf import generate_report instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to the new implementation
    return generate_report(
        "in_house",
        years=years,
        df_inhouse=df_inhouse,
        boundaries=boundaries
    )

