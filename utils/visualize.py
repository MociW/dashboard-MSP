import streamlit as st
import plotly.express as px
import pandas as pd


def create_status_pie_chart(data, title, color_map=None):
    """
    Create a pie chart for status distribution.

    Args:
        data: DataFrame or Series with status counts
        title: Chart title
        color_map: Optional custom color mapping dictionary

    Returns:
        Plotly figure object
    """
    if color_map is None:
        color_map = {
            "Normal": "#00CC96",
            "Abnormal Above": "#EF553B",
            "Abnormal Below": "#636EFA",
        }

    # Check if data is a DataFrame or Series
    is_dataframe = isinstance(data, pd.DataFrame)

    fig = px.pie(
        data,
        names="Status" if (is_dataframe and "Status" in data.columns) else data.index,
        values="count" if (is_dataframe and "count" in data.columns) else data.values,
        title=title,
        color="Status" if (is_dataframe and "Status" in data.columns) else data.index,
        color_discrete_map=color_map,
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(title_x=0, margin=dict(l=0, r=0, t=50, b=0), height=400)

    return fig


def display_pie_with_metrics(df, title, boundaries):
    """
    Display a pie chart with metrics in a two-column layout.

    Args:
        df: DataFrame or Series with status counts
        title: Chart title
        boundaries: Boundary percentage for abnormal values
    """
    # Set up the color mapping with dynamic boundary values
    color_map = {
        "Normal": px.colors.qualitative.Pastel[0],
        f"Abnormal Above {boundaries}%": px.colors.qualitative.Pastel[1],
        f"Abnormal Below -{boundaries}%": px.colors.qualitative.Pastel[2],
    }

    with st.container(border=False):
        # Create two columns for the main content
        main_col1, main_col2 = st.columns([1, 0.55], gap="small", border=True)

        # First column for the pie chart
        with main_col1:
            fig = create_status_pie_chart(df, f"{title} Item", color_map)
            st.plotly_chart(fig, use_container_width=True)

        # Second column for the metrics
        with main_col2:
            st.subheader(f"{title} Number")

            # Display metrics for each status
            for status in [f"Abnormal Above {boundaries}%", "Normal", f"Abnormal Below -{boundaries}%"]:
                # Handle both Series and DataFrame inputs
                if isinstance(df, pd.Series):
                    value = df.get(status, 0) if status in df.index else 0
                else:  # DataFrame
                    status_row = df[df["Status"] == status] if "Status" in df.columns else None
                    value = status_row["count"].iloc[0] if status_row is not None and not status_row.empty else 0
                st.metric(label=status, value=value)


def display_simple_pie_chart(df, title, col_ratio=None):
    """
    Display a simple pie chart in a container with optional column ratio.

    Args:
        df: DataFrame with destination and count columns
        title: Chart title
        col_ratio: Optional column ratio list
    """
    with st.container(border=True):
        # Create columns with the specified ratio or default
        if col_ratio is None:
            col_ratio = [0.5, 1, 0.5]

        cols = st.columns(col_ratio, gap="large")

        # Middle column for the pie chart
        with cols[1]:
            fig = px.pie(df, names="destination", values="count")
            fig.update_layout(title_text=title, title_x=0, margin=dict(l=0, r=0, t=50, b=50), height=400)
            st.plotly_chart(fig, use_container_width=True)


def get_status_counts(df, group_by_field=None):
    """
    Get status counts from a DataFrame.

    Args:
        df: DataFrame with Status column
        group_by_field: Optional field to group by before counting statuses

    Returns:
        DataFrame with status counts
    """
    if group_by_field:
        return df.groupby([group_by_field, "Status"]).size().reset_index(name="count")
    else:
        return df.groupby("Status").size().reset_index(name="count")


def create_status_pie_charts(df, boundaries):
    """
    Create multiple pie charts for each unique value in a field and an overall chart.

    Args:
        df: DataFrame with destination and Status columns
        boundaries: Boundary percentage for abnormal values

    Returns:
        Dictionary of pie charts and the original DataFrame
    """
    # Define color map with dynamic boundaries
    color_map = {
        "Normal": "#00CC96",
        f"Abnormal Above {boundaries}%": "#EF553B",
        f"Abnormal Below -{boundaries}%": "#636EFA",
    }

    # Get status counts by destination
    status_by_destination = get_status_counts(df, "destination")

    # Create a dictionary to store pie charts
    pie_charts = {}

    # Create pie charts for each destination
    for dest in df["destination"].unique():
        dest_data = status_by_destination[status_by_destination["destination"] == dest]
        fig = create_status_pie_chart(dest_data, f"{dest}", color_map)
        pie_charts[dest] = fig

    # Create overall pie chart
    overall_status = get_status_counts(df)
    overall_fig = create_status_pie_chart(overall_status, "Overall Status Distribution", color_map)
    pie_charts["Overall"] = overall_fig

    return pie_charts, df


def create_filtered_pie_chart(data, filter_field, filter_value, boundaries):
    """
    Create a pie chart for a filtered subset of data.

    Args:
        data: DataFrame with Status column
        filter_field: Field name to filter on
        filter_value: Value to filter for
        boundaries: Boundary percentage for abnormal values

    Returns:
        Plotly figure object
    """
    # Filter data
    filtered_data = data[data[filter_field] == filter_value]

    # Get status counts
    status_counts = filtered_data["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "count"]

    # Define color map with dynamic boundaries
    color_map = {
        "Normal": "#00CC96",
        f"Abnormal Above {boundaries}%": "#EF553B",
        f"Abnormal Below -{boundaries}%": "#636EFA",
    }

    # Create and return the pie chart
    return create_status_pie_chart(status_counts, f"{filter_value} Abnormal Number", color_map)


# Specific wrapper functions that use the core functions above
def create_pie_chart_packing(data, destination, boundaries):
    return create_filtered_pie_chart(data, "destination", destination, boundaries)


def create_pie_chart_out_house(data, source, boundaries):
    return create_filtered_pie_chart(data, "source", source, boundaries)


def pie_char_with_total_counts(df, title, boundaries):
    display_pie_with_metrics(df, title, boundaries)


def pie_char_with_total_counts_packing(df, title):
    display_simple_pie_chart(df, title)


def create_pie_charts(df, boundaries):
    return create_status_pie_charts(df, boundaries)
