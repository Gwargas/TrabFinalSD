from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

# URLs do backend
BACKEND_CITIES_URL = "http://127.0.0.1:8000/cities"
BACKEND_FORECAST_URL = "http://127.0.0.1:8000/forecast"

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
    .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    h1 { text-align: center; color: #007BFF; }
    form { display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px; }
    .input-group { display: flex; gap: 10px; align-items: center; }
    input[type="text"] { flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
    input[type="number"] { padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 80px; }
    button { padding: 10px 15px; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #0056b3; }
    .weather-info, .city-list { margin-top: 20px; }
    .weather-info h2 { font-size: 22px; }
    .error { color: #d9534f; background-color: #f2dede; border: 1px solid #ebccd1; padding: 15px; border-radius: 4px; text-align: center; }
    .city-list ul { list-style: none; padding: 0; }
    .city-list li { margin-bottom: 10px; }
    .city-selector { width: 100%; background: none; border: 1px solid #007BFF; color: #007BFF; text-align: left; padding: 10px; font-size: 16px; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
    .city-selector:hover, .city-selector.active { background-color: #e6f2ff; }
    .city-forecast-options { display: none; padding: 15px; margin-top: -1px; border: 1px solid #ddd; border-radius: 0 0 4px 4px; background-color: #f9f9f9; flex-direction: row; align-items: center; gap: 10px; }
    .accordion-button { display: flex; align-items: center; gap: 15px; background-color: #007BFF; color: white; cursor: pointer; padding: 18px; width: 100%; border: none; text-align: left; outline: none; font-size: 18px; transition: background-color 0.2s; border-radius: 4px; margin-top: 8px; }
    .accordion-button:hover, .accordion-button.active { background-color: #0056b3; }
    .accordion-panel { padding: 0 18px; background-color: #f9f9f9; display: none; overflow: hidden; border: 1px solid #ddd; border-top: none; border-radius: 0 0 4px 4px; }
    .accordion-panel p { margin: 12px 0; font-size: 16px; }

    .header-actions { text-align: center; margin-bottom: 20px; }
    .home-button {
        display: inline-block;
        padding: 10px 20px;
        background: #007BFF;
        color: white;
        text-decoration: none;
        border-radius: 4px;
        font-size: 16px;
        transition: background-color 0.2s;
    }
    .home-button:hover {
        background: #0056b3;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Previsão do Tempo</h1>

    {% if city_list or weather_data %}
      <div class="header-actions">
        <a href="/" class="home-button">↩️ Voltar ao Início</a>
      </div>
    {% endif %}
    
    <form method="post">
      <input type="hidden" name="action" value="search_cities">
      <div class="input-group">
        <input type="text" name="cidade" placeholder="Digite o nome da cidade" required>
        <button type="submit">Buscar</button>
      </div>
    </form>

    {% if city_list %}
      <div class="city-list">
        <h3>Por favor, selecione a cidade correta:</h3>
        <ul>
          {% for city in city_list %}
            <li>
              <button type="button" class="city-selector">
                {{ city.name }}{% if city.admin1 %}, {{ city.admin1 }}{% endif %}, {{ city.country }}
              </button>
              <form method="post" class="city-forecast-options">
                <input type="hidden" name="action" value="get_weather">
                <input type="hidden" name="latitude" value="{{ city.latitude }}">
                <input type="hidden" name="longitude" value="{{ city.longitude }}">
                <input type="hidden" name="local" value="{{ city.name }}{% if city.admin1 %}, {{ city.admin1 }}{% endif %}, {{ city.country }}">
                
                <label for="forecast_days_{{city.id}}">Dias:</label>
                <input type="number" id="forecast_days_{{city.id}}" name="forecast_days" min="1" max="16" value="7">
                
                <button type="submit">Obter Previsão</button>
              </form>
            </li>
          {% endfor %}
        </ul>
      </div>
    {% endif %}

    {% if weather_data %}
      <div class="weather-info">
        <h2>Previsão para {{ weather_data.local }}</h2>
        <div class="accordion">
          {% for day in weather_data.forecast %}
            <button class="accordion-button">
              <span>
                {% if day.precipitation_probability_max <= 35 %} ☀️
                {% elif day.precipitation_probability_max <= 65 %} ☁️
                {% else %} 🌧️
                {% endif %}
              </span>
              {{ day.date }}
            </button>
            <div class="accordion-panel">
              <p><strong>🌡️ Temperatura (Máx/Mín):</strong> {{ day.temperature_max }}°C / {{ day.temperature_min }}°C</p>
              {% if day.sensacao_termica is not none %}
                <p><strong>🌡️ Sensação Térmica (Início do dia):</strong> {{ day.sensacao_termica }}°C</p>
              {% endif %}
              <p><strong>☀️ Índice UV (Máx):</strong> {{ day.uv_index_max }}</p>
              <p><strong>💧 Chance de Chuva (Máx):</strong> {{ day.precipitation_probability_max }}%</p>
              {% if day.wave_height_max is not none %}
                <p><strong>🌊 Ondas (Máx):</strong> {{ day.wave_height_max }} m</p>
              {% else %} <p><strong>🌊 Sem informações sobre ondas no local!</p>
                   
              {% endif %}
            </div>
          {% endfor %}
        </div>
      </div>
    {% endif %}

    {% if error %}
      <div class="error"><p><strong>Erro:</strong> {{ error }}</p></div>
    {% endif %}
  </div>

  <script>
    var acc = document.getElementsByClassName("accordion-button");
    for (var i = 0; i < acc.length; i++) { acc[i].addEventListener("click", function() { this.classList.toggle("active"); var panel = this.nextElementSibling; if (panel.style.display === "block") { panel.style.display = "none"; } else { panel.style.display = "block"; } }); }
    var citySelectors = document.getElementsByClassName("city-selector");
    for (var i = 0; i < citySelectors.length; i++) { citySelectors[i].addEventListener("click", function() { var allOptions = document.getElementsByClassName("city-forecast-options"); for (var j = 0; j < allOptions.length; j++) { if (allOptions[j] !== this.nextElementSibling) { allOptions[j].style.display = "none"; } } var allSelectors = document.getElementsByClassName("city-selector"); for (var k = 0; k < allSelectors.length; k++) { if (allSelectors[k] !== this) { allSelectors[k].classList.remove("active"); } } this.classList.toggle("active"); var optionsPanel = this.nextElementSibling; if (optionsPanel.style.display === "flex") { optionsPanel.style.display = "none"; } else { optionsPanel.style.display = "flex"; } }); }
  </script>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    weather_data, error_message, city_list = None, None, None

    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "search_cities":
            cidade = request.form.get("cidade")
            if cidade:
                try:
                    response = requests.get(BACKEND_CITIES_URL, params={'name': cidade}, timeout=15)
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
            params = {
                "latitude": float(request.form.get("latitude")),
                "longitude": float(request.form.get("longitude")),
                "forecast_days": int(request.form.get("forecast_days", 7)),
                "local": request.form.get("local")
            }
            
            try:
                response = requests.get(BACKEND_FORECAST_URL, params=params, timeout=15)
                
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
                                  )

if __name__ == "__main__":
    app.run(debug=True, port=5000)