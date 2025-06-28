# star.py - VERSÃO CORRIGIDA DE ACORDO COM A DOCUMENTAÇÃO

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- URLs das APIs Externas ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
STANDARD_API_URL = "https://api.open-meteo.com/v1/forecast"

# --- Modelos Pydantic ---
class WeatherRequest(BaseModel):
    cidade: str
    is_coastal: bool

class WeatherResponse(BaseModel):
    local: str
    temperatura_c: float
    umidade: float
    vento_kph: float
    prob_chuva: float
    tamanho_onda_m: float
    temperatura_a: float

# --- Aplicação FastAPI ---
app = FastAPI()

@app.post("/previsao", response_model=WeatherResponse)
def obter_previsao(request_data: WeatherRequest):
    try:
        # 1. Geocodificação
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

        # Lógica baseada na flag 'is_coastal'
        if request_data.is_coastal:
            # --- LÓGICA PARA CIDADES COSTEIRAS ---
            logger.info(f"Cidade '{request_data.cidade}' marcada como costeira. Usando a API Marítima.")
            forecast_params = {
                'latitude': latitude,
                'longitude': longitude,
                # A documentação não lista uma variável para chuva/precipitação horária.
                'hourly': 'sea_surface_temperature',
                'daily': 'wave_height_max',
                'timezone': 'auto'
            }
            forecast_response = requests.get(MARINE_API_URL, params=forecast_params, timeout=10)
            forecast_response.raise_for_status()
            weather_data = forecast_response.json()

            forecast_params = {
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,relative_humidity_2m,rain,wind_speed_10m',
                'timezone': 'auto'
            }
            forecast_response_standard = requests.get(STANDARD_API_URL, params=forecast_params, timeout=10)
            forecast_response_standard.raise_for_status()
            weather_data_standard = forecast_response_standard.json()

            # Processa a resposta da API Padrão
            current = weather_data_standard['current']
            temperatura = current['temperature_2m']
            umidade = current['relative_humidity_2m']
            vento = current['wind_speed_10m']
            chuva = current['rain']

            # Processa a resposta da API Marítima
            hourly = weather_data['hourly']
            daily = weather_data['daily']
            temperatura_agua = hourly['sea_surface_temperature'][0]
            umidade = 0.0  # Não disponível na API Marítima
            #vento = 0.0      # Não disponível na API Marítima
            #chuva = 0.0      # Não disponível na API Marítima
            ondas = daily.get('wave_height_max', [0.0])[0] or 0.0

        else:
            # --- LÓGICA PARA CIDADES NÃO COSTEIRAS ---
            logger.info(f"Cidade '{request_data.cidade}' não marcada como costeira. Usando a API Padrão.")
            forecast_params = {
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,relative_humidity_2m,rain,wind_speed_10m',
                'timezone': 'auto'
            }
            forecast_response_standard = requests.get(STANDARD_API_URL, params=forecast_params, timeout=10)
            forecast_response_standard.raise_for_status()
            weather_data_standard = forecast_response_standard.json()

            # Processa a resposta da API Padrão
            current = weather_data_standard['current']
            temperatura = current['temperature_2m']
            umidade = current['relative_humidity_2m']
            vento = current['wind_speed_10m']
            chuva = current['rain']
            ondas = 0.0
            temperatura_agua = 0.0


        # Cálculo da probabilidade de chuva
        prob_chuva = 100.0 if chuva > 0 else 0.0

        return WeatherResponse(
            local=local_nome,
            temperatura_c=temperatura,
            umidade=umidade,
            vento_kph=vento,
            prob_chuva=prob_chuva,
            tamanho_onda_m=ondas,
            temperatura_a=temperatura_agua
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de comunicação com a API externa: {e}")
        raise HTTPException(status_code=503, detail=f"Erro ao comunicar com o serviço externo: {e}")
    except (KeyError, IndexError) as e:
        logger.error(f"Erro ao processar dados da API. Resposta: {weather_data}. Erro: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar os dados recebidos da API.")