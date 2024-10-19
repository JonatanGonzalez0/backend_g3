import pickle
from prophet import Prophet
import pandas as pd
from sqlalchemy import create_engine

# Database credentials and connection
host = "arqui2-grupo2.craowweawy84.us-east-1.rds.amazonaws.com"
user = "admin"
password = "HlflryugsQaBW3ppUa55"
database = "Sensores"

db_url = f"mysql+pymysql://{user}:{password}@{host}/{database}"
engine = create_engine(db_url)

def fetch_data():
    # Fetch data from MySQL database
    query_temp = "SELECT fecha_hora, valor AS temperatura FROM Temperatura"
    query_humedad = "SELECT fecha_hora, valor AS humedad FROM Humedad"
    query_aire = "SELECT fecha_hora, valor AS aire FROM Aire"
    query_luz = "SELECT fecha_hora, valor AS luz FROM Luz"

    df_temp = pd.read_sql(query_temp, engine)
    df_humedad = pd.read_sql(query_humedad, engine)
    df_aire = pd.read_sql(query_aire, engine)
    df_luz = pd.read_sql(query_luz, engine)

    return df_temp, df_humedad, df_aire, df_luz

def prepare_data(df, variable_name):
    # Prepare the data for Prophet model
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    df = df.rename(columns={'fecha_hora': 'ds', variable_name: 'y'})
    df = df.set_index('ds').resample('D').mean()
    df = df.interpolate(method='linear').reset_index()
    return df[['ds', 'y']]

# Fetch and prepare the data
df_temp, df_humedad, df_aire, df_luz = fetch_data()
df_temp_prepared = prepare_data(df_temp, 'temperatura')
df_humedad_prepared = prepare_data(df_humedad, 'humedad')
df_aire_prepared = prepare_data(df_aire, 'aire')
df_luz_prepared = prepare_data(df_luz, 'luz')

# Train the models
model_temp = Prophet()
model_temp.fit(df_temp_prepared)

model_humedad = Prophet()
model_humedad.fit(df_humedad_prepared)

model_aire = Prophet()
model_aire.fit(df_aire_prepared)

model_luz = Prophet()
model_luz.fit(df_luz_prepared)

# Save the trained models as .pkl files
with open('model_temp.pkl', 'wb') as f:
    pickle.dump(model_temp, f)

with open('model_humedad.pkl', 'wb') as f:
    pickle.dump(model_humedad, f)

with open('model_aire.pkl', 'wb') as f:
    pickle.dump(model_aire, f)

with open('model_luz.pkl', 'wb') as f:
    pickle.dump(model_luz, f)

print("Models trained and saved as .pkl files.")
