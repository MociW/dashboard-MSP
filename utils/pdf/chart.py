import plotly.graph_objects as go
import pandas as pd
import io
from plotly.subplots import make_subplots
import plotly.express as px


def grouped_bar_chart(
    df: pd.DataFrame, source, boundaries: str, width: int = 800, height: int = 480, legend_param=True
):
    # Get unique sources
    sources = df[source].unique()

    # Count total items per source to determine sorting
    source_counts = {}
    for i in sources:
        source_counts[i] = df[df[source] == i].shape[0]

    # Sort sources by total count (descending)
    sources = sorted(sources, key=lambda x: source_counts[x], reverse=True)

    # Count statuses by source
    normal_counts = []
    above_counts = []
    below_counts = []

    for i in sources:
        source_data = df[df[source] == i]
        # Count normal statuses
        normal_count = source_data[source_data["Status"] == "Normal"].shape[0]
        normal_counts.append(normal_count)
        # Count above threshold statuses
        above_count = source_data[source_data["Status"] == f"Abnormal Above {boundaries}%"].shape[0]
        above_counts.append(above_count)
        # Count below threshold statuses
        below_count = source_data[source_data["Status"] == f"Abnormal Below -{boundaries}%"].shape[0]
        below_counts.append(below_count)

    # Create a figure
    fig = go.Figure()

    # Add the primary product bar trace
    fig.add_trace(
        go.Bar(
            x=sources,
            y=normal_counts,
            name="Normal",
            marker_color="rgb(57,74,86)",
            text=[count if count > 0 else "" for count in normal_counts],  # Only show non-zero counts
            textposition="outside",
        )
    )

    # Add the secondary product bar trace
    fig.add_trace(
        go.Bar(
            x=sources,
            y=above_counts,
            name=f"Abnormal Above {boundaries}%",
            marker_color="rgb(139, 0, 0)",
            text=[count if count > 0 else "" for count in above_counts],  # Only show non-zero counts
            textposition="outside",
        )
    )

    # Add the third product bar trace
    fig.add_trace(
        go.Bar(
            x=sources,
            y=below_counts,
            name=f"Abnormal Below -{boundaries}%",
            marker_color="rgb(255, 0, 0)",
            text=[count if count > 0 else "" for count in below_counts],  # Only show non-zero counts
            textposition="outside",
        )
    )

    # Update the layout
    fig.update_layout(
        showlegend=legend_param,
        barmode="group",
        # xaxis_tickangle=-45,
        yaxis=dict(
            visible=False,
            showticklabels=True,
            showgrid=False,
            zeroline=True,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=50, l=20, r=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        height=height,
        width=width,
        font=dict(size=14),
    )

    image_data = fig.to_image(format="png", engine="kaleido")
    return io.BytesIO(image_data)


def single_pie_chart(df, boundaries, column_status, title, height=400, width=400, legend_param=False):
    # Get status counts
    status_counts = df[column_status].value_counts().reset_index()
    status_counts.columns = ["Status", "count"]

    # Define color map
    color_map = {
        # f"Abnormal Above {boundaries}%": "#EF553B",
        # f"Abnormal Below -{boundaries}%": "#636EFA",
        "Normal": "rgb(57,74,86)",
        f"Abnormal Above {boundaries}%": "rgb(139, 0, 0)",
        f"Abnormal Below -{boundaries}%": "rgb(255, 0, 0)",
    }

    # Create the pie chart
    fig = px.pie(
        status_counts,
        values="count",
        names="Status",
        color="Status",
        color_discrete_map=color_map,
    )

    if legend_param:
        y_pos = 0.2
    else:
        y_pos = 0.08

    # Update layout
    fig.update_layout(
        showlegend=legend_param,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=50, l=0, r=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
        ),
        height=height,
        width=width,
        title={
            "text": title,
            "y": y_pos,
            "x": 0.5,
            "yanchor": "top",
            "xanchor": "center",
        },
        font=dict(size=14),
    )

    # Update hover info
    fig.update_traces(hoverinfo="label+percent+value", textinfo="percent")

    # Convert to image and return as BytesIO
    image_data = fig.to_image(format="png", engine="kaleido")
    return io.BytesIO(image_data)


def grouped_pie_chart(df, boundaries, width=900, height=300):
    categories = {
        "LVA": df["LVA Status"].value_counts(),
        "Non LVA": df["Non LVA Status"].value_counts(),
        "Tooling": df["Tooling Status"].value_counts(),
        "Process Cost": df["Process Cost Status"].value_counts(),
    }
    category_names = list(categories.keys())
    num_categories = len(category_names)

    # Create specs and titles
    specs = [[{"type": "domain"} for _ in range(num_categories)]]

    # Create subplots
    fig = make_subplots(
        rows=1,
        cols=num_categories,
        specs=specs,
        subplot_titles=category_names,
    )

    # Define color map for consistent colors across plots
    color_map = {
        "Normal": "rgb(57,74,86)",
        f"Abnormal Above {boundaries}%": "rgb(139, 0, 0)",
        f"Abnormal Below -{boundaries}%": "rgb(255, 0, 0)",
    }

    # Add a pie chart for each category
    for i, (category, counts) in enumerate(categories.items(), start=1):
        # Convert to DataFrame for easier handling
        status_counts = counts.reset_index()
        status_counts.columns = ["status", "count"]

        # Add the pie chart
        fig.add_trace(
            go.Pie(
                labels=status_counts["status"],
                values=status_counts["count"],
                name=category,
                marker_colors=[color_map.get(status, "blue") for status in status_counts["status"]],
                textinfo="percent",
            ),
            row=1,
            col=i,
        )

    # Update hover info
    fig.update_traces(hoverinfo="label+percent+name")

    # Position the titles below the pie charts
    for i in range(len(fig.layout.annotations)):
        fig.layout.annotations[i].y = 0.0
        fig.layout.annotations[i].yanchor = "top"

    # Update layout
    fig.update_layout(
        showlegend=True,
        legend=dict(x=0, y=-0.2, xanchor="left", yanchor="top", orientation="h"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=50, l=20, r=20),
        height=height,
        width=width,
        font=dict(size=14),
    )

    # Save as PNG with transparent background
    image_data = fig.to_image(format="png", engine="kaleido")
    return io.BytesIO(image_data)


def grouped_bar_chart_dest(
    df: pd.DataFrame, source, boundaries: str, width: int = 800, height: int = 480, legend_param=True
):
    # Get unique sources
    sources = df[source].unique()

    # Count total items per source to determine sorting
    source_counts = {}
    for i in sources:
        source_counts[i] = df[df[source] == i].shape[0]

    # Sort sources by total count (descending)
    sources = sorted(sources, key=lambda x: source_counts[x], reverse=True)

    # Calculate percentages by source
    normal_percentages = []
    abnormal_percentages = []

    for i in sources:
        source_data = df[df[source] == i]
        total_count = source_data.shape[0]

        # Count normal statuses
        normal_count = source_data[source_data["Status"] == "Normal"].shape[0]
        normal_percentage = (normal_count / total_count * 100) if total_count > 0 else 0
        normal_percentages.append(normal_percentage)

        # Count and combine both abnormal statuses (above and below)
        above_count = source_data[source_data["Status"] == f"Abnormal Above {boundaries}%"].shape[0]
        below_count = source_data[source_data["Status"] == f"Abnormal Below -{boundaries}%"].shape[0]
        abnormal_count = above_count + below_count
        abnormal_percentage = (abnormal_count / total_count * 100) if total_count > 0 else 0
        abnormal_percentages.append(abnormal_percentage)

    # Create a figure
    fig = go.Figure()

    # Add the normal percentage bar trace
    fig.add_trace(
        go.Bar(
            x=sources,
            y=normal_percentages,
            name="Normal",
            marker_color="rgb(57,74,86)",
            text=[f"{percentage:.1f}%" if percentage > 0 else "" for percentage in normal_percentages],
            textposition="outside",
        )
    )

    # Add the combined abnormal percentage bar trace
    fig.add_trace(
        go.Bar(
            x=sources,
            y=abnormal_percentages,
            name=f"Abnormal (±{boundaries}%)",
            marker_color="rgb(255, 0, 0)",
            text=[f"{percentage:.1f}%" if percentage > 0 else "" for percentage in abnormal_percentages],
            textposition="outside",
        )
    )
    if legend_param:
        mb = 50
    else:
        mb = 20

    # Update the layout
    fig.update_layout(
        showlegend=legend_param,
        barmode="group",
        # xaxis_tickangle=-45,
        yaxis=dict(
            title="Percentage (%)",
            visible=True,
            showticklabels=True,
            showgrid=False,
            zeroline=True,
            range=[0, 110],
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=mb, l=60, r=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        height=height,
        width=width,
        font=dict(size=14),
    )

    image_data = fig.to_image(format="png", engine="kaleido")
    return io.BytesIO(image_data)
