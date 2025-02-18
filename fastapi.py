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
