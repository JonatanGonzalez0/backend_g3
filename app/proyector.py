from datetime import datetime
import logging
import pickle
import pandas as pd
from sqlalchemy import create_engine

class ClimateForecaster:
    def __init__(self, host, user, password, database, model_temp_path, model_humedad_path, model_aire_path, model_luz_path):
        # Initialize models and dataframes dictionaries
        self.models = {}
        self.dataframes = {}

        # Create a connection to the MySQL database
        self.db_url = f"mysql+pymysql://{user}:{password}@{host}/{database}"
        self.engine = create_engine(self.db_url)

        # Load pre-trained models from pickle files
        with open(model_temp_path, 'rb') as f:
            self.models['temperatura'] = pickle.load(f)

        with open(model_humedad_path, 'rb') as f:
            self.models['humedad'] = pickle.load(f)

        with open(model_aire_path, 'rb') as f:
            self.models['aire'] = pickle.load(f)

        with open(model_luz_path, 'rb') as f:
            self.models['luz'] = pickle.load(f)

    def fetch_data(self):
        # Fetch data from the MySQL database
        query_temp = "SELECT fecha_hora, valor AS temperatura FROM Temperatura"
        query_humedad = "SELECT fecha_hora, valor AS humedad FROM Humedad"
        query_aire = "SELECT fecha_hora, valor AS aire FROM Aire"
        query_luz = "SELECT fecha_hora, valor AS luz FROM Luz"

        df_temp = pd.read_sql(query_temp, self.engine)
        df_humedad = pd.read_sql(query_humedad, self.engine)
        df_aire = pd.read_sql(query_aire, self.engine)
        df_luz = pd.read_sql(query_luz, self.engine)

        return df_temp, df_humedad, df_aire, df_luz

    def prepare_data(self, df, variable_name):
        # Prepare the data for forecasting
        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
        df = df.rename(columns={'fecha_hora': 'ds', variable_name: 'y'})
        df = df.set_index('ds').resample('D').mean()
        df = df.interpolate(method='linear').reset_index()
        return df[['ds', 'y']]

    def forecast_all(self, ultimo_dia, dias_a_predecir=8):
        # Make forecasts for the next `dias_a_predecir` days for all models
        fecha_actual = pd.to_datetime(datetime.now().date())
        dias_desde_ultimo_dia = (fecha_actual - ultimo_dia).days

        future_temp = self.models['temperatura'].make_future_dataframe(
            periods=dias_desde_ultimo_dia + dias_a_predecir, freq='D')
        self.dataframes['forecast_temp'] = self.models['temperatura'].predict(future_temp)

        future_humedad = self.models['humedad'].make_future_dataframe(
            periods=dias_desde_ultimo_dia + dias_a_predecir, freq='D')
        self.dataframes['forecast_humedad'] = self.models['humedad'].predict(future_humedad)

        future_aire = self.models['aire'].make_future_dataframe(
            periods=dias_desde_ultimo_dia + dias_a_predecir, freq='D')
        self.dataframes['forecast_aire'] = self.models['aire'].predict(future_aire)

        future_luz = self.models['luz'].make_future_dataframe(
            periods=dias_desde_ultimo_dia + dias_a_predecir, freq='D')
        self.dataframes['forecast_luz'] = self.models['luz'].predict(future_luz)

    def obtener_proyeccion(self, fecha_input_usuario):
        # Get projections for a specific date
        fecha_input_usuario = pd.to_datetime(fecha_input_usuario)
        rango_tolerancia = pd.Timedelta(hours=12)

        prediccion_temp = self.dataframes['forecast_temp'][
            self.dataframes['forecast_temp']['ds'].between(
                fecha_input_usuario - rango_tolerancia, fecha_input_usuario + rango_tolerancia)]
        prediccion_humedad = self.dataframes['forecast_humedad'][
            self.dataframes['forecast_humedad']['ds'].between(
                fecha_input_usuario - rango_tolerancia, fecha_input_usuario + rango_tolerancia)]
        prediccion_aire = self.dataframes['forecast_aire'][
            self.dataframes['forecast_aire']['ds'].between(
                fecha_input_usuario - rango_tolerancia, fecha_input_usuario + rango_tolerancia)]
        prediccion_luz = self.dataframes['forecast_luz'][
            self.dataframes['forecast_luz']['ds'].between(
                fecha_input_usuario - rango_tolerancia, fecha_input_usuario + rango_tolerancia)]

        if not prediccion_temp.empty and not prediccion_humedad.empty and not prediccion_aire.empty and not prediccion_luz.empty:
            temperatura_proyectada = prediccion_temp['yhat'].values[0].round(2)
            humedad_proyectada = min(prediccion_humedad['yhat'].values[0].round(2), 100.00)
            aire_proyectado = min(prediccion_aire['yhat'].values[0].round(2), 100.00)
            luz_proyectada = min(prediccion_luz['yhat'].values[0].round(2), 100.00)

            return {
                "temperatura": temperatura_proyectada,
                "humedad": humedad_proyectada,
                "aire": aire_proyectado,
                "luz": luz_proyectada
            }
        else:
            return {
                "temperatura": 0,
                "humedad": 0,
                "aire": 0,
                "luz": 0
            }
