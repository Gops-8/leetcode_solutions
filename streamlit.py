import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import databricks.sql as dbsql  # Ensure you have installed: pip install databricks-sql-connector

# -------------------------
# Page Configuration and Custom CSS
# -------------------------
st.set_page_config(
    page_title="FOrecast Viewer for Integrity SAAS",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide default Streamlit elements (menu, footer, sidebar, deploy button)
hide_elements_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    button[title="Deploy other apps"] {display: none;}
    </style>
"""
st.markdown(hide_elements_style, unsafe_allow_html=True)

# Custom CSS for green accent on buttons
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.5em 1em;
        border-radius: 4px;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------
# ForecastDataRetriever Class
# -------------------------
class ForecastDataRetriever:
    def __init__(self):
        """
        Establish a connection to the Databricks Delta table (Hive metastore)
        using credentials provided in st.secrets. The st.secrets file should include:

            [databricks]
            server_hostname = "your-databricks-hostname"
            http_path = "your-http-path"
            access_token = "your-access-token"
            table_name = "your_database.your_table"   # Optional; default is "forecast_data"

        """
        self.conn = dbsql.connect(
            server_hostname=st.secrets["databricks"]["server_hostname"],
            http_path=st.secrets["databricks"]["http_path"],
            access_token=st.secrets["databricks"]["access_token"]
        )
        self.table_name = st.secrets["databricks"].get("table_name", "forecast_data")
    
    def _query_to_df(self, query: str) -> pd.DataFrame:
        """
        Helper method to execute a SQL query and return the results as a DataFrame.
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
        return pd.DataFrame(rows, columns=col_names)
    
    def get_unique_clients(self) -> list:
        """
        Pull distinct client names from the TenentID column.
        """
        query = f"SELECT DISTINCT TenentID FROM {self.table_name}"
        df = self._query_to_df(query)
        return df["TenentID"].tolist()
    
    def get_start_date_and_cashpool_groups(self, client: str):
        """
        For the given client, return:
          - The earliest ValueDate (start date).
          - The unique CashPoolDescription values (cashpool groups).
        """
        # Query for the earliest date for the selected client.
        query_date = f"""
            SELECT MIN(ValueDate) AS start_date
            FROM {self.table_name}
            WHERE TenentID = '{client}'
        """
        df_date = self._query_to_df(query_date)
        if df_date.empty or pd.isnull(df_date.iloc[0]["start_date"]):
            return None, []
        start_date = df_date.iloc[0]["start_date"]
        # Convert to a date object if necessary.
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        elif isinstance(start_date, pd.Timestamp):
            start_date = start_date.date()
        
        # Query for unique cashpool groups for the client.
        query_cashpools = f"""
            SELECT DISTINCT CashPoolDescription
            FROM {self.table_name}
            WHERE TenentID = '{client}'
        """
        df_cashpools = self._query_to_df(query_cashpools)
        cashpool_groups = df_cashpools["CashPoolDescription"].tolist()
        return start_date, cashpool_groups
    
    def get_forecast_data(self, client: str, selected_cashpools: list, no_of_days: int):
        """
        Based on the selected client, cashpool groups, and number of days:
          - Compute the end date (start_date + no_of_days).
          - Pull rows that match the filters.
        """
        start_date, _ = self.get_start_date_and_cashpool_groups(client)
        if start_date is None:
            return pd.DataFrame(), None, None
        
        end_date = start_date + timedelta(days=no_of_days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Build the SQL query
        query = f"""
            SELECT *
            FROM {self.table_name}
            WHERE TenentID = '{client}'
              AND ValueDate >= '{start_date_str}'
              AND ValueDate <= '{end_date_str}'
        """
        if selected_cashpools:
            # Create a comma-separated list for the IN clause.
            groups_str = ",".join(f"'{grp}'" for grp in selected_cashpools)
            query += f" AND CashPoolDescription IN ({groups_str})"
        
        df = self._query_to_df(query)
        return df, start_date, end_date

# -------------------------
# Main Streamlit Application UI
# -------------------------
st.title("FOrecast Viewer for Integrity SAAS")

# Instantiate the data retriever.
data_retriever = ForecastDataRetriever()

# --- Top Row: Client Selection and Future Timespan ---
col1, col2, col3 = st.columns(3)
with col1:
    unique_clients = data_retriever.get_unique_clients()
    client = st.selectbox("Select Client", options=unique_clients)

with col2:
    start_date, available_cashpools = data_retriever.get_start_date_and_cashpool_groups(client)
    if start_date:
        st.write(f"**Start Date:** {start_date}")
    else:
        st.write("No data available for the selected client.")

with col3:
    no_of_days = st.slider("Future Timespan (Days)", min_value=5, max_value=15, value=5)

# --- Second Row: Cashpool Group Selection ---
col4, col5 = st.columns(2)
with col4:
    selected_cashpools = st.multiselect(
        "Select CashPool Groups",
        options=available_cashpools,
        default=available_cashpools
    )
with col5:
    st.empty()  # Additional inputs can be added here if needed.

# --- Forecast Data Retrieval and Display ---
if st.button("Show Forecast"):
    forecast_df, start_date, end_date = data_retriever.get_forecast_data(client, selected_cashpools, no_of_days)
    
    if forecast_df.empty:
        st.warning("No data found for the selected filters.")
    else:
        st.subheader("Forecast Results (Transposed)")
        # Transpose the DataFrame before displaying.
        st.dataframe(forecast_df.T)
        
        st.subheader("Forecast Plot")
        # Aggregate the forecasted amounts per date.
        plot_data = forecast_df.groupby("ValueDate")["ForecastedClosingBalance"].sum().reset_index()
        plot_data = plot_data.sort_values("ValueDate")
        # Set ValueDate as index for a proper line chart.
        plot_data = plot_data.set_index("ValueDate")
        st.line_chart(plot_data)
