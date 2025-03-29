import psycopg2
from config import config
from datetime import date, timedelta
import random

def insert_azienda_e_miniere():
    connection = None
    try:
        # Caricamento dei parametri di configurazione del database dal file config
        params = config()
        print("Connecting to the PostgreSQL database...")

        # Connessione al database PostgreSQL tramite psycopg2
        connection = psycopg2.connect(**params)
        cursor = connection.cursor()

        # ===================================
        # INSERIMENTO DI UNA NUOVA AZIENDA
        # ===================================

        # Query SQL per inserire un record nella tabella "Azienda"
        insert_azienda_query = """
        INSERT INTO Azienda (
            Nome, Settore, Localita, Anno_Fondazione, Email, Telefono,
            Indirizzo1, Indirizzo2
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING ID_Azienda;
        """

        # Esecuzione della query con valori fittizi
        cursor.execute(insert_azienda_query, (
            "Western Minerals Ltd",                   # Nome azienda
            "Minerario",                              # Settore
            "Perth, Western Australia",               # Località
            1998,                                      # Anno di fondazione
            "info@westernminerals.au",                # Email
            "+61 8 1234 5678",                         # Telefono
            "1 Mining Way",                            # Indirizzo 1
            "Unit 2, Industrial Estate"                # Indirizzo 2
        ))

        # Recupera l'ID assegnato automaticamente dal database alla nuova azienda
        id_azienda = cursor.fetchone()[0]
        print(f"Azienda inserita con ID: {id_azienda}")

        # ====================================================
        # CREAZIONE DI UNA LISTA DI MINIERE DA INSERIRE
        # ====================================================
        # Ogni miniera ha nome, tipo di minerale, latitudine e longitudine
        miniere = [
            {"nome": "Pilbara Iron Mine", "tipo": "Ferro", "lat": -22.2955, "lon": 118.0000},
            {"nome": "Kalgoorlie Super Pit", "tipo": "Oro", "lat": -30.7489, "lon": 121.4656},
            {"nome": "Ravensthorpe Nickel Mine", "tipo": "Nichel", "lat": -33.5781, "lon": 120.0486},
            {"nome": "Greenbushes Lithium Mine", "tipo": "Litio", "lat": -33.8527, "lon": 116.0587},
            {"nome": "Mount Keith Nickel", "tipo": "Nichel", "lat": -27.3000, "lon": 120.3667},
            {"nome": "Paraburdoo Iron Ore", "tipo": "Ferro", "lat": -23.2167, "lon": 117.6667}
        ]

        # Query per inserire una miniera associata all'azienda
        insert_miniera_query = """
        INSERT INTO Miniera (
            ID_Azienda, Nome, Tipo_Minerale, Capacita, Stato,
            Latitudine, Longitudine, Profondita_Media, Area_Km2,
            Data_Apertura, Numero_Lavoratori, Tecnologie_Utilizzate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        # ====================================================
        # CICLO PER INSERIRE LE MINIERE UNA PER UNA
        # ====================================================
        for m in miniere:
            # Genera valori realistici randomizzati per ogni attributo
            cursor.execute(insert_miniera_query, (
                id_azienda,                              # Collegamento all'azienda appena creata
                m["nome"],                               # Nome miniera
                m["tipo"],                               # Tipo di minerale estratto
                random.randint(8000, 20000),             # Capacità della miniera in tonnellate
                random.choice(["Attiva", "In Attivazione", "Chiusa"]),  # Stato operativo
                m["lat"],                                # Latitudine
                m["lon"],                                # Longitudine
                random.randint(100, 1500),               # Profondità media in metri
                round(random.uniform(5.0, 30.0), 2),     # Area della miniera in km²
                date.today() - timedelta(days=random.randint(1000, 5000)),  # Data di apertura
                random.randint(80, 300),                 # Numero di lavoratori
                random.choice([                          # Tecnologie usate nella miniera
                    "Scavo Meccanico, Sensori IoT",
                    "Robotica Mineraria",
                    "AI + IoT Monitoring",
                    "Trivellazione Profonda",
                    "Estrazione a cielo aperto"
                ])
            ))
            print(f"Miniera '{m['nome']}' inserita.")

        # Commit finale per salvare i cambiamenti nel database
        connection.commit()
        print("Tutti i dati sono stati inseriti e salvati nel database.")

    except (Exception, psycopg2.DatabaseError) as error:
        # Gestione degli errori in fase di esecuzione
        print("Errore durante l'inserimento:", error)
    finally:
        # Chiusura della connessione al database
        if connection is not None:
            connection.close()
            print("Connessione al database chiusa.")

# ======================================
# Avvio dello script se eseguito diretto
# ======================================
if __name__ == "__main__":
    insert_azienda_e_miniere()
