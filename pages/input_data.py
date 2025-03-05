import streamlit as st
import pandas as pd

from psycopg2 import pool
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

import utils.sql_in_house as us
import utils.sql_packing as up
import utils.sql_out_house as uo

with open("database-dev.yaml", "r", encoding="utf-8") as file:
    database = yaml.load(file, Loader=SafeLoader)

# Configuration - in production, use st.secrets or environment variables
DB_HOST = database["database"]["host"]
DB_PORT = database["database"]["port"]
DB_NAME = database["database"]["name"]
DB_USER = database["database"]["user"]
DB_PASSWORD = database["database"]["password"]

# Initialize connection pool
connection_pool = None


def init_connection_pool():
    """Initialize a connection pool for database operations"""
    global connection_pool
    try:
        connection_pool = pool.SimpleConnectionPool(
            1, 10, host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        return True
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return False


def get_connection():
    """Get a connection from the pool"""
    if connection_pool:
        return connection_pool.getconn()
    else:
        if init_connection_pool():
            return connection_pool.getconn()
    return None


def release_connection(conn):
    """Release a connection back to the pool"""
    if connection_pool:
        connection_pool.putconn(conn)


st.set_page_config(page_title="TMMIN PBMD - Data Input", layout="wide")
st.image("images/toyota.png", width=250)
st.header("DATA INPUT - PBMD")

# Authentication (same as main app)
with open("config.yaml", "r", encoding="utf-8") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"], config["cookie"]["name"], config["cookie"]["key"], config["cookie"]["expiry_days"]
)

# Check authentication status
if "authentication_status" not in st.session_state or st.session_state["authentication_status"] is None:
    st.warning("Please log in from the main dashboard page first")
    st.stop()
elif st.session_state["authentication_status"] is False:
    st.error("Authentication failed. Please log in from the main dashboard page")
    st.stop()

# Display welcome message and logout button
m = st.columns((1, 0.08))
with m[0]:
    st.subheader(f"Welcome {st.session_state['name']}")
with m[1]:
    authenticator.logout()

st.page_link("app.py", label="Input Data", icon="📊")

# Select data type to upload
data_type = st.selectbox("Select Data Type", ["IN HOUSE COST", "OUT HOUSE COST", "PACKING COST"])

# File uploader
uploaded_file = st.file_uploader("Upload Data File", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names

        table_mapping = {"IN HOUSE COST": "in_house", "OUT HOUSE COST": "out_house", "PACKING COST": "packing"}
        table_name = table_mapping.get(data_type)

        try:
            uploaded_sheets = []
            for name in sheet_names:
                if data_type == "IN HOUSE COST":
                    df = excel_file.parse(name, header=[0, 1])
                    # us.import_data(get_connection(), df)
                elif data_type == "OUT HOUSE COST":
                    df = excel_file.parse(name, header=[0, 1])
                    df.columns = [
                        "part_no",
                        "part_name",
                        "source",
                        "price_prev",
                        "price_curr",
                        "price_gap",
                        "explanation",
                    ]
                    st.dataframe(df)
                    # uo.import_data(get_connection(), df)
                elif data_type == "PACKING COST":
                    df = excel_file.parse(name, header=[0, 1])
                    # up.import_data(get_connection(), df)

                uploaded_sheets.append(name)

            st.success(f"All sheets ({', '.join(uploaded_sheets)}) successfully uploaded to {data_type} tables!")
        except Exception as e:
            st.error(f"Error uploading data: {str(e)}")

    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
