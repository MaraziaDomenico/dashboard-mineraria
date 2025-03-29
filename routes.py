import pandas as pd
import psycopg2
from flask import Blueprint, jsonify
from config import config
import plotly.graph_objs as go
import plotly.io as pio
from plotly.colors import qualitative
from flask import send_file
import io

# Crea un Blueprint Flask chiamato 'api'.
# I Blueprint servono per organizzare il codice in componenti riutilizzabili (es. api separate, moduli).
# '__name__' permette a Flask di sapere dove si trova questo blueprint nel progetto.
blueprint_api = Blueprint('api', __name__)

# === Utility ===
def get_connection():
    return psycopg2.connect(**config())


def plotly_layout(title, margin=dict(t=40, l=40, r=40, b=40), **kwargs):
    return dict(
        title=title, # Titolo del grafico
        template='plotly_white', # Tema bianco come sfondo (pulito e leggibile)
        margin=margin, # Margini esterni del grafico
        **kwargs # Estensione del layout con altri argomenti forniti
    )

# === API: Miniere ===
# Questa route API fornisce un elenco completo delle miniere presenti nel database,
# includendo informazioni relative anche all'azienda associata.
@blueprint_api.route("/api/miniere")
def api_miniere():
    conn = get_connection()
    query = """
        SELECT m.id_miniera, m.nome, m.tipo_minerale, m.stato, m.capacita, m.numero_lavoratori,
               m.latitudine, m.longitudine, a.nome AS nome_azienda
        FROM miniera m
        JOIN azienda a ON m.id_azienda = a.id_azienda;
    """
    df = pd.read_sql_query(query, conn) # Esegue la query SQL usando pandas, che restituisce i risultati come DataFrame
    conn.close() 

    return jsonify(df.to_dict(orient='records')) # Restituisce i dati in formato JSON, convertendo il DataFrame in un dizionario.

# === API: Grafico Produzione ===
@blueprint_api.route("/api/grafico_produzione_html")
def grafico_produzione_html():
    conn = get_connection()
    query = """
        SELECT 
            m.tipo_minerale,
            SUM(p.quantita) AS quantita_totale,
            AVG(p.purezza) AS purezza_media
        FROM produzione p
        JOIN miniera m ON p.id_miniera = m.id_miniera
        GROUP BY m.tipo_minerale
        ORDER BY quantita_totale DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Creazione del grafico con barre più larghe e colori più contrastanti
    fig = go.Figure([
        go.Bar(
            x=df['tipo_minerale'],
            y=df['quantita_totale'], 
            name='Quantità (ton)', 
            marker_color='#3498db',  # Blu più intenso
            width=0.7,  # Barre più larghe
            opacity=0.9
        ),
        go.Scatter(
            x=df['tipo_minerale'], 
            y=df['purezza_media'], 
            name='Purezza (%)', 
            yaxis='y2',
            mode='lines+markers', 
            line=dict(color='#e74c3c', width=3),  # Rosso più intenso
            marker=dict(size=8)
        )
    ])

    # Layout ottimizzato per enfatizzare le quantità
    fig.update_layout(
        **plotly_layout(
            title='',
            xaxis_title='Tipo Minerale',
            yaxis=dict(
                title='<b>Quantità Totale (ton)</b>',  # Titolo in grassetto
                rangemode='tozero', 
                automargin=True, 
                tickfont=dict(size=12),
                gridcolor='#f0f0f0',  # Griglia più leggera
                title_font=dict(size=14, color='#3498db')  # Colore coordinato con le barre
            ),
            yaxis2=dict(
                title='Purezza (%)', 
                overlaying='y', 
                side='right', 
                tickfont=dict(size=12),
                title_font=dict(size=14, color='#e74c3c'),  # Colore coordinato con la linea
                gridcolor='rgba(0,0,0,0)'  # Rimuove la griglia per l'asse destro
            ),
            barmode='group',
            bargap=0.15,  # Più spazio tra gruppi di barre
            plot_bgcolor='white',  # Sfondo bianco
            paper_bgcolor='white',
            margin=dict(l=50, r=50, b=80, t=30, pad=4),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
    )

    # Enfatizza ulteriormente le barre delle quantità
    fig.update_traces(
        selector={'name': 'Quantità (ton)'},
        hovertemplate='<b>%{x}</b><br>Quantità: %{y:.0f} ton<extra></extra>'
    )

    # Riduci la prominenza della linea di purezza
    fig.update_traces(
        selector={'name': 'Purezza (%)'},
        hovertemplate='<b>%{x}</b><br>Purezza: %{y:.1f}%<extra></extra>'
    )

    return pio.to_html(fig, full_html=False)

# === API: Consumi Generali ===
@blueprint_api.route("/api/consumi_generali")
def statistiche_generali():
    # Coefficienti per stimare il consumo di elettricità, acqua e CO₂ in base alla produzione
    # Ogni coefficiente ha:
    #  - "q": fattore moltiplicativo per la quantità estratta
    #  - "t": fattore moltiplicativo per il tempo di estrazione
    #  - "m": valore fisso legato al metodo estrattivo usato
    #  - "div": divisore per riportare il totale nell’unità desiderata (es. GWh, ML, kt)
    COEFF = {
        "elettricita": {
            "q": 0.5,  # kWh per tonnellata
            "t": 20,   # kWh per ora di estrazione
            "m": {     # Consumo fisso per metodo
                "Frantumazione": 300,
                "Sotterranea": 200,
                "Idraulica": 150,
                "Cielo aperto": 100
            },
            "div": 1_000_000  # da kWh a GWh
        },
        "acqua": {
            "q": 2.5,  # litri per tonnellata
            "t": 10,   # litri per ora di estrazione
            "m": {
                "Frantumazione": 100,
                "Sotterranea": 80,
                "Idraulica": 200,
                "Cielo aperto": 50
            },
            "div": 1_000_000  # da litri a megalitri (ML)
        },
        "co2": {
            "q": 0.2,  # kg di CO₂ per tonnellata
            "t": 5,    # kg di CO₂ per ora di estrazione
            "m": {
                "Frantumazione": 50,
                "Sotterranea": 40,
                "Idraulica": 30,
                "Cielo aperto": 20
            },
            "div": 1_000  # da kg a tonnellate (kt)
        }
    }

    # Coefficienti per il calcolo del costo operativo (valuta: AUD - Dollaro Australiano)
    COSTO_OPERATIVO_AUD = {
        "q": 24.75,  # AUD per tonnellata estratta
        "t": 82.5,   # AUD per ora di estrazione
        "m": {       # costo fisso per tipo di metodo estrattivo
            "Frantumazione": 8250,
            "Sotterranea": 6600,
            "Idraulica": 5775,
            "Cielo aperto": 4125
        },
        "div": 1_000_000  # da AUD a milioni di AUD
    }

    # Connessione al database e recupero dei dati di produzione
    conn = get_connection()
    df = pd.read_sql_query("SELECT quantita, tempo_estrazione, metodo_estrattivo FROM produzione;", conn)
    conn.close()

    # Funzione generica che applica la formula:
    # (quantità × coeff["q"]) + (tempo × coeff["t"]) + (valore associato al metodo)
    def calcola(coeff):
        return (
            df["quantita"] * coeff["q"] +                          # parte variabile per quantità
            df["tempo_estrazione"] * coeff["t"] +                 # parte variabile per tempo
            df["metodo_estrattivo"].map(coeff["m"]).fillna(4000)  # parte fissa per metodo, fallback 4000 se non trovato
        )

    # Calcolo delle tre metriche ambientali e del costo
    consumo_elettricita = calcola(COEFF["elettricita"])  # kWh
    consumo_acqua = calcola(COEFF["acqua"])              # litri
    emissioni_co2 = calcola(COEFF["co2"])                # kg
    costo_operativo_aud = calcola(COSTO_OPERATIVO_AUD)   # AUD

    # Restituzione dei risultati in formato JSON, convertiti in unità di misura leggibili
    return jsonify({
        "consumo_elettricita_gwh": round(consumo_elettricita.sum() / COEFF["elettricita"]["div"], 3),  # GWh
        "consumo_acqua_ml": round(consumo_acqua.sum() / COEFF["acqua"]["div"], 3),                    # Megalitri
        "emissioni_co2_kt": round(emissioni_co2.sum() / COEFF["co2"]["div"], 3),                      # Kiloton
        "costo_operativo_totale": round(costo_operativo_aud.sum() / COSTO_OPERATIVO_AUD["div"], 3)    # Milioni AUD
    })



# === API: Grafico Sicurezza ===
@blueprint_api.route("/api/grafico_sicurezza_html")  # Definizione dell’endpoint API accessibile via /api/grafico_sicurezza_html
def grafico_sicurezza_html():
    # Connessione al database PostgreSQL
    conn = get_connection()

    # Query SQL per contare quanti incidenti si sono verificati per ogni tipo
    query = """
        SELECT tipo_incidente, COUNT(*) AS numero
        FROM sicurezza
        GROUP BY tipo_incidente
        ORDER BY numero DESC;
    """
    
    # Esecuzione della query e caricamento del risultato in un DataFrame Pandas
    df = pd.read_sql_query(query, conn)

    # Chiusura connessione al database
    conn.close()

    # === Creazione del grafico a torta con Plotly ===
    fig = go.Figure([
        go.Pie(
            labels=df['tipo_incidente'],  # Etichette delle sezioni: tipo di incidente
            values=df['numero'],         # Valori associati: conteggio per tipo
            hole=0.3                     # "Buca" interna: trasforma la torta in un donut chart
        )
    ])

    # Imposta il layout generale del grafico
    fig.update_layout(
        height=230,                     # Altezza ridotta per adattarsi alla dashboard
        **plotly_layout("")            # Applica uno stile predefinito (template bianco e margini)
    )

    # Converte il grafico Plotly in HTML (in modo da poterlo embeddare nel frontend)
    return pio.to_html(fig, full_html=False)

# === API: Grafico Mercato ===
@blueprint_api.route("/api/grafico_mercato_html")
def grafico_mercato_html():
    # Connessione al database PostgreSQL
    conn = get_connection()

    # Query per ottenere dati di mercato ordinati per tipo minerale e data
    query = """
        SELECT tipo_minerale, data, prezzo
        FROM mercato
        ORDER BY tipo_minerale, data;
    """
    df = pd.read_sql_query(query, conn)  # Caricamento risultati in DataFrame Pandas
    conn.close()  # Chiusura connessione

    # === Analisi e calcolo variazioni per ogni tipo di minerale ===
    info_minerali = {}  # Dizionario per contenere info su ogni minerale

    # Lista dei minerali distinti presenti nella tabella mercato
    minerali = df['tipo_minerale'].unique()

    # Palette di colori di Plotly per rendere le linee visivamente distinte
    palette = qualitative.Plotly
    colori_minerali = {m: palette[i % len(palette)] for i, m in enumerate(minerali)}  # Associa ogni minerale a un colore

    # Ciclo su ciascun tipo di minerale per calcolare metriche di analisi
    for minerale in minerali:
        subset = df[df['tipo_minerale'] == minerale].sort_values('data')  # Sottoinsieme dei dati per quel minerale

        if subset.empty:
            continue  # Se non ci sono dati, salta

        # Calcolo della variazione percentuale del prezzo nel tempo
        prezzo_iniziale = subset['prezzo'].iloc[0]
        prezzo_finale = subset['prezzo'].iloc[-1]
        variazione = ((prezzo_finale - prezzo_iniziale) / prezzo_iniziale) * 100  # Formula Δ% = (P_f - P_i) / P_i * 100

        # Calcolo deviazione standard per valutare la volatilità del prezzo
        std_dev = subset['prezzo'].std()

        # Score di competizione = somma tra volatilità e variazione assoluta
        score = abs(variazione) + std_dev

        # Classificazione della competizione in base allo score
        competizione = (
            "Alta" if score > 20 else
            "Media" if score >= 10 else
            "Bassa"
        )

        # Salva le info nel dizionario
        info_minerali[minerale] = {
            "variazione": round(variazione, 2),     # Δ%
            "competizione": competizione,           # Livello competizione
            "subset": subset                        # Dati grezzi da usare nel grafico
        }

    # === Creazione grafico Plotly ===
    fig = go.Figure()

    # Aggiunta di una traccia per ogni minerale
    for minerale, info in info_minerali.items():
        fig.add_trace(go.Scatter(
            x=info["subset"]['data'],                     # Asse X: data
            y=info["subset"]['prezzo'],                   # Asse Y: prezzo
            mode='lines+markers',                         # Linea con punti
            name=f"{minerale} ({info['competizione']}, Δ{info['variazione']:+.1f}%)",  # Etichetta leggibile
            line=dict(color=colori_minerali.get(minerale, "gray"))  # Colore linea personalizzato
        ))

    # Personalizzazione del layout del grafico
    fig.update_layout(**plotly_layout(
        title="",  # Nessun titolo principale
        xaxis_title="Data",  # Etichetta asse X
        yaxis_title="Prezzo (€)",  # Etichetta asse Y
        legend_title="Minerale (Competizione, Δ%)",  # Titolo della legenda
        xaxis=dict(
            tickformat="%b %Y",  # Formato mese-anno (es. Gen 2024)
            tickangle=45         # Angolo dell’etichetta sull’asse X
        ),
        height=500,  # Altezza del grafico in pixel
        margin=dict(t=60, b=100, l=60, r=20)  # Margini del grafico
    ))

    # Esporta il grafico come HTML da embeddare nel frontend
    return pio.to_html(fig, full_html=False)

# === API: Scarica Report Produzione ===
@blueprint_api.route("/api/miniera/<int:miniera_id>/report")  # Definizione dell’endpoint con parametro dinamico miniera_id
def scarica_report_produzione(miniera_id):
    # Connessione al database PostgreSQL utilizzando la configurazione
    conn = psycopg2.connect(**config())

    # Query SQL per selezionare tutti i record della produzione relativi alla miniera specificata
    query = """
        SELECT p.*
        FROM produzione p
        WHERE p.id_miniera = %s
        ORDER BY p.data;
    """

    # Esecuzione della query, passando miniera_id come parametro
    df = pd.read_sql_query(query, conn, params=(miniera_id,))

    # Chiusura della connessione al database
    conn.close()

    # Se non ci sono dati per la miniera richiesta, restituisce un errore 404
    if df.empty:
        return "Nessun dato disponibile per questa miniera.", 404

    # === Esportazione del DataFrame in un file CSV ===
    # Crea un buffer in memoria (testuale) per scrivere il CSV
    output = io.StringIO()

    # Salva il contenuto del DataFrame in formato CSV, senza includere l’indice Pandas
    df.to_csv(output, index=False)

    # Riporta il puntatore all’inizio del buffer
    output.seek(0)

    # Nome del file da scaricare, basato sull’ID della miniera
    filename = f"report_miniera_{miniera_id}.csv"

    # Restituisce il file CSV come risposta scaricabile
    return send_file(
        io.BytesIO(output.getvalue().encode()),  # Converte il contenuto testuale in byte
        mimetype='text/csv',                     # Specifica il tipo MIME del file
        as_attachment=True,                      # Indica al browser di scaricare il file
        download_name=filename                   # Nome del file che verrà suggerito al download
    )

