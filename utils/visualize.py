import streamlit as st
import plotly.express as px


def pie_char_with_total_counts(df, title, bounderies):
    with st.container(border=False):
        # Create two columns for the main content
        main_col1, main_col2 = st.columns([1, 0.55], border=True)

        # First column for the pie chart
        with main_col1:
            pastel_colors = px.colors.qualitative.Pastel
            fig = px.pie(
                df,
                names=df.index,
                values=df.values,
                color=df.index,
                color_discrete_map={
                    "Normal": pastel_colors[0],
                    f"Abnormal Above {bounderies}%": pastel_colors[1],
                    f"Abnormal Below -{bounderies}%": pastel_colors[2],
                },
            )
            fig.update_layout(
                title_text=f"{title} Item",
                title_x=0,
                yaxis_title=None,
                xaxis_title=None,
                margin=dict(l=0, r=0, t=50, b=0),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Second column for the metrics
        with main_col2:
            # Create three metrics side by side
            val_above = f"Abnormal Above {bounderies}%"
            val_under = f"Abnormal Below -{bounderies}%"
            st.subheader(f"{title} Number")
            if val_above in df:
                st.metric(label=val_above, value=df[val_above])
            else:
                st.metric(label=val_above, value=0)

            if "Normal" in df:
                st.metric(label="Normal", value=df["Normal"])
            else:
                st.metric(label="Normal", value=0)

            if val_under in df:
                st.metric(label=val_under, value=df[val_under])
            else:
                st.metric(label=val_under, value=0)


def pie_char_with_total_counts_packing(df, title):
    with st.container(border=True):
        # Create two columns for the main content
        m = st.columns([0.5, 1, 0.5], gap="large")

        # First column for the pie chart
        with m[1]:
            fig = px.pie(df, names=df["destination"], values=df["count"])
            fig.update_layout(
                title_text=f"{title}",
                title_x=0,
                yaxis_title=None,
                xaxis_title=None,
                margin=dict(l=0, r=0, t=50, b=50),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)


def create_pie_charts(df, boundaries):
    # Create a grouped dataframe for the pie chart
    status_by_destination = df.groupby(["destination", "Status"]).size().reset_index(name="count")

    # Create a dictionary to store pie charts by destination
    pie_charts = {}

    # Get unique destinations
    destinations = df["destination"].unique()

    # Create a pie chart for each destination
    for dest in destinations:
        dest_data = status_by_destination[status_by_destination["destination"] == dest]

        fig = px.pie(
            dest_data,
            values="count",
            names="Status",
            title=f"{dest}",
            color="Status",
            color_discrete_map={
                "Normal": "#00CC96",
                f"Abnormal Above {boundaries}%": "#EF553B",
                f"Abnormal Below -{boundaries}%": "#636EFA",
            },
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")
        pie_charts[dest] = fig

    # Also create an overall pie chart
    overall_status = df.groupby("Status").size().reset_index(name="count")
    overall_fig = px.pie(
        overall_status,
        values="count",
        names="Status",
        title="Overall Status Distribution",
        color="Status",
        color_discrete_map={
            "Normal": "#00CC96",
            f"Abnormal Above {boundaries}%": "#EF553B",
            f"Abnormal Below -{boundaries}%": "#636EFA",
        },
    )
    overall_fig.update_traces(textposition="inside", textinfo="percent+label")
    pie_charts["Overall"] = overall_fig

    return pie_charts, df


def create_pie_chart_packing(data, destination, boundaries):
    # Filter data for the selected destination

    filtered_data = data[data["destination"] == destination]
    title = f"{destination} Abnormal Number"

    # Count occurrences of each status
    status_counts = filtered_data["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "count"]

    # Create pie chart
    fig = px.pie(
        status_counts,
        values="count",
        names="Status",
        title=title,
        color="Status",
        color_discrete_map={
            "Normal": "#00CC96",
            f"Abnormal Above {boundaries}%": "#EF553B",
            f"Abnormal Below -{boundaries}%": "#636EFA",
        },
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def create_pie_chart_out_house(data, source, boundaries):
    # Filter data for the selected destination

    filtered_data = data[data["source"] == source]
    title = f"{source} Abnormal Number"

    # Count occurrences of each status
    status_counts = filtered_data["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "count"]

    # Create pie chart
    fig = px.pie(
        status_counts,
        values="count",
        names="Status",
        title=title,
        color="Status",
        color_discrete_map={
            "Normal": "#00CC96",
            f"Abnormal Above {boundaries}%": "#EF553B",
            f"Abnormal Below -{boundaries}%": "#636EFA",
        },
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig
