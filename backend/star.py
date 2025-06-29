# star.py - VERSÃO RESTful CORRIGIDA

from fastapi import FastAPI, HTTPException, Request
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
class Link(BaseModel):
    href: str
    rel: str
    type: str

class CityLinks(BaseModel):
    self: Link
    forecast: Link

class CityInfoWithLinks(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    country: str
    admin1: Optional[str] = None
    links: CityLinks

class DailyForecast(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    uv_index_max: float
    precipitation_probability_max: float
    wave_height_max: Optional[float] = None
    sensacao_termica: Optional[float] = None

class WeatherResponse(BaseModel):
    local: str
    forecast: List[DailyForecast]
    links: List[Link]

# --- Aplicação FastAPI ---
app = FastAPI(title="API de Previsão do Tempo RESTful")

@app.get("/cities", response_model=List[CityInfoWithLinks])
def search_cities(name: str, request: Request):
    params = {'name': name, 'count': 10, 'language': 'pt', 'format': 'json'}
    try:
        response = requests.get(GEOCODING_API_URL, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get('results', [])
        
        cities_with_links = []
        for city in results:
            city_id = city['id']
            base_url = str(request.base_url)
            city_links = CityLinks(
                self=Link(href=f"{base_url}cities/{city_id}", rel="self", type="GET"),
                forecast=Link(href=f"{base_url}forecast?latitude={city['latitude']}&longitude={city['longitude']}", rel="forecast", type="GET")
            )
            cities_with_links.append(
                CityInfoWithLinks(**city, links=city_links)
            )
            print(cities_with_links)
        return cities_with_links

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na API de Geocodificação: {e}")
        raise HTTPException(status_code=503, detail="Erro ao comunicar com o serviço de geocodificação.")

# <<< A CORREÇÃO ESTÁ AQUI >>>
# O argumento 'request: Request' foi movido para antes dos argumentos com valores padrão.
@app.get("/forecast", response_model=WeatherResponse)
def get_forecast(latitude: float, longitude: float, request: Request, forecast_days: int = 7, is_coastal: bool = False, local: str = ""):
    forecast_days = max(1, min(forecast_days, 16))
    daily_params = "temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_probability_max"
    
    standard_api_params = {
        'latitude': latitude,
        'longitude': longitude,
        'daily': daily_params,
        'hourly': 'apparent_temperature',
        'timezone': 'auto',
        'forecast_days': forecast_days
    }
    
    try:
        standard_response = requests.get(STANDARD_API_URL, params=standard_api_params, timeout=10)
        standard_response.raise_for_status()
        json_response = standard_response.json()
        standard_data = json_response.get('daily', {})
        hourly_data = json_response.get('hourly', {})

        marine_data = {}
        if is_coastal:
            marine_api_params = {'latitude': latitude, 'longitude': longitude, 'daily': 'wave_height_max', 'timezone': 'auto', 'forecast_days': forecast_days}
            marine_response = requests.get(MARINE_API_URL, params=marine_api_params, timeout=10)
            marine_response.raise_for_status()
            marine_data = marine_response.json().get('daily', {})

        forecast_list = []
        num_days = len(standard_data.get('time', []))
        apparent_temp_list = hourly_data.get('apparent_temperature', [])

        for i in range(num_days):
            hourly_index = i * 24
            sensacao = apparent_temp_list[hourly_index] if hourly_index < len(apparent_temp_list) else None
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
        
        self_link = Link(href=str(request.url), rel="self", type="GET")
        display_local = local if local else f"{latitude}, {longitude}"
        print(self_link)

        return WeatherResponse(local=display_local, forecast=forecast_list, links=[self_link])

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de comunicação com a API externa: {e}")
        raise HTTPException(status_code=503, detail=f"Erro ao comunicar com o serviço externo: {e}")
    except (KeyError, IndexError) as e:
        logger.error(f"Erro ao processar dados da API. Erro: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar os dados recebidos da API.")