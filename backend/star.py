# star.py - VERSÃO CORRIGIDA COM SENSACAO TERMICA DIARIA

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- URLs ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
STANDARD_API_URL = "https://api.open-meteo.com/v1/forecast"

# --- Modelos Pydantic ---
class CityInfo(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    country: str
    admin1: Optional[str] = None

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float
    is_coastal: bool
    local: str
    forecast_days: Optional[int] = 1

class DailyForecast(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    uv_index_max: float
    precipitation_probability_max: float
    wave_height_max: Optional[float] = None
    sensacao_termica: Optional[float] = None # Campo para a sensação térmica da primeira hora

class WeatherResponse(BaseModel):
    local: str
    forecast: List[DailyForecast]

# --- Aplicação FastAPI ---
app = FastAPI(title="API de Previsão do Tempo")

@app.get("/search-cities", response_model=List[CityInfo])
def search_cities(name: str):
    params = {'name': name, 'count': 10, 'language': 'pt', 'format': 'json'}
    try:
        response = requests.get(GEOCODING_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [CityInfo(**city) for city in data.get('results', [])]
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na API de Geocodificação: {e}")
        raise HTTPException(status_code=503, detail="Erro ao comunicar com o serviço de geocodificação.")

@app.post("/previsao", response_model=WeatherResponse)
def obter_previsao(request_data: WeatherRequest):
    forecast_days = max(1, min(request_data.forecast_days, 16))
    daily_params = "temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_probability_max"
    
    standard_api_params = {
        'latitude': request_data.latitude,
        'longitude': request_data.longitude,
        'daily': daily_params,
        'hourly': 'apparent_temperature', # Pedimos a sensação térmica horária
        'timezone': 'auto',
        'forecast_days': forecast_days
    }
    
    try:
        # Obter dados da API padrão
        standard_response = requests.get(STANDARD_API_URL, params=standard_api_params, timeout=10)
        standard_response.raise_for_status()
        json_response = standard_response.json()
        standard_data = json_response.get('daily', {})
        hourly_data = json_response.get('hourly', {})

        # Obter dados da API marítima se for costeira
        marine_data = {}
        if request_data.is_coastal:
            marine_api_params = {
                'latitude': request_data.latitude,
                'longitude': request_data.longitude,
                'daily': 'wave_height_max',
                'timezone': 'auto',
                'forecast_days': forecast_days
            }
            marine_response = requests.get(MARINE_API_URL, params=marine_api_params, timeout=10)
            marine_response.raise_for_status()
            marine_data = marine_response.json().get('daily', {})

        # Construir a lista de previsões diárias
        forecast_list = []
        num_days = len(standard_data.get('time', []))
        apparent_temp_list = hourly_data.get('apparent_temperature', [])

        for i in range(num_days):
            # O índice para a primeira hora do dia 'i' é i * 24
            hourly_index = i * 24
            
            # Pega a sensação térmica para a primeira hora do dia
            sensacao = None
            if hourly_index < len(apparent_temp_list):
                sensacao = apparent_temp_list[hourly_index]

            daily_entry = DailyForecast(
                date=standard_data['time'][i],
                temperature_max=standard_data['temperature_2m_max'][i],
                temperature_min=standard_data['temperature_2m_min'][i],
                uv_index_max=standard_data['uv_index_max'][i],
                precipitation_probability_max=standard_data['precipitation_probability_max'][i],
                wave_height_max=marine_data.get('wave_height_max', [None]*num_days)[i],
                sensacao_termica=sensacao
            )
            forecast_list.append(daily_entry)
            
        return WeatherResponse(local=request_data.local, forecast=forecast_list)

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de comunicação com a API externa: {e}")
        raise HTTPException(status_code=503, detail=f"Erro ao comunicar com o serviço externo: {e}")
    except (KeyError, IndexError) as e:
        logger.error(f"Erro ao processar dados da API. Erro: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar os dados recebidos da API.")