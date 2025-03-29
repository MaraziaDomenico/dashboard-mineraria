import os # Modulo per accedere alle variabili d'ambiente del sistema operativo (es. DATABASE_URL)
from configparser import ConfigParser # Modulo per leggere file di configurazione .ini (es. database.ini)
import urllib.parse as up # Modulo per analizzare e interpretare URL (utile per DATABASE_URL di Railway/Heroku)

def config(filename="database.ini", section="postgresql"):
    # Caso 1: se DATABASE_URL è definita nelle variabili d'ambiente (es. Railway)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        up.uses_netloc.append("postgres") # Aggiunge il supporto allo schema "postgres" per l'URL parser
        url = up.urlparse(database_url) # Esegue il parsing dell'URL di connessione

        # Restituisce i parametri estratti dall'URL
        return {
            "host": url.hostname,
            "database": url.path[1:],  # rimuove lo slash iniziale
            "user": url.username,
            "password": url.password,
            "port": url.port or 5432 # porta di default PostgreSQL
        }

    # Caso 2: se non esiste DATABASE_URL, legge i dati dal file .ini
    parser = ConfigParser()
    parser.read(filename) # Carica il file specificato

    # Verifica che la sezione esista
    if not parser.has_section(section):
        raise Exception(f"Sezione {section} non trovata in {filename}")

    # Converte la sezione del file .ini in dizionario
    return {key: value for key, value in parser.items(section)}
