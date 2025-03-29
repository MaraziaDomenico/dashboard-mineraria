import psycopg2  # Libreria per connettersi al database PostgreSQL
from random import choice, randint, uniform  # Per generare dati casuali
from datetime import date, timedelta  # Per gestire date
from config import config  # Funzione per leggere la configurazione del database

# Connessione al database usando i parametri definiti nel file config.py
params = config()
conn = psycopg2.connect(**params)
cur = conn.cursor()

# Possibili tipi di incidente da simulare
tipi_incidente = [
    "Crollo galleria", "Fuga di gas", "Allagamento", "Corto circuito",
    "Guasto meccanico", "Caduta materiali", "Malore operatore"
]

# Livelli di gravità ammessi (conformi al vincolo della tabella)
gravita_possibili = ["Lieve", "Moderata", "Grave"]

# Misure correttive che possono essere state applicate dopo l'incidente
misure_correttive = [
    "Evacuazione area", "Manutenzione straordinaria", "Formazione del personale",
    "Revisione impianti", "Aumento ventilazione", "Controllo strutturale"
]

# Funzione per generare una data casuale negli ultimi 60 giorni
def data_casuale():
    giorni_fa = randint(0, 60)
    return date.today() - timedelta(days=giorni_fa)

# Inserisce 3 incidenti casuali per ciascuna delle 6 miniere (con ID da 1 a 6)
for id_miniera in range(1, 7):
    for _ in range(3):  # Tre incidenti per ogni miniera
        tipo = choice(tipi_incidente)  # Tipo incidente casuale
        gravita = choice(gravita_possibili)  # Gravità casuale
        data = data_casuale()  # Data incidente
        misura = choice(misure_correttive)  # Misura correttiva casuale
        costo_danno = round(uniform(500.0, 8000.0), 2)  # Costo danno moderato (in AUD)
        feriti = randint(0, 3)  # Numero feriti, tra 0 e 3
        stop_minuti = round(uniform(30, 300), 2)  # Tempo fermata in minuti

        # Inserimento nel database, seguendo lo schema della tabella `Sicurezza`
        cur.execute("""
            INSERT INTO Sicurezza (
                ID_Miniera, Tipo_Incidente, Gravita, Data,
                Misure_Correttive, Costo_Danno, Numero_Feriti, Tempo_Fermata_Operazioni
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (id_miniera, tipo, gravita, data, misura, costo_danno, feriti, stop_minuti))

# Salvataggio dei dati nel database
conn.commit()

# Chiusura della connessione al database
cur.close()
conn.close()

# Messaggio finale di conferma
print("Incidenti di sicurezza generati con successo.")
