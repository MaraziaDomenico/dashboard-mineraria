import os
from configparser import ConfigParser
import urllib.parse as up

def config(filename="database.ini", section="postgresql"):
    # Se DATABASE_URL è presente (es. Railway), parse e restituisce i parametri
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        up.uses_netloc.append("postgres")
        url = up.urlparse(database_url)

        return {
            "host": url.hostname,
            "database": url.path[1:],  # rimuove lo slash iniziale
            "user": url.username,
            "password": url.password,
            "port": url.port or 5432
        }

    # Altrimenti legge dal file .ini (es. in locale)
    parser = ConfigParser()
    parser.read(filename)

    if not parser.has_section(section):
        raise Exception(f"Sezione {section} non trovata in {filename}")

    return {key: value for key, value in parser.items(section)}
