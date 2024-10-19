from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.proyector import ClimateForecaster
from datetime import datetime
import pandas as pd

app = FastAPI()

# CORS settings
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the forecaster with the pre-trained model paths
forecaster = ClimateForecaster(
    host="arqui2-grupo2.craowweawy84.us-east-1.rds.amazonaws.com",
    user="admin",
    password="HlflryugsQaBW3ppUa55",
    database="Sensores",
    model_temp_path="app/model_temp.pkl",  # Adjust the paths based on your structure
    model_humedad_path="app/model_humedad.pkl",
    model_aire_path="app/model_aire.pkl",
    model_luz_path="app/model_luz.pkl"
)

# Pydantic model for date input validation
class FechaInput(BaseModel):
    fecha: str  # Date in 'YYYY-MM-DD' format

# Event triggered on app startup to fetch data and prepare models
@app.on_event("startup")
async def startup_event():
    """
    Fetch and prepare data when the FastAPI app starts.
    """
    df_temp, df_humedad, df_aire, df_luz = forecaster.fetch_data()
    forecaster.dataframes['temperatura'] = forecaster.prepare_data(df_temp, 'temperatura')
    forecaster.dataframes['humedad'] = forecaster.prepare_data(df_humedad, 'humedad')
    forecaster.dataframes['aire'] = forecaster.prepare_data(df_aire, 'aire')
    forecaster.dataframes['luz'] = forecaster.prepare_data(df_luz, 'luz')

    # Forecast for the next 8 days starting from the last date in the data
    ultimo_dia = max(
        forecaster.dataframes['temperatura']['ds'].max(),
        forecaster.dataframes['humedad']['ds'].max(),
        forecaster.dataframes['aire']['ds'].max(),
        forecaster.dataframes['luz']['ds'].max()
    )
    forecaster.forecast_all(ultimo_dia)

@app.get("/")
async def root():
    return {"message": "Welcome to the Climate Forecaster API!"}

# Endpoint to get the projection for one specific day
@app.post("/get_one_day_projection")
async def get_one_day_projection(fecha_input: FechaInput):
    """
    Route to get weather projection for a specific date (YYYY-MM-DD).
    """
    try:
        df_temp, df_humedad, df_aire, df_luz = forecaster.fetch_data()
        forecaster.dataframes['temperatura'] = forecaster.prepare_data(df_temp, 'temperatura')
        forecaster.dataframes['humedad'] = forecaster.prepare_data(df_humedad, 'humedad')
        forecaster.dataframes['aire'] = forecaster.prepare_data(df_aire, 'aire')
        forecaster.dataframes['luz'] = forecaster.prepare_data(df_luz, 'luz')

        fecha_input_usuario = pd.to_datetime(fecha_input.fecha).normalize()
        fecha_actual = pd.to_datetime(datetime.now().date())
        diferencia_dias = (fecha_input_usuario - fecha_actual).days

        if diferencia_dias < 0 or diferencia_dias > 8:
            raise HTTPException(status_code=400, detail="The selected date is outside the forecast range.")

        return forecaster.obtener_proyeccion(fecha_input.fecha)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating projection: {str(e)}")

# New endpoint to get projections for today and the next 8 days
@app.get("/get_all_projections_today")
async def get_all_projections_today():
    '''
    Route to get weather projections from today for the next 8 days
    '''
    try:
        # Debugging step 1: Start of data fetching
        print("Fetching data from the database...")
        
        # Fetch and prepare the latest data from the database
        df_temp, df_humedad, df_aire, df_luz = forecaster.fetch_data()
        
        print("Data fetched successfully.")
        
        # Debugging step 2: Preparing the data
        print("Preparing data for prediction...")
        forecaster.dataframes['temperatura'] = forecaster.prepare_data(df_temp, 'temperatura')
        forecaster.dataframes['humedad'] = forecaster.prepare_data(df_humedad, 'humedad')
        forecaster.dataframes['aire'] = forecaster.prepare_data(df_aire, 'aire')
        forecaster.dataframes['luz'] = forecaster.prepare_data(df_luz, 'luz')

        # Debugging step 3: Getting the projections
        today = datetime.now().date()
        proyecciones = {}
        for i in range(8):
            fecha = today + pd.Timedelta(days=i)
            print(f"Generating projection for: {fecha}")
            proyecciones[fecha] = forecaster.obtener_proyeccion(str(fecha))
        print("All projections generated successfully.")
        return proyecciones

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating projections: {str(e)}")
