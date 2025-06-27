# star.py (ou backend_main.py) - VERSÃO CORRIGIDA

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import logging # <<< MUDANÇA: Importando a biblioteca de logging

# Configurando um logger básico para ver os erros no console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuração das APIs Externas (Open-Meteo) ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"

# --- Modelos de Dados (Pydantic) ---
class WeatherRequest(BaseModel):
    cidade: str

class WeatherResponse(BaseModel):
    local: str
    temperatura_c: float
    umidade: float
    vento_kph: float
    prob_chuva: float
    tamanho_onda_m: float

# --- Instância do Aplicativo FastAPI ---
app = FastAPI(
    title="API de Previsão do Tempo com Open-Meteo",
    description="Um serviço que converte um nome de cidade em previsão do tempo, usando as APIs da Open-Meteo.",
    version="1.0.0"
)

# --- Endpoint da API ---
@app.post("/previsao", response_model=WeatherResponse)
def obter_previsao(request_data: WeatherRequest):
    """
    Este endpoint recebe o nome de uma cidade, busca suas coordenadas geográficas,
    obtém a previsão do tempo e retorna os dados de forma estruturada.
    """
    try:
        # 1. Geocodificação
        geocoding_params = {'name': request_data.cidade, 'count': 1}
        # <<< MUDANÇA: Adicionado um timeout de 10 segundos
        geo_response = requests.get(GEOCODING_API_URL, params=geocoding_params, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get('results'):
            raise HTTPException(status_code=404, detail=f"Cidade não encontrada: {request_data.cidade}")

        location = geo_data['results'][0]
        latitude = location['latitude']
        longitude = location['longitude']
        local_nome = f"{location['name']}, {location.get('admin1', '')}, {location['country']}"

        # 2. Previsão do Tempo
        forecast_params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': 'temperature_2m,relative_humidity_2m,rain,wind_speed_10m',
            'daily': 'wave_height_max',
            'timezone': 'auto'
        }
        # <<< MUDANÇA: Adicionado um timeout de 10 segundos
        forecast_response = requests.get(FORECAST_API_URL, params=forecast_params, timeout=10)
        forecast_response.raise_for_status()
        weather_data = forecast_response.json()

        # 3. Processamento
        current_weather = weather_data['current']
        daily_weather = weather_data['daily']
        prob_chuva_calculada = 100.0 if current_weather.get('rain', 0) > 0 else 0.0

        resposta_formatada = WeatherResponse(
            local=local_nome,
            temperatura_c=current_weather['temperature_2m'],
            umidade=current_weather['relative_humidity_2m'],
            vento_kph=current_weather['wind_speed_10m'],
            prob_chuva=prob_chuva_calculada,
            tamanho_onda_m=daily_weather.get('wave_height_max', [0.0])[0] or 0.0
        )
        return resposta_formatada

    except requests.exceptions.Timeout as e:
        # <<< MUDANÇA: Capturando o erro de timeout especificamente
        logger.error(f"Timeout ao conectar com a API externa: {e}")
        raise HTTPException(status_code=504, detail="O serviço de meteorologia demorou muito para responder.")

    except requests.exceptions.RequestException as e:
        # <<< MUDANÇA: Adicionado logging para ver o erro real no console
        logger.error(f"Erro de comunicação com a API externa: {e}")
        raise HTTPException(status_code=503, detail=f"Erro ao comunicar com o serviço externo: {e}")
        
    except (KeyError, IndexError) as e:
        # <<< MUDANÇA: Adicionado logging para ver o erro real no console
        logger.error(f"Erro ao processar dados da API externa. Resposta recebida: {weather_data}. Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar os dados recebidos da API externa: {e}")