import psycopg2  # Libreria per la connessione al database PostgreSQL
from random import uniform, choice  # Per generare valori casuali
from datetime import date, timedelta  # Per lavorare con date
from config import config  # Funzione personalizzata per ottenere i parametri di connessione

# Connessione al database PostgreSQL
params = config()
conn = psycopg2.connect(**params)
cur = conn.cursor()

# Definizione dei tipi di minerali per cui simulare dati di mercato
minerali = ['Oro', 'Litio', 'Nichel', 'Ferro', 'Rame', 'Cobalto', 'Bauxite']

# Possibili regioni di mercato (geografiche)
regioni = ['Nord America', 'Sud America', 'Europa', 'Asia', 'Africa', 'Oceania']

# Range realistici di prezzo per ciascun minerale ($ per tonnellata, tranne oro che è per oz e convertito)
range_prezzi = {
    'Oro': (45000, 65000),
    'Litio': (15000, 25000),
    'Nichel': (18000, 28000),
    'Ferro': (80, 150),
    'Rame': (8000, 12000),
    'Cobalto': (25000, 35000),
    'Bauxite': (30, 60)
}

# Calcolo dell'intervallo di date da 1 gennaio ad oggi
anno_corrente = date.today().year
data_inizio = date(anno_corrente, 1, 1)
data_fine = date.today()
delta = data_fine - data_inizio  # Differenza in giorni

# Pulizia della tabella Mercato e reset dell'ID autoincrementale
cur.execute("TRUNCATE TABLE Mercato RESTART IDENTITY")

# Inserimento dei dati simulati
for tipo in minerali:
    prezzo_min, prezzo_max = range_prezzi[tipo]

    for i in range(delta.days + 1):
        data = data_inizio + timedelta(days=i)  # Data corrente nel ciclo
        progress = i / delta.days  # Progressione nel tempo: da 0 a 1

        # Simula l'andamento di mercato: prezzo base aumenta leggermente nel tempo
        prezzo_base = prezzo_min + (prezzo_max - prezzo_min) * progress

        # Genera il prezzo con una variazione del ±10%
        prezzo = round(uniform(prezzo_base * 0.9, prezzo_base * 1.1), 2)

        # Seleziona una regione casuale tra quelle disponibili
        regione = choice(regioni)

        # Inserimento nel database
        cur.execute("""
            INSERT INTO Mercato (
                Tipo_Minerale, Prezzo, Data, Regione_Mercato
            ) VALUES (%s, %s, %s, %s)
        """, (tipo, prezzo, data, regione))

# Committa tutte le operazioni (scrittura definitiva)
conn.commit()

# Chiude la connessione al database
cur.close()
conn.close()

# Messaggi informativi
print(f"Dati di mercato inseriti con successo per il periodo {data_inizio} - {data_fine}.")
print(f"Minerali inseriti: {', '.join(minerali)}")
print(f"Regioni utilizzate: {', '.join(regioni)}")
