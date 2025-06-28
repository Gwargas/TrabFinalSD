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

from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)
BACKEND_URL = "http://127.0.0.1:8000/previsao"

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
    .weather-info { margin-top: 20px; }
    .weather-info h2 { font-size: 24px; }
    .weather-info p { font-size: 16px; margin: 5px 0; }
    .error { color: #d9534f; background-color: #f2dede; border: 1px solid #ebccd1; padding: 15px; border-radius: 4px; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Previsão do Tempo</h1>
    <form method="post">
      <div class="input-group">
        <input type="text" name="cidade" placeholder="Digite o nome da cidade" required>
        <button type="submit">Buscar</button>
      </div>
      <div class="checkbox-group">
        <input type="checkbox" id="is_coastal" name="is_coastal" value="true">
        <label for="is_coastal">É uma cidade costeira? (para obter dados de ondas)</label>
      </div>
    </form>

    {% if weather_data %}
      <div class="weather-info">
        <h2>Previsão para {{ weather_data.local }}</h2>
        <p><strong>🌡️ Temperatura:</strong> {{ weather_data.temperatura_c }} °C</p>
        
        <!-- <<< MUDANÇA: Só exibe os campos se eles tiverem valor -->
        {% if weather_data.umidade > 0 %}
          <p><strong>💧 Umidade:</strong> {{ weather_data.umidade }}%</p>
        {% endif %}
        {% if weather_data.vento_kph > 0 %}
          <p><strong>💨 Vento:</strong> {{ weather_data.vento_kph }} km/h</p>
        {% endif %}
        {% if weather_data.tamanho_onda_m > 0 %}
          <p><strong>🌊 Tamanho da(s) Onda(s):</strong> {{ weather_data.tamanho_onda_m }} m</p>
        {% endif %}
        {% if weather_data.temperatura_a > 0 %}
          <p><strong>🌡️ Temperatura da Agua:</strong> {{ weather_data.temperatura_a }} °C</p>
        {% endif %}

        <p><strong>🌦️ Chuva:</strong> {{ weather_data.prob_chuva }}</p>
      </div>
    {% endif %}

    {% if error %}
      <div class="error">
        <p><strong>Erro:</strong> {{ error }}</p>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

# --- Rota Flask (sem alterações) ---
@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    error_message = None
    if request.method == "POST":
        cidade = request.form.get("cidade")
        is_coastal = True if request.form.get('is_coastal') else False
        if cidade:
            payload = {"cidade": cidade, "is_coastal": is_coastal}
            try:
                response = requests.post(BACKEND_URL, json=payload, timeout=15)
                if response.status_code == 200:
                    weather_data = response.json()
                else:
                    error_data = response.json()
                    error_message = error_data.get("detail", "Ocorreu um erro desconhecido.")
            except requests.exceptions.RequestException:
                error_message = "Não foi possível conectar ao serviço de previsão."
        else:
            error_message = "Por favor, insira o nome de uma cidade."
    return render_template_string(HTML_TEMPLATE, weather_data=weather_data, error=error_message)

if __name__ == "__main__":
    app.run(debug=True, port=5000)