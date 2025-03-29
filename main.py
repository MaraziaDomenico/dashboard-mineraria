from flask import Flask, render_template
# Flask: framework per creare web app
# render_template: serve a caricare file HTML da /templates

from routes import blueprint_api # Importa il blueprint con le API definite separatamente nel modulo `routes.py`
import time # Usato per introdurre un ritardo prima dell’avvio (utile in ambienti Docker)

def create_app():
    app = Flask(__name__) # Crea un'app Flask come oggetto principale
    app.register_blueprint(blueprint_api) # Registra il blueprint con le API, montate su "/api/..."

    # Definisce la route principale: quando un utente accede a "/", viene servito index.html
    @app.route("/")
    def index():
        return render_template("index.html")

    return app

if __name__ == "__main__":
    # Introduce una pausa di 2 secondi per dare tempo a Postgres di avviarsi
    # Utile soprattutto quando Flask è avviato in un container Docker che dipende dal database
    time.sleep(2)
    
    # Crea l'applicazione Flask tramite la funzione definita sopra
    app = create_app()
    
    # Avvia il server Flask in modalità debug, accessibile da tutte le interfacce (0.0.0.0)
    # Questo consente l’accesso esterno (es. da browser o altri container Docker)
    app.run(host="0.0.0.0", debug=True)
