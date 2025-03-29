# Importazione dei moduli necessari
import psycopg2  # Libreria per la connessione al database PostgreSQL
from random import uniform, choice, randint  # Funzioni per generare dati casuali
from datetime import date, timedelta  # Gestione delle date
from config import config  # Funzione personalizzata per leggere la configurazione del database

# Legge i parametri di connessione dal file di configurazione
params = config()

# Connessione al database PostgreSQL
conn = psycopg2.connect(**params)
cur = conn.cursor()

# Funzione che genera una data casuale negli ultimi 30 giorni
def data_casuale():
    giorni_fa = randint(0, 30)  # Numero di giorni fa, da oggi
    return date.today() - timedelta(days=giorni_fa)

# Lista dei possibili metodi di estrazione mineraria
metodi_estrattivi = ['Cielo aperto', 'Sotterranea', 'Idraulica', 'Frantumazione']

# Inserimento dati nella tabella Produzione
# Ciclo per ogni ID di miniera: si assumono 6 miniere con ID da 1 a 6
for id_miniera in range(1, 7):
    # Per ogni miniera, genera 5 record di produzione
    for _ in range(5):
        data = data_casuale()  # Data casuale tra oggi e 30 giorni fa
        quantita = round(uniform(100.0, 1000.0), 2)  # Quantità prodotta in tonnellate (float con 2 decimali)
        purezza = round(uniform(70.0, 99.9), 2)      # Purezza del materiale estratto in percentuale
        tempo_estrazione = round(uniform(2.0, 12.0), 2)  # Tempo di estrazione in ore
        metodo = choice(metodi_estrattivi)  # Metodo di estrazione selezionato casualmente

        # Esegue l'inserimento del record nel database
        cur.execute("""
            INSERT INTO Produzione (
                ID_Miniera, Data, Quantita, Purezza, Tempo_Estrazione, Metodo_Estrattivo
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            id_miniera,          # Collegamento alla miniera
            data,                # Data di produzione
            quantita,            # Quantità prodotta
            purezza,             # Grado di purezza del materiale
            tempo_estrazione,    # Tempo impiegato per l'estrazione
            metodo               # Metodo utilizzato per estrarre
        ))

# Conferma le operazioni di inserimento nel database
conn.commit()

# Chiude il cursore e la connessione per liberare risorse
cur.close()
conn.close()

# Messaggio di conferma
print("Dati di produzione inseriti con successo per tutte le miniere.")
