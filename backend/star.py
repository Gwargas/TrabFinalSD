from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import logging

# --- Logger Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- External API URLs ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API_URL = "https://marine-api.open-meteo.com/v1/marine"
STANDARD_API_URL = "https://api.open-meteo.com/v1/forecast"

# --- Pydantic Models ---
class WeatherRequest(BaseModel):
    cidade: str

class WeatherResponse(BaseModel):
    local: str
    temperatura_c: float
    umidade: float
    vento_kph: float
    prob_chuva: float
    tamanho_onda_m: float

# --- FastAPI App ---
app = FastAPI()

@app.get("/")
def root():
    return {"message": "API de Previsão do Tempo está funcionando!"}

@app.post("/previsao", response_model=WeatherResponse)
def obter_previsao(request_data: WeatherRequest):
    try:
        # 1. Geocoding API
        geocoding_params = {'name': request_data.cidade, 'count': 1}
        geo_response = requests.get(GEOCODING_API_URL, params=geocoding_params, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get('results'):
            raise HTTPException(status_code=404, detail=f"Cidade não encontrada: {request_data.cidade}")

        location = geo_data['results'][0]
        latitude = location['latitude']
        longitude = location['longitude']
        local_nome = f"{location['name']}, {location.get('admin1', '')}, {location['country']}"

        # 2. Determine API based on location
        if abs(latitude) > 60 or abs(longitude) > 60:  # Example rule for coastal
            forecast_url = FORECAST_API_URL
            forecast_params = {
                'latitude': latitude,
                'longitude': longitude,
                'hourly': 'wave_height,wind_speed,air_temperature',
                'daily': 'wave_height_max',
                'timezone': 'auto'
            }
        else:
            forecast_url = STANDARD_API_URL
            forecast_params = {
                'latitude': latitude,
                'longitude': longitude,
                'hourly': 'temperature_2m,relative_humidity_2m,rain,wind_speed_10m',
                'timezone': 'auto'
            }

        # 3. Fetch weather data
        forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
        forecast_response.raise_for_status()
        weather_data = forecast_response.json()

        # 4. Process response
        current_weather = weather_data.get('current', {})
        daily_weather = weather_data.get('daily', {})
        tamanho_onda_m = daily_weather.get('wave_height_max', [0.0])[0] if 'wave_height_max' in daily_weather else 0.0
        prob_chuva = 100.0 if current_weather.get('rain', 0.0) > 0 else 0.0

        return WeatherResponse(
            local=local_nome,
            temperatura_c=current_weather.get('temperature_2m', 0.0),
            umidade=current_weather.get('relative_humidity_2m', 0.0),
            vento_kph=current_weather.get('wind_speed_10m', 0.0),
            prob_chuva=prob_chuva,
            tamanho_onda_m=tamanho_onda_m
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de comunicação com a API externa: {e}")
        raise HTTPException(status_code=503, detail="Erro ao comunicar com o serviço externo.")