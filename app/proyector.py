import logging
from sqlalchemy import create_engine
import pandas as pd
from prophet import Prophet
from datetime import datetime

class ClimateForecaster:
    def __init__(self, host, user, password, database):
        # Usar SQLAlchemy para crear una cadena de conexión
        self.db_url = f"mysql+pymysql://{user}:{password}@{host}/{database}"
        self.engine = create_engine(self.db_url)
        self.dataframes = {}
        self.models = {}

    def fetch_data(self):
        # Consultar los datos de las tablas
        query_temp = "SELECT fecha_hora, valor AS temperatura FROM Temperatura"
        query_humedad = "SELECT fecha_hora, valor AS humedad FROM Humedad"
        query_aire = "SELECT fecha_hora, valor AS aire FROM Aire"
        query_luz = "SELECT fecha_hora, valor AS luz FROM Luz"

        # Cargar los datos en dataframes usando SQLAlchemy
        df_temp = pd.read_sql(query_temp, self.engine)
        df_humedad = pd.read_sql(query_humedad, self.engine)
        df_aire = pd.read_sql(query_aire, self.engine)
        df_luz = pd.read_sql(query_luz, self.engine)

        return df_temp, df_humedad, df_aire, df_luz

    def prepare_data(self, df, variable_name):
        # Verificar que la columna 'fecha_hora' existe en el DataFrame
        if 'fecha_hora' not in df.columns:
            raise KeyError("La columna 'fecha_hora' no se encuentra en el DataFrame")

        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])  # Convertir a datetime
        df = df.rename(columns={'fecha_hora': 'ds', variable_name: 'y'})  # Renombrar columnas
        df = df.set_index('ds')  # Establecer 'ds' como índice
        df = df.resample('D').mean()  # Resamplear a diario
        df = df.interpolate(method='linear')  # Rellenar datos faltantes con interpolación
        df = df.reset_index()  # Restablecer el índice
        return df[['ds', 'y']]  # Devolver sólo las columnas necesarias

    def fit_models(self, df_temp, df_humedad, df_aire, df_luz):
        model_temp = Prophet()
        model_temp.fit(df_temp)
        self.models['temperatura'] = model_temp

        model_humedad = Prophet()
        model_humedad.fit(df_humedad)
        self.models['humedad'] = model_humedad

        model_aire = Prophet()
        model_aire.fit(df_aire)
        self.models['aire'] = model_aire

        model_luz = Prophet()
        model_luz.fit(df_luz)
        self.models['luz'] = model_luz

    def forecast_all(self, ultimo_dia, dias_a_predecir=8):
        fecha_actual = pd.to_datetime(datetime.now().date())
        dias_desde_ultimo_dia = (fecha_actual - ultimo_dia).days

        future_temp = self.models['temperatura'].make_future_dataframe(periods=dias_desde_ultimo_dia + dias_a_predecir, freq='D')
        self.dataframes['forecast_temp'] = self.models['temperatura'].predict(future_temp)

        future_humedad = self.models['humedad'].make_future_dataframe(periods=dias_desde_ultimo_dia + dias_a_predecir, freq='D')
        self.dataframes['forecast_humedad'] = self.models['humedad'].predict(future_humedad)

        future_aire = self.models['aire'].make_future_dataframe(periods=dias_desde_ultimo_dia + dias_a_predecir, freq='D')
        self.dataframes['forecast_aire'] = self.models['aire'].predict(future_aire)

        future_luz = self.models['luz'].make_future_dataframe(periods=dias_desde_ultimo_dia + dias_a_predecir, freq='D')
        self.dataframes['forecast_luz'] = self.models['luz'].predict(future_luz)
    
    def obtener_proyeccion(self, fecha_input_usuario):
        """
        Método para obtener la proyección del clima para una fecha específica.
        """
        fecha_input_usuario = pd.to_datetime(fecha_input_usuario)

        # Establecer un rango de tolerancia de 12 horas para la comparación de fechas
        rango_tolerancia = pd.Timedelta(hours=12)

        # Buscar la predicción para la fecha seleccionada con un rango de tolerancia
        prediccion_temp = self.dataframes['forecast_temp'][self.dataframes['forecast_temp']['ds'].between(
            fecha_input_usuario - rango_tolerancia, fecha_input_usuario + rango_tolerancia)]
        prediccion_humedad = self.dataframes['forecast_humedad'][self.dataframes['forecast_humedad']['ds'].between(
            fecha_input_usuario - rango_tolerancia, fecha_input_usuario + rango_tolerancia)]
        prediccion_aire = self.dataframes['forecast_aire'][self.dataframes['forecast_aire']['ds'].between(
            fecha_input_usuario - rango_tolerancia, fecha_input_usuario + rango_tolerancia)]
        prediccion_luz = self.dataframes['forecast_luz'][self.dataframes['forecast_luz']['ds'].between(
            fecha_input_usuario - rango_tolerancia, fecha_input_usuario + rango_tolerancia)]

        # Verificar que se haya encontrado una predicción para cada variable
        if not prediccion_temp.empty and not prediccion_humedad.empty and not prediccion_aire.empty and not prediccion_luz.empty:
            # Obtener los valores proyectados
            temperatura_proyectada = prediccion_temp['yhat'].values[0].round(2)
            humedad_proyectada = min(prediccion_humedad['yhat'].values[0].round(2), 100.00)
            aire_proyectado = min(prediccion_aire['yhat'].values[0].round(2), 100.00)
            luz_proyectada = min(prediccion_luz['yhat'].values[0].round(2), 100.00)


            #debvolver un json con los valores proyectados
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

    def interpretar_clima(self, temperatura, humedad, aire, luz):
        """
        Método para interpretar el estado del clima basado en las proyecciones.
        """
        logging.debug(f"Proyección - Temperatura: {temperatura}, Humedad: {humedad}, Aire: {aire}, Luz: {luz}")
        if temperatura > 28 and luz > 70:  # Luz es un porcentaje
            return "Caluroso y Soleado"
        elif temperatura < 10:
            return "Frío"
        elif humedad > 80:
            return "Húmedo"
        elif luz < 30:
            return "Nublado"
        elif luz >= 30 and luz <= 60:
            return "Parcialmente Nublado"
        elif luz > 60 and humedad < 40:
            return "Seco"
        elif aire > 75:  # Aire es un porcentaje
            return "Ventoso"
        else:
            return "Clima no determinado"