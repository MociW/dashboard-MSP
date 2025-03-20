import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import LoginError
import utils.sql_in_house as us
import utils.sql_packing as up
import utils.sql_out_house as uo
import utils.visualize as uv
import utils.formatting as uf
import utils.pdf.generate_pdf as ag
import os

# Page configuration
st.set_page_config(page_title="TMMIN PBMD - Dashboard", layout="wide")
st.image("images/toyota.png", width=250)
st.header("🗒️ DASHBOARD ABNORMALITY MANAGEMENT - PBMD")


# Authentication setup
@st.cache_resource
def load_config():
    with open("config.yaml", "r", encoding="utf-8") as file:
        return yaml.load(file, Loader=SafeLoader)


config = load_config()
authenticator = stauth.Authenticate(
    config["credentials"], config["cookie"]["name"], config["cookie"]["key"], config["cookie"]["expiry_days"]
)

# Handle login
try:
    authenticator.login()
except LoginError as e:
    st.error(e)

# Authentication status checking
if st.session_state["authentication_status"]:
    # User info, input data button, and logout
    col1, col2, col3, col4 = st.columns([0.52, 0.20, 0.20, 0.08])
    with col1:
        st.subheader(f"Welcome {st.session_state['name']}")
    with col3:
        allowed_input_roles = ["archmagus", "oracles", "treasurers", "shielders", "seekers"]
        if st.session_state["roles"][0] in allowed_input_roles:
            if st.button("📊 Input Data", use_container_width=True):
                st.switch_page("pages/input_data.py")
    with col2:
        allowed_update_roles = ["archmagus", "oracles"]
        if st.session_state["roles"][0] in allowed_update_roles:
            if st.button("📋 Update Data", use_container_width=True):
                st.switch_page("pages/update_data.py")
    with col4:
        authenticator.logout()

    # Database connection
    conn = st.connection("postgresql", type="sql")

    # Input form
    with st.form(key="form_input"):
        col1, col2 = st.columns(2)
        input_previous_year = col1.text_input("Input Previous Year")
        input_current_year = col2.text_input("Input Current Year")
        input_abnormal = st.text_input("Abnormal Boundaries (%)")
        submit_button = st.form_submit_button(label="Submit", type="primary")

        if submit_button:
            st.session_state["years"] = [input_previous_year, input_current_year]
            st.session_state["input_abnormal"] = input_abnormal
    # Check if required session state data exists
    if not all(key in st.session_state for key in ["years", "input_abnormal"]):
        st.warning("Please submit the form above to continue")
        st.stop()

    # Extract common values
    years = st.session_state["years"]
    input_abnormal = st.session_state["input_abnormal"]
    input_previous_year, input_current_year = years

elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
    st.stop()
elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")
    st.stop()


# Function to display status metrics
def display_status_metrics(status_data):
    m = st.columns(3, gap="small")
    for i, status in enumerate(["Deleted", "Remain", "New"]):
        with m[i]:
            value = status_data.get(status, 0)
            st.metric(label=status, value=value)


# Function to generate and display download buttons
def display_download_buttons(full_excel, filtered_excel, section_name):
    cols = st.columns(2, border=True)
    with cols[0]:
        st.subheader("Full Excel")
        st.download_button(
            label="Download Excel File",
            data=full_excel,
            file_name=f"{section_name}_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with cols[1]:
        st.subheader("Filtered Excel")
        st.download_button(
            label="Download Excel File",
            data=filtered_excel,
            file_name=f"{section_name}_filtered_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ======================================== IN HOUSE ========================================
st.header("IN HOUSE")


# Cache query results to prevent redundant database calls
@st.cache_data(ttl="15m")
def get_in_house_data(years, abnormal_threshold):
    try:
        status_items = conn.query(us.status_product_two_year(years))
        abnormal_cal = conn.query(us.abnormal_cal(years, abnormal_threshold))
        full_abnormal_cal = conn.query(us.full_abnormal_cal(years, abnormal_threshold))
        return status_items, abnormal_cal, full_abnormal_cal
    except Exception as e:
        # st.warning(e)
        if "sqlalchemy.exc.ProgrammingError" in str(e) or "psycopg2.errors.SyntaxError" in str(e):
            st.warning("There was an issue with your database query. Please check your input parameters.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        else:
            raise e


try:
    # Get in-house data
    status_items_impl, abnormal_cal_impl, full_abnormal_cal_impl = get_in_house_data(years, input_abnormal)

    # Process data
    status_items_counts = status_items_impl["Status"].value_counts()
    full_abnormal_cal_impl["Status Abnormal"] = abnormal_cal_impl["Status Abnormal"]
    abnormal_cal_counts = abnormal_cal_impl["Status Abnormal"].value_counts()
    explain_cal_counts = abnormal_cal_impl["Explanation Status"].value_counts()

    # Process abnormal data categories
    abnormal_categories = {
        "LVA Status": full_abnormal_cal_impl["LVA Status"].value_counts(),
        "Non LVA Status": full_abnormal_cal_impl["Non LVA Status"].value_counts(),
        "Tooling Status": full_abnormal_cal_impl["Tooling Status"].value_counts(),
        "Process Cost Status": full_abnormal_cal_impl["Process Cost Status"].value_counts(),
        "Total Cost Status": full_abnormal_cal_impl["Total Cost Status"].value_counts(),
    }

    # Generate Excel files
    df_generate = abnormal_cal_impl.drop("Status Abnormal", axis=1)
    generate_excel = uf.convert_to_excel_in_house(
        df_generate, input_previous_year, input_current_year, int(input_abnormal)
    )

    abnormal_filtered = abnormal_cal_impl[abnormal_cal_impl["Status Abnormal"] == "Abnormal"].drop(
        "Status Abnormal", axis=1
    )
    generate_excel_filtered = uf.convert_to_excel_in_house(
        abnormal_filtered, input_previous_year, input_current_year, int(input_abnormal)
    )

    # Display metrics
    mc = st.columns(3, border=True)
    with mc[0]:
        st.subheader("Item Status")
        display_status_metrics(status_items_counts)

    with mc[1]:
        st.subheader("Abnormal Number")
        m = st.columns(2, gap="small")
        with m[0]:
            val_above = "Abnormal"
            st.metric(label=val_above, value=abnormal_cal_counts.get(val_above, 0))
        with m[1]:
            st.metric(label="Normal", value=abnormal_cal_counts.get("Normal", 0))
    with mc[2]:
        st.subheader("Explanation Status")
        m = st.columns(3, gap="small")
        statuses = ["Approved", "Disapproved", "Awaiting"]
        for i, status in enumerate(statuses):
            with m[i]:
                st.metric(label=status, value=explain_cal_counts.get(status, 0))

    # Display pie charts for all categories
    for category_name, category_data in abnormal_categories.items():
        uv.pie_char_with_total_counts(category_data, category_name, input_abnormal)
    # Display download buttons
    display_download_buttons(generate_excel, generate_excel_filtered, "in_house")

except Exception as e:
    if "KeyError" in str(e):
        st.warning("There was an issue with your database query. Please check your input parameters.")

# ======================================== OUT HOUSE ========================================
st.divider()
st.header("OUT HOUSE")


# Cache query results for out house data
@st.cache_data(ttl="15m")
def get_out_house_data(years, abnormal_threshold):
    try:
        status_items = conn.query(uo.status_product_two_year_out_house(years))
        abnormal_cal = conn.query(uo.abnormal_cal_out_house(years, abnormal_threshold))
        abnormal_cal_per_part = conn.query(uo.abnormal_cal_out_house_per_part(years))
        return status_items, abnormal_cal, abnormal_cal_per_part
    except Exception as e:
        # st.warning(e)
        if "sqlalchemy.exc.ProgrammingError" in str(e) or "psycopg2.errors.SyntaxError" in str(e):
            st.warning("There was an issue with your database query. Please check your input parameters.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        else:
            raise e


try:
    # Get out house data
    status_items_out, abnormal_cal_out, abnormal_cal_per_part_out = get_out_house_data(years, input_abnormal)

    # Process data
    status_counts_out = status_items_out["Status"].value_counts()
    abnormal_counts_out = abnormal_cal_out["Status"].value_counts()
    explain_cal_counts_out = abnormal_cal_impl["Explanation Status"].value_counts()

    # Generate Excel files
    df_generate_out = abnormal_cal_out.drop("Status", axis=1)
    generate_excel_out = uf.convert_to_excel_format_out_house(
        df_generate_out, input_previous_year, input_current_year, int(input_abnormal)
    )

    # Filter for abnormal items
    abnormal_filter = (abnormal_cal_out["Status"] == f"Abnormal Above {input_abnormal}%") | (
        abnormal_cal_out["Status"] == f"Abnormal Below -{input_abnormal}%"
    )
    abnormal_filtered_out = abnormal_cal_out[abnormal_filter].drop("Status", axis=1)
    generate_excel_filtered_out = uf.convert_to_excel_format_out_house(
        abnormal_filtered_out, input_previous_year, input_current_year, int(input_abnormal)
    )

    generate_excel_per_part = uf.convert_to_excel_format_out_house_per_part(
        abnormal_cal_per_part_out, input_previous_year, input_current_year, int(input_abnormal)
    )

    # Display metrics
    mc = st.columns(3, border=True)
    with mc[0]:
        st.subheader("Item Status")
        display_status_metrics(status_counts_out)

    with mc[1]:
        st.subheader("Abnormal Number")
        m = st.columns(3, gap="small")
        statuses = [f"Abnormal Above {input_abnormal}%", "Normal", f"Abnormal Below -{input_abnormal}%"]
        for i, status in enumerate(statuses):
            with m[i]:
                st.metric(label=status, value=abnormal_counts_out.get(status, 0))

    with mc[2]:
        st.subheader("Explanation Status")
        m = st.columns(3, gap="small")
        statuses = ["Approved", "Disapproved", "Awaiting"]
        for i, status in enumerate(statuses):
            with m[i]:
                st.metric(label=status, value=explain_cal_counts_out.get(status, 0))

    # Display pie chart
    with st.container(border=True):
        pastel_colors = px.colors.qualitative.Pastel
        fig = px.pie(
            abnormal_counts_out,
            values=abnormal_counts_out.values,
            names=abnormal_counts_out.index,
            title="Out House Cost Abnormality Distribution",
            color=abnormal_counts_out.index,
            color_discrete_map={
                "Normal": pastel_colors[0],
                f"Abnormal Above {input_abnormal}%": pastel_colors[1],
                f"Abnormal Below -{input_abnormal}%": pastel_colors[2],
            },
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    n = st.columns(2, gap="medium")

    # Left column - Top 10 Above
    with n[0]:
        st.markdown(f"### Top 10 Above {input_abnormal}%")

        # Get top 10 above data
        top_10_above = abnormal_cal_out.dropna(subset=["Gap Price"]).drop("Status", axis=1, errors="ignore").head(10)
        # Create a container with styling
        st.dataframe(
            top_10_above,
            column_config={
                "Gap Price": st.column_config.NumberColumn(
                    "Gap (%)", format="%.2f%%", help="Percentage difference from expected price"
                ),
                f"Price {input_previous_year}": st.column_config.NumberColumn(
                    f"{input_previous_year} (Rp)", format="Rp %.0f"
                ),
                f"Price {input_current_year}": st.column_config.NumberColumn(
                    f"{input_current_year} (Rp)", format="Rp %.0f"
                ),
            },
            use_container_width=True,
            hide_index=False,
        )

        with st.container(border=True):
            # Display metrics for the first entry if available
            if not top_10_above.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        label=f"Price {input_previous_year}",
                        value=f"Rp {top_10_above[f'Price {input_previous_year}'].iloc[0]:,.0f}",
                    )

                with col2:
                    # Use the correct column name for current price
                    st.metric(
                        label="Highest Gap",
                        value=f"{top_10_above['Gap Price'].iloc[0]:.2f}%",
                        delta=f"{top_10_above['Gap Price'].iloc[0] - float(input_abnormal):.2f}%",
                        delta_color="inverse",
                    )
                with col3:
                    # Use the correct column name for current price
                    st.metric(
                        label=f"Price {input_current_year}",
                        value=f"Rp {top_10_above[f'Price {input_current_year}'].iloc[0]:,.0f}",
                    )

    with n[1]:
        st.markdown(f"### Top 10 Below -{input_abnormal}%")

        # Get top 10 below data
        top_10_below = (
            abnormal_cal_out.dropna(subset=["Gap Price"])
            .drop("Status", axis=1, errors="ignore")
            .sort_values("Gap Price")
            .head(10)
        )

        st.dataframe(
            top_10_below,
            column_config={
                "Gap Price": st.column_config.NumberColumn(
                    "Gap (%)", format="%.2f%%", help="Percentage difference from expected price"
                ),
                f"Price {input_previous_year}": st.column_config.NumberColumn(
                    f"{input_previous_year} (Rp)", format="Rp %.0f"
                ),
                f"Price {input_current_year}": st.column_config.NumberColumn(
                    f"{input_current_year} (Rp)", format="Rp %.0f"
                ),
            },
            use_container_width=True,
            hide_index=False,
        )

        # Create a container with styling
        with st.container(border=True):
            # Display metrics for the first entry if available
            if not top_10_below.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        label=f"Price {input_previous_year}",
                        value=f"Rp {top_10_below[f'Price {input_previous_year}'].iloc[0]:,.0f}",
                    )

                with col2:
                    st.metric(
                        label="Lowest Gap",
                        value=f"{top_10_below['Gap Price'].iloc[0]:.2f}%",
                        delta=f"{top_10_below['Gap Price'].iloc[0] + float(input_abnormal):.2f}%",
                        delta_color="normal",
                    )

                with col3:
                    st.metric(
                        label=f"Price {input_current_year}",
                        value=f"Rp {top_10_below[f'Price {input_current_year}'].iloc[0]:,.0f}",
                    )
    # Source selection
    with st.container(border=True):
        st.subheader("Abnormal Number Per Source")
        sources = sorted(abnormal_cal_out["source"].unique())

        # Initialize session state if needed
        if "selected_source" not in st.session_state:
            st.session_state["selected_source"] = sources[0] if sources else ""

        selected_source = st.selectbox(
            "Choose a destination:", sources, index=sources.index(st.session_state["selected_source"])
        )
        st.session_state["selected_source"] = selected_source

        # Create and display chart
        if selected_source:
            chart = uv.create_pie_chart_out_house(abnormal_cal_out, selected_source, input_abnormal)
            st.plotly_chart(chart, use_container_width=True)

            # Calculate and display statistics
            filtered_data = abnormal_cal_out[abnormal_cal_out["source"] == selected_source]
            total_items_oh = len(filtered_data)

            if total_items_oh > 0:
                normal_count_oh = filtered_data[filtered_data["Status"] == "Normal"].shape[0]
                abnormal_above_oh = filtered_data[filtered_data["Status"] == f"Abnormal Above {input_abnormal}%"].shape[
                    0
                ]
                abnormal_below_oh = filtered_data[
                    filtered_data["Status"] == f"Abnormal Below -{input_abnormal}%"
                ].shape[0]

    with st.container(border=True):
        st.subheader(f"{selected_source} Summary Statistics")
        cols = st.columns(4)
        cols[0].metric("Total Items", total_items_oh)
        cols[1].metric("Normal", f"{normal_count_oh} ({normal_count_oh / total_items_oh * 100:.1f}%)")
        cols[2].metric("Above Threshold", f"{abnormal_above_oh} ({abnormal_above_oh / total_items_oh * 100:.1f}%)")
        cols[3].metric("Below Threshold", f"{abnormal_below_oh} ({abnormal_below_oh / total_items_oh * 100:.1f}%)")

    # Display download buttons
    section_name = "out_house"
    cols = st.columns(3, border=True)
    with cols[0]:
        st.subheader("Full Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel_out,
            file_name=f"{section_name}_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with cols[1]:
        st.subheader("Filtered Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel_filtered_out,
            file_name=f"{section_name}_filtered_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with cols[2]:
        st.subheader("Filtered Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel_per_part,
            file_name=f"{section_name}_per_part_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
except Exception as e:
    if "KeyError" in str(e):
        st.warning("There was an issue with your database query. Please check your input parameters.")

# ======================================== PACKING ========================================
st.divider()
st.header("PACKING")


# Cache query results for packing data
@st.cache_data(ttl="15m")
def get_packing_data(years, abnormal_threshold):
    try:
        status_items = conn.query(up.status_product_two_year(years))
        abnormal_cal = conn.query(up.packing_max_abnormal_cal(years, abnormal_threshold))
        return status_items, abnormal_cal
    except Exception as e:
        # st.warning(e)
        if "sqlalchemy.exc.ProgrammingError" in str(e) or "psycopg2.errors.SyntaxError" in str(e):
            st.warning("There was an issue with your database query. Please check your input parameters.")
            return pd.DataFrame(), pd.DataFrame()
        else:
            raise e


try:
    # Get packing data
    status_items_packing, abnormal_cal_packing = get_packing_data(years, input_abnormal)

    # Process data

    status_counts_packing = status_items_packing["Status"].value_counts()
    abnormal_counts_packing = abnormal_cal_packing["Status"].value_counts()
    explanation_counts_packing = abnormal_cal_packing["Explanation Status"].value_counts()

    # Generate Excel files
    generate_excel_packing = uf.convert_to_excel_format_packaging(
        abnormal_cal_packing, input_previous_year, input_current_year, int(input_abnormal)
    )

    abnormal_filter_packing = (abnormal_cal_packing["Status"] == f"Abnormal Above {input_abnormal}%") | (
        abnormal_cal_packing["Status"] == f"Abnormal Below {input_abnormal}%"
    )
    abnormal_filtered_packing = abnormal_cal_packing[abnormal_filter_packing]
    generate_excel_filtered_packing = uf.convert_to_excel_format_packaging(
        abnormal_filtered_packing, input_previous_year, input_current_year, int(input_abnormal)
    )

    # Display metrics
    mc = st.columns(3, border=True)
    with mc[0]:
        st.subheader("Item Status")
        display_status_metrics(status_counts_packing)

    with mc[1]:
        st.subheader("Abnormal Number")
        m = st.columns(3, gap="small")
        statuses = [f"Abnormal Above {input_abnormal}%", "Normal", f"Abnormal Below -{input_abnormal}%"]
        for i, status in enumerate(statuses):
            with m[i]:
                st.metric(label=status, value=abnormal_counts_packing.get(status, 0))
    with mc[2]:
        st.subheader("Explanation Status")
        m = st.columns(3, gap="small")
        statuses = ["Approved", "Disapproved", "Awaiting"]
        for i, status in enumerate(statuses):
            with m[i]:
                st.metric(label=status, value=explanation_counts_packing.get(status, 0))

    # Destination selection
    with st.container(border=True):
        st.subheader("Abnormal Number Per Destination")
        destinations = sorted(abnormal_cal_packing["destination"].unique())

        # Initialize session state if needed
        if "selected_destination" not in st.session_state:
            st.session_state["selected_destination"] = destinations[0] if destinations else ""

        selected_destination = st.selectbox(
            "Choose a destination:",
            destinations,
            index=destinations.index(st.session_state["selected_destination"])
            if st.session_state["selected_destination"] in destinations
            else 0,
        )
        st.session_state["selected_destination"] = selected_destination

        # Create and display chart
        if selected_destination:
            chart = uv.create_pie_chart_packing(abnormal_cal_packing, selected_destination, input_abnormal)
            st.plotly_chart(chart, use_container_width=True)

            # Calculate and display statistics
            filtered_data = abnormal_cal_packing[abnormal_cal_packing["destination"] == selected_destination]
            total_items = len(filtered_data)

            if total_items > 0:
                normal_count = filtered_data[filtered_data["Status"] == "Normal"].shape[0]
                abnormal_above = filtered_data[filtered_data["Status"] == f"Abnormal Above {input_abnormal}%"].shape[0]
                abnormal_below = filtered_data[filtered_data["Status"] == f"Abnormal Below -{input_abnormal}%"].shape[0]

    with st.container(border=True):
        st.subheader(f"{selected_destination} Summary Statistics")
        cols = st.columns(4)
        cols[0].metric("Total Items", total_items)
        cols[1].metric("Normal", f"{normal_count} ({normal_count / total_items * 100:.1f}%)")
        cols[2].metric("Above Threshold", f"{abnormal_above} ({abnormal_above / total_items * 100:.1f}%)")
        cols[3].metric("Below Threshold", f"{abnormal_below} ({abnormal_below / total_items * 100:.1f}%)")

    # Display download buttons
    display_download_buttons(generate_excel_packing, generate_excel_filtered_packing, "packing")
except Exception as e:
    if "KeyError" in str(e):
        st.warning("There was an issue with your database query. Please check your input parameters.")

st.divider()
st.subheader("PDF")
if st.button("Generate PDF"):
    with st.spinner("Generating PDF..."):
        pdf_data = ag.generate_pdf_report(
            years=years,
            df_inhouse=full_abnormal_cal_impl,
            df_outhouse=abnormal_cal_out,
            df_packing=abnormal_cal_packing,
            boundaries=input_abnormal,
        )

        pdf_bytes = bytes(pdf_data)
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"Report Abnomality {input_current_year}-{input_previous_year}.pdf",
            mime="application/pdf",
        )
