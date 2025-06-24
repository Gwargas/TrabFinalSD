from flask import Flask, render_template

#referenciando esse arquivo
app = Flask(__name__)

#definindo uma rota para apenas não ir para 404
#a rota é definida para a func logo abaixo
@app.route('/')
def index():
    return render_template('index.html')



#quando rodamos esse arquivo em especifico, no python app.py estamos def
#q esse arq é a main, assim, outros arquivos n rodam o que está no if qnd importado
#se rodar o arquivo app.py vai rodar o que está dentro do if
#caso seja importado o que está dentro do if n roda
if(__name__ == "__main__"):
    app.run(debug=True)