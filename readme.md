
# Instalacion de requerimientos
```bash
pip install -r requirements.txt
```

# Ejecucion
```bash
uvicorn api:app
```

# Endpoints

## GET /get_all_projections_today
Obtiene todas las proyecciones de hoy en adelante 8 dias mas

```json
{
    "2024-10-16": {
        "temperatura": 22.91,
        "humedad": 71.33,
        "aire": 95.34,
        "luz": 73.19
    },
    "2024-10-17": {
        "temperatura": 22.54,
        "humedad": 70.47,
        "aire": 100.0,
        "luz": 73.5
    },
    "2024-10-18": {
        "temperatura": 22.17,
        "humedad": 69.6,
        "aire": 100.0,
        "luz": 73.81
    },
    "2024-10-19": {
        "temperatura": 21.81,
        "humedad": 68.74,
        "aire": 100.0,
        "luz": 74.11
    },
    "2024-10-20": {
        "temperatura": 21.44,
        "humedad": 67.88,
        "aire": 100.0,
        "luz": 74.42
    },
    "2024-10-21": {
        "temperatura": 21.08,
        "humedad": 67.02,
        "aire": 100.0,
        "luz": 74.72
    },
    "2024-10-22": {
        "temperatura": 20.71,
        "humedad": 66.16,
        "aire": 100.0,
        "luz": 75.03
    },
    "2024-10-23": {
        "temperatura": 20.35,
        "humedad": 65.3,
        "aire": 100.0,
        "luz": 75.34
    }
}
```

## POST /get_one_day_projection

Obtiene la proyeccion de un dia en especifico se necesita enviar el parametro date en formato YYYY-MM-DD

Envio POST
```json
{
  "fecha": "2024-10-16"
}
```

Resultado
```json
{
    "temperatura": 22.91,
    "humedad": 71.33,
    "aire": 95.34,
    "luz": 73.19
}
```