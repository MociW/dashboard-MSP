import streamlit as st
import repository.psql.conn as conn
import repository.out_house as ro
import repository.in_house as ri
import repository.packing as rp
import pandas as pd
import os

# Initialize session state variables if they don't exist
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False
if "name" not in st.session_state:
    st.session_state["name"] = ""
if "failed_data" not in st.session_state:
    st.session_state["failed_data"] = None

st.set_page_config(page_title="PBMD - Dashboard", layout="wide")
st.image("images/toyota.png", width=250)
st.header("📋 UPDATE DATABASE - PBMD")

# Authentication status checking
if st.session_state["authentication_status"]:
    # User info, input data button, and logout
    col1, col2 = st.columns([0.8, 0.20])
    with col1:
        st.subheader(f"Welcome {st.session_state['name']}")
    with col2:
        if st.button("🗒️ Dashboard", use_container_width=True):
            st.switch_page("app.py")

    # Create input form
    with st.form(key="input_form"):
        st.subheader("Data Input Form")

        # Dropdown for selecting data type
        data_type = st.selectbox("Select Data Type", options=["INHOUSE", "OUTHOUSE", "PACKING"], index=0)

        # File uploader for Excel files
        uploaded_file = st.file_uploader(
            "Upload Excel File", type=["xlsx"], help="Please upload an Excel file with the required format"
        )

        # Submit button
        submit_button = st.form_submit_button(label="Submit Data", type="primary")

    # Process form submission outside the form
    if submit_button:
        if uploaded_file is not None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            config_path = os.path.join(project_root, "config/database-dev.yaml")
            config = conn.load_config(config_path)
            if not config:
                st.error("Failed to load configuration. Exiting.")
            else:
                db_connection = conn.DatabaseConnection(config["database"])
                try:
                    result = None
                    if data_type == "INHOUSE":
                        result = ri.update_in_house_data(uploaded_file, db_connection)
                    elif data_type == "OUTHOUSE":
                        result = ro.update_out_house_data(uploaded_file, db_connection)
                    elif data_type == "PACKING":
                        result = rp.update_packing_data(uploaded_file, db_connection)

                    # Display results
                    if result:
                        st.success(
                            f"✅ Successfully processed {result['success']} out of {result['total']} records in {uploaded_file.name}"
                        )

                        if result["failed"] > 0:
                            st.warning(f"⚠️ {result['failed']} records failed to import")

                            # Store failed data in session state
                            st.session_state["failed_data"] = result["failed_parts"]

                            # Create a dataframe of failed parts for better display
                            failed_df = pd.DataFrame(result["failed_parts"])

                            # Use expander to keep the UI clean
                            with st.expander("View Failed Records"):
                                st.dataframe(failed_df)

                                # Add option to download failed records as CSV
                                excel = failed_df.to_excel(index=False)
                                st.download_button(
                                    label="Download Failed Records Excel",
                                    data=excel,
                                    file_name="failed_imports.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                )
                    else:
                        st.success(f"✅ Successfully updated {uploaded_file.name} to {data_type.lower()} database")
                except Exception as e:
                    st.error(f"❌ Failed to update {uploaded_file.name} to {data_type.lower()} database: {str(e)}")
        else:
            st.error("Please upload a file first")

    # Template download section (outside the form)
    st.subheader("Download Templates")
    col1, col2, col3, col4 = st.columns([0.18, 0.18, 0.18, 0.4], gap="small")
    with col1:
        try:
            # Read the template file
            with open("resource/in_house_template_input_database.xlsx", "rb") as template_file:
                template_bytes_in = template_file.read()

            st.download_button(
                label="Download Template Inhouse",
                data=template_bytes_in,
                file_name="in_house_template_input_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except FileNotFoundError:
            st.error("Template file not found")

    with col2:
        try:
            # Read the template file
            with open("resource/out_house_template_input_database.xlsx", "rb") as template_file:
                template_bytes_out = template_file.read()

            st.download_button(
                label="Download Template Outhouse",
                data=template_bytes_out,
                file_name="out_house_template_input_database.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except FileNotFoundError:
            st.error("Template file not found")

    with col3:
        try:
            # Read the template file
            with open("resource/packing_template_input_database.xlsx", "rb") as template_file:
                template_bytes_packing = template_file.read()

            st.download_button(
                label="Download Template Packing",
                data=template_bytes_packing,
                file_name="packing_template_input_database.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except FileNotFoundError:
            st.error("Template file not found")

else:
    st.switch_page("app.py")
