from flask import Flask, render_template
from routes import blueprint_api
import time

def create_app():
    app = Flask(__name__)
    app.register_blueprint(blueprint_api)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app

if __name__ == "__main__":
    time.sleep(2)  # Aspetta che Postgres sia pronto
    app = create_app()
    app.run(host="0.0.0.0", debug=True)
