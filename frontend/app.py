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

# --- Configuração ---
app = Flask(__name__)
# URL do NOSSO backend FastAPI. É aqui que a mágica da interação aplicação-aplicação acontece.
BACKEND_URL = "http://127.0.0.1:8000/previsao"

# --- Template HTML ---
# Adicionamos o campo para "Tamanho das Ondas"
HTML_TEMPLATE = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>Previsão do Tempo - Open-Meteo</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f0f2f5; color: #1c1e21; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
    .container { max-width: 600px; width: 100%; margin: auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    h1 { color: #1877f2; text-align: center; }
    form { display: flex; gap: 10px; margin-bottom: 25px; }
    input[type="text"] { flex-grow: 1; padding: 12px; border: 1px solid #dddfe2; border-radius: 6px; font-size: 16px; }
    input[type="text"]:focus { border-color: #1877f2; outline: none; }
    button { padding: 12px 20px; background-color: #1877f2; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; }
    button:hover { background-color: #166fe5; }
    .weather-info { margin-top: 20px; border-top: 1px solid #dddfe2; padding-top: 20px; }
    .weather-info h2 { font-size: 24px; color: #1c1e21; }
    .weather-info p { font-size: 18px; line-height: 1.6; }
    .error { color: #fa3e3e; background-color: #ffebe_e; border: 1px solid #fa3e3e; padding: 12px; border-radius: 6px; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Consulte a Previsão do Tempo</h1>
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
      <div class="error">
        <p><strong>Erro:</strong> {{ error }}</p>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

# --- Rota da Aplicação ---
@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    error_message = None

    if request.method == "POST":
        cidade = request.form.get("cidade")
        if cidade:
            payload = {"cidade": cidade}
            try:
                # O frontend (cliente) chama o backend (serviço)
                response = requests.post(BACKEND_URL, json=payload)
                
                if response.status_code == 200:
                    weather_data = response.json()
                else:
                    error_data = response.json()
                    error_message = error_data.get("detail", "Ocorreu um erro ao buscar a previsão.")
            
            except requests.exceptions.ConnectionError:
                error_message = "Não foi possível conectar ao serviço de previsão. O backend está rodando?"
            except Exception as e:
                error_message = f"Um erro inesperado ocorreu: {e}"

    return render_template_string(HTML_TEMPLATE, weather_data=weather_data, error=error_message)

if __name__ == "__main__":
    app.run(debug=True, port=5000)