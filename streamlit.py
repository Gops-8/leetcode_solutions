import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

# -------------------------
# Page Configuration & Custom CSS
# -------------------------
st.set_page_config(
    page_title="FOrecast Viewer for Integrity SAAS",
    page_icon=":bar_chart:",
    layout="wide",  # to allow side-by-side inputs
    initial_sidebar_state="collapsed"
)

# Hide Streamlit’s default menu, footer, sidebar, and the “Deploy other apps” button.
hide_elements_style = """
    <style>
    /* Hide hamburger menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Hide the sidebar completely */
    [data-testid="stSidebar"] {display: none;}

    /* Hide the deploy button (if present) */
    button[title="Deploy other apps"] {display: none;}
    </style>
    """
st.markdown(hide_elements_style, unsafe_allow_html=True)

# Custom CSS to give a green accent to buttons
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
# App Title
# -------------------------
st.title("FOrecast Viewer for Integrity SAAS")

# -------------------------
# Top Row of Input Fields (Client & Pool Groups, Future Timespan)
# -------------------------
col1, col2, col3 = st.columns(3)

with col1:
    client = st.selectbox("Select Client Name", options=["CVS", "Aegon"])

with col2:
    # Simulate reading pool groups based on the client name.
    if client == "CVS":
        available_pool_groups = ["CVS Group A", "CVS Group B", "CVS Group C"]
    else:  # Aegon
        available_pool_groups = ["Aegon Group X", "Aegon Group Y"]
    pool_groups = st.multiselect("Select Pool Groups", options=available_pool_groups)

with col3:
    future_days = st.slider("Future Timespan (Days)", min_value=5, max_value=15, value=5)

# -------------------------
# Second Row of Input Fields (Forecast Fields & Historical Date Range)
# -------------------------
col4, col5, col6 = st.columns(3)

with col4:
    # Let the user select which columns (fields) to forecast.
    # Here we assume column numbers are represented as strings.
    forecast_fields = st.multiselect(
        "Fields to Forecast (Column Number)",
        options=["Column 1", "Column 2", "Column 3", "Column 4", "Column 5"]
    )

with col5:
    # Historical date range input (a tuple of start and end dates)
    historical_dates = st.date_input(
        "Select Historical Date Range",
        value=(date.today() - timedelta(days=365), date.today())
    )

with col6:
    # You can use this column for additional inputs or leave it empty.
    st.empty()

# -------------------------
# Forecast Button and Output Table
# -------------------------
if st.button("Show Forecast"):
    # In a production app, you would connect to your Databricks catalog and query the raw output.
    # For demonstration purposes, we simulate a forecast DataFrame.

    def get_forecast_data(client, pool_groups, future_days, forecast_fields, historical_dates):
        # Generate future dates starting from tomorrow.
        start_date = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
        future_dates = pd.date_range(start=start_date, periods=future_days)

        # Build a list of forecast records. In your case, replace this logic with a query to your catalog.
        records = []
        # If no pool groups or forecast fields are selected, provide defaults.
        groups = pool_groups if pool_groups else ["N/A"]
        fields = forecast_fields if forecast_fields else ["Column 1"]

        for pool in groups:
            for field in fields:
                for forecast_date in future_dates:
                    records.append({
                        "Date": forecast_date.date(),
                        "Client": client,
                        "Pool Group": pool,
                        "Field": field,
                        "Forecast Value": round(np.random.rand() * 100, 2)
                    })
        return pd.DataFrame(records)

    # Fetch the forecast data
    forecast_df = get_forecast_data(client, pool_groups, future_days, forecast_fields, historical_dates)

    st.subheader("Forecast Results")
    st.dataframe(forecast_df)
