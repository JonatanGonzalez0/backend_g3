from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.proyector import ClimateForecaster

from datetime import datetime
import pandas as pd

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar el predictor de clima
# forecaster = ClimateForecaster(
#     host="localhost",
#     user="root",
#     password="Ne59481739#",
#     database="sensores"
# )

forecaster = ClimateForecaster(
    host="arqui2-grupo2.craowweawy84.us-east-1.rds.amazonaws.com",
    user="admin",
    password="HlflryugsQaBW3ppUa55",
    database="Sensores"
)

# Definir el modelo Pydantic para validar la fecha
class FechaInput(BaseModel):
    fecha: str  # Recibirá la fecha en formato 'YYYY-MM-DD'

@app.on_event("startup")
async def startup_event():
    """
    Inicializar el modelo al iniciar el servidor FastAPI.
    """
    df_temp, df_humedad, df_aire, df_luz = forecaster.fetch_data()
    
    # Validar que las columnas existen antes de continuar
    if 'fecha_hora' not in df_temp.columns:
        raise KeyError("La columna 'fecha_hora' no está en el DataFrame df_temp.")
    if 'fecha_hora' not in df_humedad.columns:
        raise KeyError("La columna 'fecha_hora' no está en el DataFrame df_humedad.")
    if 'fecha_hora' not in df_aire.columns:
        raise KeyError("La columna 'fecha_hora' no está en el DataFrame df_aire.")
    if 'fecha_hora' not in df_luz.columns:
        raise KeyError("La columna 'fecha_hora' no está en el DataFrame df_luz.")

    # Preparar los datos y ajustar los modelos
    forecaster.dataframes['temperatura'] = forecaster.prepare_data(df_temp, 'temperatura')
    forecaster.dataframes['humedad'] = forecaster.prepare_data(df_humedad, 'humedad')
    forecaster.dataframes['aire'] = forecaster.prepare_data(df_aire, 'aire')
    forecaster.dataframes['luz'] = forecaster.prepare_data(df_luz, 'luz')
    
    # Ajustar los modelos
    forecaster.fit_models(
        forecaster.dataframes['temperatura'],
        forecaster.dataframes['humedad'],
        forecaster.dataframes['aire'],
        forecaster.dataframes['luz']
    )
    
    # Obtener la última fecha en los datos y realizar la proyección
    ultimo_dia = max(
        forecaster.dataframes['temperatura']['ds'].max(), 
        forecaster.dataframes['humedad']['ds'].max(), 
        forecaster.dataframes['aire']['ds'].max(), 
        forecaster.dataframes['luz']['ds'].max()
    )
    forecaster.forecast_all(ultimo_dia)


@app.post("/get_one_day_projection")
async def get_proyeccion(fecha_input: FechaInput):
    """
    Ruta para obtener la proyección del clima dado un día en formato YYYY-MM-DD.
    """
    try:
        # Recargar los datos desde la base de datos
        df_temp, df_humedad, df_aire, df_luz = forecaster.fetch_data()
        
        # Volver a preparar los datos y ajustar los modelos si es necesario
        forecaster.dataframes['temperatura'] = forecaster.prepare_data(df_temp, 'temperatura')
        forecaster.dataframes['humedad'] = forecaster.prepare_data(df_humedad, 'humedad')
        forecaster.dataframes['aire'] = forecaster.prepare_data(df_aire, 'aire')
        forecaster.dataframes['luz'] = forecaster.prepare_data(df_luz, 'luz')

        # Validar la fecha de entrada
        fecha_input_usuario = pd.to_datetime(fecha_input.fecha).normalize()
        fecha_actual = pd.to_datetime(datetime.now().date())
        diferencia_dias = (fecha_input_usuario - fecha_actual).days

        if diferencia_dias < 0 or diferencia_dias > 8:
            raise HTTPException(status_code=400, detail="La fecha seleccionada está fuera del rango de proyección.")
        
        # Obtener la proyección
        return forecaster.obtener_proyeccion(fecha_input.fecha)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la proyección: {str(e)}")

@app.get("/get_all_projections_today")
async def get_all_projections_today():
    '''
    Ruta para obtener la proyección apartir de la fecha actual 8 días
    '''
    try:
        # Recargar los datos desde la base de datos
        df_temp, df_humedad, df_aire, df_luz = forecaster.fetch_data()
        
        # Volver a preparar los datos y ajustar los modelos si es necesario
        forecaster.dataframes['temperatura'] = forecaster.prepare_data(df_temp, 'temperatura')
        forecaster.dataframes['humedad'] = forecaster.prepare_data(df_humedad, 'humedad')
        forecaster.dataframes['aire'] = forecaster.prepare_data(df_aire, 'aire')
        forecaster.dataframes['luz'] = forecaster.prepare_data(df_luz, 'luz')

        # Obtener la proyección para la fecha actual y los próximos 8 días
        today = datetime.now().date()

        #crear un diccionario para guardar las proyecciones de cada día
        proyecciones = {}
        try:
            for i in range(8):
                fecha = today + pd.Timedelta(days=i)
                proyecciones[fecha] = forecaster.obtener_proyeccion(str(fecha))
            return proyecciones
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en la proyección: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la proyección: {str(e)}")