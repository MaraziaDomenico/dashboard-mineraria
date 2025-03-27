import psycopg2
from config import config

def test_connessione():
    try:
        params = config()
        print("🔍 Parametri di connessione:", params)

        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print("✅ Connessione riuscita! Versione PostgreSQL:", db_version[0])
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Errore nella connessione al database:")
        print(e)

if __name__ == "__main__":
    test_connessione()
