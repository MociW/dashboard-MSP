import streamlit as st
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

st.set_page_config(page_title="TMMIN PBMD - Dashboard", layout="wide")
st.image("images/toyota.png", width=250)
st.header("DASHBOARD ABNORMALITY MANAGEMENT  - PBMD")

# # Sidebar navigation
# st.sidebar.page_link("app.py", label="Dashboard", icon="📊")
# st.sidebar.page_link("pages/in_house.py", label="IN HOUSE COST", icon="🏠")
# st.sidebar.page_link("pages/out_house.py", label="OUT HOUSE COST", icon="🌎")
# st.sidebar.page_link("pages/packing.py", label="PACKING COST", icon="📦")

with open("config.yaml", "r", encoding="utf-8") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"], config["cookie"]["name"], config["cookie"]["key"], config["cookie"]["expiry_days"]
)

try:
    authenticator.login()
except LoginError as e:
    st.error(e)


if st.session_state["authentication_status"]:
    m = st.columns((1, 0.08))
    with m[0]:
        st.subheader(f"Welcome {st.session_state['name']}")
    with m[1]:
        authenticator.logout()
    st.page_link("pages/input_data.py", label="Input Data", icon="📥")
elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")

conn = st.connection("postgresql", type="sql")

# ======================================== FORM ========================================
if st.session_state["authentication_status"]:
    with st.form(key="form_input"):
        m7, m8 = st.columns((1, 1))
        m3, m4, m5 = st.columns((1, 1, 1))
        input_current_year = m8.text_input("Input Current Year")
        input_previous_year = m7.text_input("Input Previous Year")
        input_abnormal = m3.text_input("Abnormal Boundaries (%)")
        submitButton = st.form_submit_button(label="Submit")

        if submitButton:
            st.session_state["years"] = [input_previous_year, input_current_year]
            st.session_state["input_abnormal"] = input_abnormal

# ======================================== IN HOUSE ========================================
if "years" in st.session_state and "input_abnormal" in st.session_state and st.session_state["authentication_status"]:
    st.header("IN HOUSE")

    years = st.session_state["years"]
    input_abnormal = st.session_state["input_abnormal"]

    status_items = us.status_product_two_year(years)
    status_items_impl = conn.query(status_items, ttl="15m")
    status_items_impl = status_items_impl["Status"].value_counts()

    # --------------------------------------- Abnormal Calculation ---------------------------------------
    abnormal_cal = us.abnormal_cal(years, input_abnormal)
    abnormal_cal_impl = conn.query(abnormal_cal, ttl="15m")
    abnormal_cal_num = abnormal_cal_impl["Status Abnormal"].value_counts()

    full_abnormal_cal = us.full_abnormal_cal(years, input_abnormal)
    full_abnormal_cal_impl = conn.query(full_abnormal_cal, ttl="15m")
    lva_abnormal_number = full_abnormal_cal_impl["LVA Status"].value_counts()
    non_lva_abnormal_number = full_abnormal_cal_impl["Non LVA Status"].value_counts()
    tooling_abnormal_nummber = full_abnormal_cal_impl["Tooling Status"].value_counts()
    process_cost_abnormal_number = full_abnormal_cal_impl["Process Cost Status"].value_counts()
    total_cost_abnormal_number = full_abnormal_cal_impl["Total Cost Status"].value_counts()

    # --------------------------------------- Generate Excel ---------------------------------------
    df_generate = abnormal_cal_impl.drop("Status Abnormal", axis=1)
    generate_excel = uf.convert_to_excel_in_house(
        df_generate, input_previous_year, input_current_year, int(input_abnormal)
    )

    abnormal_cal_impl_filtered = abnormal_cal_impl[abnormal_cal_impl["Status Abnormal"] == "Abnormal"]
    abnormal_cal_impl_filtered = abnormal_cal_impl_filtered.drop("Status Abnormal", axis=1)
    generate_excel_filtered = uf.convert_to_excel_in_house(
        abnormal_cal_impl_filtered, input_previous_year, input_current_year, int(input_abnormal)
    )

    mc = st.columns(2, border=True)
    with mc[0]:
        st.subheader("Item Status")
        m = st.columns(3, gap="small")
        with m[0]:
            if "Deleted" in status_items_impl:
                st.metric(label="Deleted", value=status_items_impl["Deleted"])
            else:
                st.metric(label="Deleted", value=0)

        with m[1]:
            if "Remain" in status_items_impl:
                st.metric(label="Remain", value=status_items_impl["Remain"])
            else:
                st.metric(label="Remain", value=0)

        with m[2]:
            if "New" in status_items_impl:
                st.metric(label="New", value=status_items_impl["New"])
            else:
                st.metric(label="New", value=0)

    with mc[1]:
        st.subheader("Abnormal Number")
        m = st.columns(2, gap="small")
        with m[0]:
            val_above = "Abnormal"
            if val_above in abnormal_cal_num:
                st.metric(label=val_above, value=abnormal_cal_num[val_above])
            else:
                st.metric(label=val_above, value=0)

        with m[1]:
            if "Normal" in abnormal_cal_num:
                st.metric(label="Normal", value=abnormal_cal_num["Normal"])
            else:
                st.metric(label="Normal", value=0)

    uv.pie_char_with_total_counts(total_cost_abnormal_number, "Total Cost Abnormal", input_abnormal)
    uv.pie_char_with_total_counts(lva_abnormal_number, "LVA Abnormal", input_abnormal)
    uv.pie_char_with_total_counts(non_lva_abnormal_number, "Non LVA Abnormal", input_abnormal)
    uv.pie_char_with_total_counts(tooling_abnormal_nummber, "Tooling Abnormal", input_abnormal)
    uv.pie_char_with_total_counts(process_cost_abnormal_number, "Process Cost Abnormal", input_abnormal)

    m = st.columns(2, border=True)
    with m[0]:
        st.subheader("Full Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel,
            file_name=f"in_house_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with m[1]:
        st.subheader("Filtered Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel_filtered,
            file_name=f"in_house_filtered_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ======================================== OUT HOUSE ========================================
if "years" in st.session_state and "input_abnormal" in st.session_state and st.session_state["authentication_status"]:
    st.divider()
    st.header("OUT HOUSE")

    years = st.session_state["years"]
    input_abnormal = st.session_state["input_abnormal"]

    status_items = uo.status_product_two_year_out_house(years)
    status_items_impl = conn.query(status_items, ttl="15m")
    status_items_impl = status_items_impl["Status"].value_counts()

    abnormal_cal_out_house = uo.abnormal_cal_out_house(years, input_abnormal)
    abnormal_cal_out_house_impl = conn.query(abnormal_cal_out_house, ttl="15m")
    abnormal_cal_out_house_num = abnormal_cal_out_house_impl["Status"].value_counts()

    df_generate_out = abnormal_cal_out_house_impl.drop("Status", axis=1)
    generate_excel_out = uf.convert_to_excel_format_out_house(
        df_generate_out, input_previous_year, input_current_year, int(input_abnormal)
    )

    abnormal_cal_impl_filtered_out = abnormal_cal_out_house_impl[
        (abnormal_cal_out_house_impl["Status"] == f"Abnormal Above {input_abnormal}%")
        | (abnormal_cal_out_house_impl["Status"] == f"Abnormal Below -{input_abnormal}%")
    ]
    abnormal_cal_impl_filtered_out = abnormal_cal_impl_filtered_out.drop("Status", axis=1)
    generate_excel_filtered_out = uf.convert_to_excel_format_out_house(
        abnormal_cal_impl_filtered_out, input_previous_year, input_current_year, int(input_abnormal)
    )

    mc = st.columns(2, border=True)
    with mc[0]:
        st.subheader("Item Status")
        m = st.columns(3, gap="small")
        with m[0]:
            if "Deleted" in status_items_impl:
                st.metric(label="Deleted", value=status_items_impl["Deleted"])
            else:
                st.metric(label="Deleted", value=0)

        with m[1]:
            if "Remain" in status_items_impl:
                st.metric(label="Remain", value=status_items_impl["Remain"])
            else:
                st.metric(label="Remain", value=0)

        with m[2]:
            if "New" in status_items_impl:
                st.metric(label="New", value=status_items_impl["New"])
            else:
                st.metric(label="New", value=0)

    with mc[1]:
        st.subheader("Abnormal Number")
        m = st.columns(3, gap="small")
        with m[0]:
            val_above = f"Abnormal Above {input_abnormal}%"
            if val_above in abnormal_cal_out_house_num:
                st.metric(label=val_above, value=abnormal_cal_out_house_num[val_above])
            else:
                st.metric(label=val_above, value=0)

        with m[1]:
            if "Normal" in abnormal_cal_out_house_num:
                st.metric(label="Normal", value=abnormal_cal_out_house_num["Normal"])
            else:
                st.metric(label="Normal", value=0)

        with m[2]:
            val_under = f"Abnormal Below -{input_abnormal}%"
            if val_under in abnormal_cal_out_house_num:
                st.metric(label=val_under, value=abnormal_cal_out_house_num[val_under])
            else:
                st.metric(label=val_under, value=0)

    with st.container(border=True):
        pastel_colors = px.colors.qualitative.Pastel
        fig = px.pie(
            abnormal_cal_out_house_num,
            values=abnormal_cal_out_house_num.values,
            names=abnormal_cal_out_house_num.index,
            title="Out House Cost Abnormality Distribution",
            color=abnormal_cal_out_house_num.index,
            color_discrete_map={
                "Normal": pastel_colors[0],
                f"Abnormal Above {input_abnormal}%": pastel_colors[1],
                f"Abnormal Below -{input_abnormal}%": pastel_colors[2],
            },
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    n = st.columns(2, border=True)
    with n[0]:
        st.subheader(f"Top 10 Above {input_abnormal}%")
        dataframe_out_house_above = abnormal_cal_out_house_impl.dropna(subset=["Gap Price"])
        dataframe_out_house_above = dataframe_out_house_above.drop("Status", axis=1, errors="ignore")
        st.dataframe(dataframe_out_house_above.head(10))

    with n[1]:
        st.subheader(f"Top 10 Below -{input_abnormal}%")
        dataframe_out_house_below = abnormal_cal_out_house_impl.dropna(subset=["Gap Price"])
        dataframe_out_house_below = dataframe_out_house_below.drop("Status", axis=1, errors="ignore")
        dataframe_out_house_below = dataframe_out_house_below.sort_values("Gap Price")
        st.dataframe(dataframe_out_house_below.head(10))

    if "selected_source" not in st.session_state:
        st.session_state["selected_source"] = abnormal_cal_out_house_impl["source"].unique()[0]

    with st.container(border=True):
        st.subheader("Abnormal Number Per Source")
        sources = sorted(abnormal_cal_out_house_impl["source"].unique())
        selected_source = st.selectbox("Choose a destination:", sources, index=0)

        # Store selection in session state
        if selected_source:
            st.session_state["selected_source"] = selected_source

        # Generate and display pie chart
        chart = uv.create_pie_chart_out_house(
            abnormal_cal_out_house_impl, st.session_state["selected_source"], input_abnormal
        )
        st.plotly_chart(chart, use_container_width=True)

        # Display statistics
        filtered_data = abnormal_cal_out_house_impl[
            abnormal_cal_out_house_impl["source"] == st.session_state["selected_source"]
        ]
        total_items_oh = len(filtered_data)
        normal_count_oh = filtered_data[filtered_data["Status"] == "Normal"].shape[0]
        abnormal_above_oh = filtered_data[filtered_data["Status"] == f"Abnormal Above {input_abnormal}%"].shape[0]
        abnormal_below_oh = filtered_data[filtered_data["Status"] == f"Abnormal Below -{input_abnormal}%"].shape[0]

    with st.container(border=True):
        st.subheader(f"{st.session_state['selected_source']} Summary Statistics")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        stat_col1.metric("Total Items", total_items_oh)
        stat_col2.metric("Normal", f"{normal_count_oh} ({normal_count_oh / total_items_oh * 100:.1f}%)")
        stat_col3.metric("Above Threshold", f"{abnormal_above_oh} ({abnormal_above_oh / total_items_oh * 100:.1f}%)")
        stat_col4.metric("Below Threshold", f"{abnormal_below_oh} ({abnormal_below_oh / total_items_oh * 100:.1f}%)")

    m = st.columns(3, border=True)
    with m[0]:
        st.subheader("Full Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel_out,
            file_name=f"out_house_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with m[1]:
        st.subheader("Filtered Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel_filtered_out,
            file_name=f"out_house_filtered_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with m[2]:
        st.subheader("")

# ======================================== PACKING ========================================
if "years" in st.session_state and "input_abnormal" in st.session_state and st.session_state["authentication_status"]:
    years = st.session_state["years"]
    input_abnormal = st.session_state["input_abnormal"]

    st.divider()
    st.header("PACKING")

    status_items = up.status_product_two_year(years)
    status_items_impl = conn.query(status_items, ttl="15m")
    status_items_impl = status_items_impl["Status"].value_counts()

    abnormal_cal_packing = up.packing_max_abnormal_cal(years, input_abnormal)
    abnormal_cal_packing_impl = conn.query(abnormal_cal_packing, ttl="15m")
    abnormal_cal_packing_num = abnormal_cal_packing_impl["Status"].value_counts()

    st.dataframe(abnormal_cal_packing_impl)

    df_generate_packing = abnormal_cal_packing_impl.drop("Status", axis=1)
    generate_excel_packing = uf.convert_to_excel_format_packaging(
        abnormal_cal_packing_impl, input_previous_year, input_current_year, int(input_abnormal)
    )

    abnormal_cal_impl_filtered_packing = abnormal_cal_packing_impl[
        (abnormal_cal_packing_impl["Status"] == f"Abnormal Above {input_abnormal}%")
        | (abnormal_cal_packing_impl["Status"] == f"Abnormal Below {input_abnormal}%")
    ]

    generate_excel_filtered_packing = uf.convert_to_excel_format_packaging(
        abnormal_cal_impl_filtered_packing, input_previous_year, input_current_year, int(input_abnormal)
    )

    mc = st.columns(2, border=True)
    with mc[0]:
        st.subheader("Item Status")
        m = st.columns(3, gap="small")
        with m[0]:
            if "Deleted" in status_items_impl:
                st.metric(label="Deleted", value=status_items_impl["Deleted"])
            else:
                st.metric(label="Deleted", value=0)

        with m[1]:
            if "Remain" in status_items_impl:
                st.metric(label="Remain", value=status_items_impl["Remain"])
            else:
                st.metric(label="Remain", value=0)

        with m[2]:
            if "New" in status_items_impl:
                st.metric(label="New", value=status_items_impl["New"])
            else:
                st.metric(label="New", value=0)
    with mc[1]:
        st.subheader("Abnormal Number")
        m = st.columns(3, gap="small")
        with m[0]:
            val_above = f"Abnormal Above {input_abnormal}%"
            if val_above in abnormal_cal_packing_num:
                st.metric(label=val_above, value=abnormal_cal_packing_num[val_above])
            else:
                st.metric(label=val_above, value=0)

        with m[1]:
            if "Normal" in abnormal_cal_packing_num:
                st.metric(label="Normal", value=abnormal_cal_packing_num["Normal"])
            else:
                st.metric(label="Normal", value=0)

        with m[2]:
            val_under = f"Abnormal Below -{input_abnormal}%"
            if val_under in abnormal_cal_packing_num:
                st.metric(label=val_under, value=abnormal_cal_packing_num[val_under])
            else:
                st.metric(label=val_under, value=0)

    # Persist selected destination
    if "selected_destination" not in st.session_state:
        st.session_state["selected_destination"] = abnormal_cal_packing_impl["destination"].unique()[0]

    with st.container(border=True):
        st.subheader("Abnormal Number Per Destination")
        destinations = sorted(abnormal_cal_packing_impl["destination"].unique())
        selected_destination = st.selectbox("Choose a destination:", destinations, index=0)

        # Store selection in session state
        if selected_destination:
            st.session_state["selected_destination"] = selected_destination

        # Generate and display pie chart
        chart = uv.create_pie_chart_packing(
            abnormal_cal_packing_impl, st.session_state["selected_destination"], input_abnormal
        )
        st.plotly_chart(chart, use_container_width=True)

        # Display statistics
        filtered_data = abnormal_cal_packing_impl[
            abnormal_cal_packing_impl["destination"] == st.session_state["selected_destination"]
        ]
        total_items = len(filtered_data)
        normal_count = filtered_data[filtered_data["Status"] == "Normal"].shape[0]
        abnormal_above = filtered_data[filtered_data["Status"] == f"Abnormal Above {input_abnormal}%"].shape[0]
        abnormal_below = filtered_data[filtered_data["Status"] == f"Abnormal Below -{input_abnormal}%"].shape[0]

    with st.container(border=True):
        st.subheader(f"{st.session_state['selected_destination']} Summary Statistics")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        stat_col1.metric("Total Items", total_items)
        stat_col2.metric("Normal", f"{normal_count} ({normal_count / total_items * 100:.1f}%)")
        stat_col3.metric("Above Threshold", f"{abnormal_above} ({abnormal_above / total_items * 100:.1f}%)")
        stat_col4.metric("Below Threshold", f"{abnormal_below} ({abnormal_below / total_items * 100:.1f}%)")

    m = st.columns(2, border=True)
    with m[0]:
        st.subheader("Full Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel_packing,
            file_name=f"packing_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with m[1]:
        st.subheader("Filtered Excel")
        st.download_button(
            label="Download Excel File",
            data=generate_excel_filtered_packing,
            file_name=f"packing_filtered_{input_previous_year}_{input_current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
