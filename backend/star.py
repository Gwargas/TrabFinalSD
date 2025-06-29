# star.py - VERSÃO FINAL COM BUSCA DE CIDADES

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- URLs das APIs Externas ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
STANDARD_API_URL = "https://api.open-meteo.com/v1/forecast"

# --- Modelos Pydantic ---

# Modelo para a lista de cidades retornada pela busca
class CityInfo(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    country: str
    admin1: Optional[str] = None  # Estado/Região

# Modelo para o pedido de previsão do tempo (agora com coordenadas)
class WeatherRequest(BaseModel):
    latitude: float
    longitude: float
    is_coastal: bool
    local: str  # O nome completo para exibição, ex: "Lisboa, Portugal"

# Modelo para a resposta final da previsão
class WeatherResponse(BaseModel):
    local: str
    temperatura_c: float
    umidade: float
    vento_kph: float
    prob_chuva: float
    tamanho_onda_m: float
    temperatura_a: float
    taxa_uv: float
    precipitation_prob: float
    sensacao: float


# --- Aplicação FastAPI ---
app = FastAPI(title="API de Previsão do Tempo")

# <<< NOVO ENDPOINT: Para buscar uma lista de cidades >>>
@app.get("/search-cities", response_model=List[CityInfo])
def search_cities(name: str):
    logger.info(f"Buscando por cidades com o nome: {name}")
    # Pedimos 10 resultados para dar opções ao usuário
    params = {'name': name, 'count': 10, 'language': 'pt', 'format': 'json'}
    try:
        response = requests.get(GEOCODING_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('results'):
            return []  # Retorna lista vazia se não encontrar nada

        # Formata a resposta em uma lista do nosso modelo CityInfo
        city_list = [
            CityInfo(
                id=city['id'],
                name=city['name'],
                latitude=city['latitude'],
                longitude=city['longitude'],
                country=city.get('country', ''),
                admin1=city.get('admin1', '')
            ) for city in data['results']
        ]
        return city_list
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na API de Geocodificação: {e}")
        raise HTTPException(status_code=503, detail="Erro ao comunicar com o serviço de geocodificação.")

# <<< ENDPOINT MODIFICADO: Agora recebe coordenadas exatas >>>
@app.post("/previsao", response_model=WeatherResponse)
def obter_previsao(request_data: WeatherRequest):
    latitude = request_data.latitude
    longitude = request_data.longitude
    is_coastal = request_data.is_coastal
    local_nome = request_data.local

    try:
        if is_coastal:
            logger.info(f"Obtendo previsão COSTEIRA para: {local_nome}")
            # Para cidades costeiras, chamamos as duas APIs para obter todos os dados
            
            # Chamada para API Padrão (temperatura do ar, umidade, vento, chuva)
            standard_params = {'latitude': latitude, 'longitude': longitude,
                               'daily': 'uv_index_max,precipitation_probability_mean',
                               'hourly' : 'apparent_temperature',
                               'current': 'temperature_2m,relative_humidity_2m,rain,wind_speed_10m', 
                               'timezone': 'auto'
                               }
            standard_response = requests.get(STANDARD_API_URL, params=standard_params, timeout=10)
            standard_response.raise_for_status()
            standard_data = standard_response.json()
            current = standard_data['current']
            daily = standard_data['daily']
            hourly = standard_data['hourly']
            temperatura = current['temperature_2m']
            umidade = current['relative_humidity_2m']
            vento = current['wind_speed_10m']
            chuva = current['rain']
            uv = daily['uv_index_max'][0]
            prob_precipitacao = daily['precipitation_probability_mean'][0]
            sensacao_termica = hourly['apparent_temperature'][0]

            # Chamada para API Marítima (temperatura da água, ondas)
            marine_params = {'latitude': latitude, 'longitude': longitude, 
                             'hourly': 'sea_surface_temperature', 
                             'daily': 'wave_height_max', 
                             'timezone': 'auto'}
            marine_response = requests.get(MARINE_API_URL, params=marine_params, timeout=10)
            marine_response.raise_for_status()
            marine_data = marine_response.json()
            temperatura_agua = marine_data['hourly']['sea_surface_temperature'][0]
            ondas = marine_data['daily'].get('wave_height_max', [0.0])[0] or 0.0
            
            print(prob_precipitacao)
            print(sensacao_termica)
        else:
            logger.info(f"Obtendo previsão PADRÃO para: {local_nome}")
            # Para cidades do interior, chamamos apenas a API Padrão
            standard_params = {'latitude': latitude, 'longitude': longitude,
                               'daily': 'uv_index_max,precipitation_probability_mean',
                               'hourly' : 'apparent_temperature',
                               'current': 'temperature_2m,relative_humidity_2m,rain,wind_speed_10m', 
                               'timezone': 'auto'
                               }            
            standard_response = requests.get(STANDARD_API_URL, params=standard_params, timeout=10)
            standard_response.raise_for_status()
            standard_data = standard_response.json()
            current = standard_data['current']
            daily = standard_data['daily']
            hourly = standard_data['hourly']
            temperatura = current['temperature_2m']
            umidade = current['relative_humidity_2m']
            vento = current['wind_speed_10m']
            chuva = current['rain']
            ondas = 0.0
            temperatura_agua = 0.0
            uv = daily['uv_index_max'][0]
            prob_precipitacao = daily['precipitation_probability_mean'][0]
            sensacao_termica = hourly['apparent_temperature'][0]

            print(prob_precipitacao)
            print(sensacao_termica)

        prob_chuva = 100.0 if chuva > 0 else 0.0

        return WeatherResponse(
            local=local_nome,
            temperatura_c=temperatura,
            umidade=umidade,
            vento_kph=vento,
            prob_chuva=prob_chuva,
            tamanho_onda_m=ondas,
            temperatura_a=temperatura_agua,
            taxa_uv=uv,
            precipitation_prob= prob_precipitacao,
            sensacao=sensacao_termica,
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de comunicação com a API externa: {e}")
        raise HTTPException(status_code=503, detail=f"Erro ao comunicar com o serviço externo: {e}")
    except (KeyError, IndexError) as e:
        logger.error(f"Erro ao processar dados da API. Erro: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar os dados recebidos da API.")