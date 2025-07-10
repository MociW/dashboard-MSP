
import pandas as pd
import warnings
from typing import List

# Import the new optimized implementation
from utils.pdf.pdf_factory import generate_report


def generate_pdf_report_out_house(
        years: List[str],
        df_inhouse: pd.DataFrame,
        df_outhouse: pd.DataFrame,
        df_packing: pd.DataFrame,
        boundaries: List[int],
):
    """
    Generate an Out-House PDF report.
    
    This function is deprecated and will be removed in a future version.
    Please use the new API instead:
    
    ```python
    from utils.pdf import generate_report
    
    pdf_bytes = generate_report(
        "out_house",
        years=["2023", "2024"],
        df_outhouse=df_outhouse,
        boundaries=[6]
    )
    ```
    
    Args:
        years: A list containing start and end years for the report period.
        df_inhouse: Not used, kept for backward compatibility.
        df_outhouse: DataFrame containing out-house data.
        df_packing: Not used, kept for backward compatibility.
        boundaries: A list of boundary percentages for abnormality detection.
            
    Returns:
        bytes: The generated PDF as bytes.
    """
    warnings.warn(
        "generate_pdf_report_out_house is deprecated and will be removed in a future version. "
        "Please use from utils.pdf import generate_report instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to the new implementation - only use the out-house data and boundary
    return generate_report(
        "out_house",
        years=years,
        df_outhouse=df_outhouse,
        boundaries=[boundaries[1]] if len(boundaries) > 1 else boundaries
    )

