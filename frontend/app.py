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

from flask import Flask, render_template_string, request
import requests

# --- Configuration ---
app = Flask(__name__)
BACKEND_URL = "http://127.0.0.1:8000/previsao"

# --- HTML Template ---
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
    form { display: flex; gap: 10px; margin-bottom: 20px; }
    input[type="text"] { flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
    button { padding: 10px 15px; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #0056b3; }
    .weather-info { margin-top: 20px; }
    .weather-info p { font-size: 16px; margin: 5px 0; }
    .error { color: red; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Previsão do Tempo</h1>
    <form method="post">
      <input type="text" name="cidade" placeholder="Digite o nome da cidade" required>
      <button type="submit">Buscar</button>
    </form>

    {% if weather_data %}
      <div class="weather-info">
        <h2>Previsão para {{ weather_data.local }}</h2>
        <p><strong>🌡️ Temperatura:</strong> {{ weather_data.temperatura_c }} °C</p>
        <p><strong>💧 Umidade:</strong> {{ weather_data.umidade }}%</p>
        <p><strong>💨 Vento:</strong> {{ weather_data.vento_kph }} km/h</p>
        <p><strong>🌊 Tamanho das Ondas:</strong> {{ weather_data.tamanho_onda_m }} m</p>
        <p><strong>🌦️ Chance de Chuva:</strong> {{ weather_data.prob_chuva }}%</p>
      </div>
    {% endif %}

    {% if error %}
      <p class="error"><strong>Erro:</strong> {{ error }}</p>
    {% endif %}
  </div>
</body>
</html>
"""

# --- Flask Route ---
@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    error = None

    if request.method == "POST":
        cidade = request.form.get("cidade")
        if cidade:
            try:
                payload = {"cidade": cidade}
                response = requests.post(BACKEND_URL, json=payload)
                response.raise_for_status()
                weather_data = response.json()
            except requests.exceptions.ConnectionError:
                error = "Não foi possível conectar ao backend. Verifique se ele está rodando."
            except Exception as e:
                error = f"Ocorreu um erro: {e}"
        else:
            error = "Por favor, insira o nome de uma cidade."

    return render_template_string(HTML_TEMPLATE, weather_data=weather_data, error=error)

if __name__ == "__main__":
    app.run(debug=True, port=5000)