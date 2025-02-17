openapi: "3.0.2"
info:
  title: "Forecast Viewer Integrity Saas API"
  version: "1.0"
  description: "API to return forecast data loaded from Databricks using a config file."
paths:
  /forecast:
    get:
      summary: "Get Forecast Data"
      description: "Returns the entire forecast table as a JSON array."
      tags:
        - Forecast
      responses:
        "200":
          description: "Forecast data retrieved successfully."
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    TenentID:
                      type: string
                      example: "CVS"
                    ValueDate:
                      type: string
                      format: date
                      example: "2023-01-01"
                    CashPoolDescription:
                      type: string
                      example: "CVS Group A"
                    WorkSheetCatagoryDescription:
                      type: string
                      example: "Category 1"
                    ForecastedClosingBalance:
                      type: number
                      format: float
                      example: 2000.50
servers:
  - url: "http://localhost:8000"
