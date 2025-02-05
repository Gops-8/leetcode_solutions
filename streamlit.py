import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# -------------------------
# Load CSV Data
# -------------------------
DATA_FILE = "sample_data.csv"

@st.cache_data
def load_data():
    # Parse the ValueDate column as dates
    df = pd.read_csv(DATA_FILE, parse_dates=["ValueDate"])
    # Convert ValueDate to date objects (if needed)
    df["ValueDate"] = df["ValueDate"].dt.date
    return df

data = load_data()

# -------------------------
# ForecastDataRetriever Class Using CSV Data
# -------------------------
class ForecastDataRetriever:
    def __init__(self, data):
        self.data = data
    
    def get_unique_clients(self) -> list:
        """Return a list of unique TenentIDs (client names) from the data."""
        return self.data["TenentID"].unique().tolist()
    
    def get_start_date_and_cashpool_groups(self, client: str):
        """For the selected client, return the earliest ValueDate and unique CashPoolDescription values."""
        client_data = self.data[self.data["TenentID"] == client]
        if client_data.empty:
            return None, []
        start_date = client_data["ValueDate"].min()
        cashpool_groups = client_data["CashPoolDescription"].unique().tolist()
        return start_date, cashpool_groups
    
    def get_forecast_data(self, client: str, selected_cashpools: list, no_of_days: int):
        """
        Based on the selected client, cashpool groups, and number of days:
          - Calculate the end date (start_date + no_of_days).
          - Return rows that match the client, the date range, and (if selected) the cashpool groups.
        """
        start_date, _ = self.get_start_date_and_cashpool_groups(client)
        if start_date is None:
            return pd.DataFrame(), None, None
        
        end_date = start_date + timedelta(days=no_of_days)
        # Filter data by client and date range.
        df_filtered = self.data[
            (self.data["TenentID"] == client) &
            (self.data["ValueDate"] >= start_date) &
            (self.data["ValueDate"] <= end_date)
        ]
        # Further filter by cashpool groups if provided.
        if selected_cashpools:
            df_filtered = df_filtered[df_filtered["CashPoolDescription"].isin(selected_cashpools)]
        
        return df_filtered.reset_index(drop=True), start_date, end_date

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
# Fixed Header with FIS Logo and Application Name
# -------------------------
header_html = """
<div id="header" style="
    position: fixed; 
    top: 0; 
    left: 0; 
    right: 0; 
    border: 2px solid #4CAF50; 
    padding: 5px 10px; 
    display: flex; 
    align-items: center; 
    justify-content: space-between; 
    background-color: white; 
    z-index: 1000;">
    <div>
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/FIS_Global_logo.svg/1200px-FIS_Global_logo.svg.png" 
             alt="FIS Global Logo" style="height:50px;">
    </div>
    <div>
        <h3 style="margin: 0; color: #4CAF50; font-size: 18px;">
            Forecast Viewer Integrity Saas
        </h3>
    </div>
</div>
<div style="height: 80px;"></div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# -------------------------
# Main Streamlit Application UI
# -------------------------
st.title("Forecast Viewer Integrity Saas")

# Instantiate the data retriever using the loaded CSV data.
data_retriever = ForecastDataRetriever(data)

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
        # Display the forecast data in transposed format.
        st.dataframe(forecast_df.T)
        
        st.subheader("Forecast Plot")
        # Aggregate the forecasted amounts per date.
        plot_data = forecast_df.groupby("ValueDate")["ForecastedClosingBalance"].sum().reset_index()
        plot_data = plot_data.sort_values("ValueDate")
        plot_data = plot_data.set_index("ValueDate")
        st.line_chart(plot_data)
