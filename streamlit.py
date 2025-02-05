import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date

# -------------------------
# Page Configuration and Custom CSS
# -------------------------
st.set_page_config(
    page_title="FOrecast Viewer for Integrity SAAS",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide default Streamlit elements and the deploy button
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
# Data Retrieval Class
# -------------------------
class ForecastDataRetriever:
    def __init__(self):
        """
        Simulate loading data from a Databricks table.
        The simulated table has the following columns:
          - TenentID
          - ValueDate
          - CashPoolDescription
          - WorkSheetCatagoryDescription
          - ForecastedClosingBalance
        """
        self.data = self._simulate_data()
    
    def _simulate_data(self):
        # Simulate data for two clients: "CVS" and "Aegon"
        clients = {
            "CVS": {
                "cashpools": ["CVS Group A", "CVS Group B", "CVS Group C"],
                "start_date": date.today() - timedelta(days=30)
            },
            "Aegon": {
                "cashpools": ["Aegon Group X", "Aegon Group Y"],
                "start_date": date.today() - timedelta(days=40)
            }
        }
        
        records = []
        # Create 50 days of data for each client and for each cashpool group.
        for client, info in clients.items():
            start_date = info["start_date"]
            cashpools = info["cashpools"]
            for day in range(50):
                current_date = start_date + timedelta(days=day)
                for cp in cashpools:
                    record = {
                        "TenentID": client,
                        "ValueDate": current_date,
                        "CashPoolDescription": cp,
                        "WorkSheetCatagoryDescription": np.random.choice(["Category 1", "Category 2", "Category 3"]),
                        "ForecastedClosingBalance": round(np.random.uniform(1000, 5000), 2)
                    }
                    records.append(record)
        df = pd.DataFrame(records)
        return df

    def get_unique_clients(self):
        """Return unique TenentIDs (client names) from the simulated data."""
        return self.data["TenentID"].unique().tolist()
    
    def get_start_date_and_cashpool_groups(self, client):
        """
        For a given client, return:
          - The earliest (minimum) ValueDate as the start date.
          - The unique CashPoolDescription values as the available cashpool groups.
        """
        client_data = self.data[self.data["TenentID"] == client]
        if client_data.empty:
            return None, []
        start_date = client_data["ValueDate"].min()
        cashpool_groups = client_data["CashPoolDescription"].unique().tolist()
        return start_date, cashpool_groups
    
    def get_forecast_data(self, client, selected_cashpools, no_of_days):
        """
        Given a client, selected cashpool groups, and a number of days:
          1. Find the start date (the minimum ValueDate for that client).
          2. Calculate the end date as: start_date + no_of_days.
          3. Filter the data for rows that match the client, fall within the start and end dates,
             and (if specified) belong to the selected cashpool groups.
        Returns the filtered DataFrame along with the start and end dates.
        """
        start_date, _ = self.get_start_date_and_cashpool_groups(client)
        if start_date is None:
            return pd.DataFrame(), None, None
        
        end_date = start_date + timedelta(days=no_of_days)
        
        # Filter data by client and date range
        df_filtered = self.data[
            (self.data["TenentID"] == client) &
            (self.data["ValueDate"] >= start_date) &
            (self.data["ValueDate"] <= end_date)
        ]
        
        # Further filter by cashpool groups if provided
        if selected_cashpools:
            df_filtered = df_filtered[df_filtered["CashPoolDescription"].isin(selected_cashpools)]
        
        return df_filtered.reset_index(drop=True), start_date, end_date

# -------------------------
# Streamlit UI
# -------------------------
st.title("FOrecast Viewer for Integrity SAAS")

# Instantiate the data retriever
data_retriever = ForecastDataRetriever()

# --- Top Row: Client Selection and Future Timespan ---
col1, col2, col3 = st.columns(3)
with col1:
    unique_clients = data_retriever.get_unique_clients()
    client = st.selectbox("Select Client", options=unique_clients)

with col2:
    # For the selected client, retrieve the start date and cashpool groups.
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
    # Let the user choose one or more cashpool groups.
    # By default, all available groups are selected.
    selected_cashpools = st.multiselect("Select CashPool Groups", options=available_cashpools, default=available_cashpools)
with col5:
    st.empty()  # Reserved for any additional inputs if needed

# --- Forecast Data Retrieval ---
if st.button("Show Forecast"):
    forecast_df, start_date, end_date = data_retriever.get_forecast_data(client, selected_cashpools, no_of_days)
    
    if forecast_df.empty:
        st.warning("No data found for the selected filters.")
    else:
        st.subheader("Forecast Results (Transposed)")
        # Display the DataFrame in transposed format.
        st.dataframe(forecast_df.T)
        
        st.subheader("Forecast Plot")
        # For plotting, aggregate (sum) the ForecastedClosingBalance per ValueDate.
        plot_data = forecast_df.groupby("ValueDate")["ForecastedClosingBalance"].sum().reset_index()
        plot_data = plot_data.sort_values("ValueDate")
        # Set the date as index for the line chart.
        plot_data = plot_data.set_index("ValueDate")
        st.line_chart(plot_data)
