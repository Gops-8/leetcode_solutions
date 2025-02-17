import configparser
import pandas as pd
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import databricks.sql as dbsql  # pip install databricks-sql-connector
import uvicorn

# -------------------------
# Pydantic Model for Forecast Record
# -------------------------
class ForecastRecord(BaseModel):
    TenentID: str
    ValueDate: date
    CashPoolDescription: str
    WorkSheetCatagoryDescription: str
    ForecastedClosingBalance: float

# -------------------------
# Load configuration from config.ini
# -------------------------
config = configparser.ConfigParser()
config.read("config.ini")

# -------------------------
# Initialize FastAPI
# -------------------------
app = FastAPI(
    title="Forecast Viewer Integrity Saas API",
    version="1.0",
    description="API to return forecast data loaded from Databricks using a config file."
)

# -------------------------
# Helper Function: Get Data from Databricks
# -------------------------
def get_databricks_data() -> pd.DataFrame:
    """
    Connect to Databricks using details from config.ini, execute a query to retrieve all records
    from the specified table, and return the result as a Pandas DataFrame.
    """
    try:
        # Establish connection using details from config.ini
        conn = dbsql.connect(
            server_hostname=config["databricks"]["server_hostname"],
            http_path=config["databricks"]["http_path"],
            access_token=config["databricks"]["access_token"]
        )
        table_name = config["databricks"]["table_name"]
        query = f"SELECT * FROM {table_name}"
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)

        # Convert ValueDate column to date objects if available
        if "ValueDate" in df.columns:
            df["ValueDate"] = pd.to_datetime(df["ValueDate"]).dt.date
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data from Databricks: {e}")

# -------------------------
# API Endpoint to Get Forecast Data
# -------------------------
@app.get("/forecast", tags=["Forecast"], summary="Get Forecast Data", 
         response_model=List[ForecastRecord],
         response_description="Returns the forecast table data")
def get_forecast():
    """
    Retrieve the forecast data from Databricks and return it as a list of forecast records.
    """
    df = get_databricks_data()
    # Convert DataFrame to list of dictionaries
    records = df.to_dict(orient="records")
    # Pydantic will validate each record according to ForecastRecord
    return JSONResponse(content=records)

# -------------------------
# Run the FastAPI Application
# -------------------------
if __name__ == "__main__":
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)
