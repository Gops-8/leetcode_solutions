import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import databricks.sql as dbsql  # Ensure you have installed: pip install databricks-sql-connector

# -------------------------
# Page Configuration and Custom CSS
# -------------------------
st.set_page_config(
    page_title="Forecast Viewer for Integrity SAAS",
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
        using credentials provided in st.secrets.
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
    
    def get_forecast_data(self, client: str, selected_cashpools: list, start_date: date, end_date: date):
        """
        Based on the selected client, cashpool groups, and date range:
          - Pull rows that match the filters.
        """
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
        return df

# -------------------------
# Main Streamlit Application UI
# -------------------------
st.title("Forecast Viewer for Integrity SAAS")

# Instantiate the data retriever.
data_retriever = ForecastDataRetriever()

# --- Top Row: Client Selection and Date Range ---
col1, col2, col3 = st.columns(3)
with col1:
    unique_clients = data_retriever.get_unique_clients()
    client = st.selectbox("Select Client", options=unique_clients)

# Initialize date range variables
start_date_selected = None
end_date_selected = None

with col2:
    start_date, available_cashpools = data_retriever.get_start_date_and_cashpool_groups(client)
    if start_date:
        # Calendar input for date range selection
        date_range = st.date_input(
            "Select Date Range",
            value=(start_date, date.today()),
            min_value=start_date,
            max_value=date.today()
        )
        if len(date_range) == 2:
            start_date_selected, end_date_selected = date_range
        else:
            st.error("Please select a valid date range (start and end dates).")
    else:
        st.write("No data available for the selected client.")

with col3:
    st.empty()  # Additional inputs can be added here if needed.

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
    if not selected_cashpools:
        st.error("Please select at least one CashPool Group.")
    elif start_date_selected is None or end_date_selected is None:
        st.error("Please select a valid date range.")
    else:
        forecast_df = data_retriever.get_forecast_data(client, selected_cashpools, start_date_selected, end_date_selected)
        
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
