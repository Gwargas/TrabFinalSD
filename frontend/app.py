#from flask import Flask, render_template

#referenciando esse arquivo
#app = Flask(__name__)

#definindo uma rota para apenas não ir para 404
#a rota é definida para a func logo abaixo
#@app.route('/')

#def index():
    #return render_template('index.html')



#quando rodamos esse arquivo em especifico, no python app.py estamos def
#q esse arq é a main, assim, outros arquivos n rodam o que está no if qnd importado
#se rodar o arquivo app.py vai rodar o que está dentro do if
#caso seja importado o que está dentro do if n roda
#if(__name__ == "__main__"):
    #app.run(debug=True)

# frontend_app.py

# app.py - VERSÃO CORRIGIDA COM LÓGICA DE EXIBIÇÃO

# app.py - VERSÃO FINAL COM FLUXO DE DOIS PASSOS

from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)
# URLs do nosso backend
BACKEND_SEARCH_URL = "http://127.0.0.1:8000/search-cities"
BACKEND_PREVISAO_URL = "http://127.0.0.1:8000/previsao"

# --- Template HTML ---
HTML_TEMPLATE = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Previsão do Tempo - Open-Meteo</title>
  <style>
    body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; padding: 20px; }
    .container { max-width: 600px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    h1 { text-align: center; color: #007BFF; }
    form { display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px; }
    .input-group { display: flex; gap: 10px; }
    input[type="text"] { flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
    button { padding: 10px 15px; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #0056b3; }
    .checkbox-group { display: flex; align-items: center; gap: 5px; }
    .weather-info, .city-list { margin-top: 20px; }
    .weather-info h2, .city-list h3 { font-size: 22px; }
    .weather-info p { font-size: 16px; margin: 5px 0; }
    .error { color: #d9534f; background-color: #f2dede; border: 1px solid #ebccd1; padding: 15px; border-radius: 4px; text-align: center; }
    /* Estilos para a lista de cidades */
    .city-list ul { list-style: none; padding: 0; }
    .city-list li { margin-bottom: 10px; }
    .link-button { background: none; border: 1px solid #007BFF; color: #007BFF; width: 100%; text-align: left; padding: 10px; font-size: 16px; border-radius: 4px; }
    .link-button:hover { background: #e6f2ff; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Previsão do Tempo</h1>
    
    <!-- Formulário de Busca Inicial -->
    <form method="post">
      <input type="hidden" name="action" value="search_cities">
      <div class="input-group">
        <input type="text" name="cidade" placeholder="Digite o nome da cidade" required>
        <button type="submit">Buscar</button>
      </div>
      <div class="checkbox-group">
        <input type="checkbox" id="is_coastal" name="is_coastal" value="true" {% if is_coastal %}checked{% endif %}>
        <label for="is_coastal">É uma cidade costeira? (para obter dados de ondas)</label>
      </div>
    </form>

    <!-- Exibe a lista de cidades para seleção -->
    {% if city_list %}
      <div class="city-list">
        <h3>Por favor, selecione a cidade correta:</h3>
        <ul>
          {% for city in city_list %}
            <li>
              <form method="post">
                <input type="hidden" name="action" value="get_weather">
                <input type="hidden" name="latitude" value="{{ city.latitude }}">
                <input type="hidden" name="longitude" value="{{ city.longitude }}">
                <input type="hidden" name="local" value="{{ city.name }}{% if city.admin1 %}, {{ city.admin1 }}{% endif %}, {{ city.country }}">
                <input type="hidden" name="is_coastal" value="{{ is_coastal }}">
                <button type="submit" class="link-button">
                  {{ city.name }}{% if city.admin1 %}, {{ city.admin1 }}{% endif %}, {{ city.country }}
                </button>
              </form>
            </li>
          {% endfor %}
        </ul>
      </div>
    {% endif %}

    <!-- Exibe a previsão do tempo final -->
    {% if weather_data %}
      <div class="weather-info">
        <h2>Previsão para {{ weather_data.local }}</h2>
        <p><strong>🌡️ Temperatura do Ar:</strong> {{ weather_data.temperatura_c }} °C</p>
        <p><strong>🌡️ Sensação Térmica:</strong> {{ weather_data.sensacao }} °C</p>
        <p><strong>🌡️ Taxa Raios Uv:</strong> {{ weather_data.taxa_uv }}</p>
        {% if weather_data.umidade > 0 %}<p><strong>💧 Umidade:</strong> {{ weather_data.umidade }}%</p>{% endif %}
        {% if weather_data.vento_kph > 0 %}<p><strong>💨 Vento:</strong> {{ weather_data.vento_kph }} km/h</p>{% endif %}
        {% if weather_data.tamanho_onda_m > 0 %}<p><strong>🌊 Tamanho da(s) Onda(s):</strong> {{ weather_data.tamanho_onda_m }} m</p>{% endif %}
        {% if weather_data.temperatura_a > 0 %}<p><strong>🌡️ Temperatura da Água:</strong> {{ weather_data.temperatura_a }} °C</p>{% endif %}
        <p><strong>🌦️ Média da probabilidade de Chuva hoje:</strong> {{ weather_data.precipitation_prob}} %</p>
        <p><strong>🌦️ Chovendo:</strong> {{ 'Sim' if weather_data.prob_chuva > 0 else 'Não' }}</p>
        
      </div>
    {% endif %}

    <!-- Exibe erros -->
    {% if error %}
      <div class="error"><p><strong>Erro:</strong> {{ error }}</p></div>
    {% endif %}
  </div>
</body>
</html>
"""

# --- Rota Flask ---
@app.route("/", methods=["GET", "POST"])
def index():
    weather_data, error_message, city_list = None, None, None
    is_coastal_checked = False

    if request.method == "POST":
        action = request.form.get("action")
        # Mantém o estado do checkbox entre as requisições
        is_coastal_checked = True if request.form.get('is_coastal') == 'true' or request.form.get('is_coastal') == 'True' else False

        if action == "search_cities":
            cidade = request.form.get("cidade")
            if cidade:
                try:
                    response = requests.get(BACKEND_SEARCH_URL, params={'name': cidade}, timeout=15)
                    if response.status_code == 200:
                        city_list = response.json()
                        if not city_list:
                            error_message = f"Nenhuma cidade encontrada para '{cidade}'."
                    else:
                        error_message = response.json().get("detail", "Erro ao buscar cidades.")
                except requests.exceptions.RequestException:
                    error_message = "Não foi possível conectar ao serviço de busca."
            else:
                error_message = "Por favor, insira o nome de uma cidade."

        elif action == "get_weather":
            payload = {
                "latitude": float(request.form.get("latitude")),
                "longitude": float(request.form.get("longitude")),
                "is_coastal": is_coastal_checked,
                "local": request.form.get("local")
            }
            try:
                response = requests.post(BACKEND_PREVISAO_URL, json=payload, timeout=15)
                if response.status_code == 200:
                    weather_data = response.json()
                else:
                    error_message = response.json().get("detail", "Erro ao obter previsão.")
            except requests.exceptions.RequestException:
                error_message = "Não foi possível conectar ao serviço de previsão."

    return render_template_string(HTML_TEMPLATE, 
                                  weather_data=weather_data, 
                                  error=error_message, 
                                  city_list=city_list,
                                  is_coastal=is_coastal_checked)

if __name__ == "__main__":
    app.run(debug=True, port=5000)