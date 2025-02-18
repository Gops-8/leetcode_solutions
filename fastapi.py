import os
import requests
import configparser

class DatabricksClient:
    def __init__(self, config_path='config/config.ini'):
        config = configparser.ConfigParser()
        # Make sure the path is relative to the project root
        config.read(os.path.join(os.path.dirname(__file__), config_path))
        
        try:
            self.token = config.get('databricks', 'token')
            self.host = config.get('databricks', 'host')
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise Exception(f"Configuration error: {e}")
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def fetch_data(self, endpoint: str, payload: dict) -> dict:
        """
        Sends a POST request to the specified Databricks endpoint with the provided payload.
        """
        url = f"{self.host}{endpoint}"
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
## main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databricks_client import DatabricksClient

app = FastAPI()

# Define your request schema (example)
class DataRequest(BaseModel):
    query: str  # Adjust or add additional fields as needed

# Define your response schema (example)
class DataResponse(BaseModel):
    data: dict

# Instantiate the Databricks client
client = DatabricksClient()

@app.post("/endpoint1", response_model=DataResponse)
async def endpoint1(request: DataRequest):
    try:
        # Adjust the Databricks API endpoint as necessary
        result = client.fetch_data("/api/endpoint1", request.dict())
        return DataResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoint2", response_model=DataResponse)
async def endpoint2(request: DataRequest):
    try:
        result = client.fetch_data("/api/endpoint2", request.dict())
        return DataResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoint3", response_model=DataResponse)
async def endpoint3(request: DataRequest):
    try:
        result = client.fetch_data("/api/endpoint3", request.dict())
        return DataResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoint4", response_model=DataResponse)
async def endpoint4(request: DataRequest):
    try:
        result = client.fetch_data("/api/endpoint4", request.dict())
        return DataResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
