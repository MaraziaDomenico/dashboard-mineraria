import pandas as pd
import psycopg2
from flask import Blueprint, jsonify
from config import config
import plotly.graph_objs as go
import plotly.io as pio
from plotly.colors import qualitative
from flask import send_file
import io

blueprint_api = Blueprint('api', __name__)

# === Utility ===
def get_connection():
    return psycopg2.connect(**config())

def plotly_layout(title, margin=dict(t=40, l=40, r=40, b=40), **kwargs):
    return dict(
        title=title,
        template='plotly_white',
        margin=margin,
        **kwargs
    )

# === API: Miniere ===
@blueprint_api.route("/api/miniere")
def api_miniere():
    conn = get_connection()
    query = """
        SELECT m.id_miniera, m.nome, m.tipo_minerale, m.stato, m.capacita, m.numero_lavoratori,
               m.latitudine, m.longitudine, a.nome AS nome_azienda
        FROM miniera m
        JOIN azienda a ON m.id_azienda = a.id_azienda;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    return jsonify(df.to_dict(orient='records'))

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
    COEFF = {
        "elettricita": {"q": 0.5, "t": 20, "m": {"Frantumazione": 300, "Sotterranea": 200, "Idraulica": 150, "Cielo aperto": 100}, "div": 1_000_000},
        "acqua": {"q": 2.5, "t": 10, "m": {"Frantumazione": 100, "Sotterranea": 80, "Idraulica": 200, "Cielo aperto": 50}, "div": 1_000_000},
        "co2": {"q": 0.2, "t": 5, "m": {"Frantumazione": 50, "Sotterranea": 40, "Idraulica": 30, "Cielo aperto": 20}, "div": 1_000}
    }

    # Costo operativo in AUD
    COSTO_OPERATIVO_AUD = {
        "q": 24.75,
        "t": 82.5,
        "m": {
            "Frantumazione": 8250,
            "Sotterranea": 6600,
            "Idraulica": 5775,
            "Cielo aperto": 4125
        },
        "div": 1_000_000
    }

    conn = get_connection()
    df = pd.read_sql_query("SELECT quantita, tempo_estrazione, metodo_estrattivo FROM produzione;", conn)
    conn.close()

    def calcola(coeff):
        return (
            df["quantita"] * coeff["q"] +
            df["tempo_estrazione"] * coeff["t"] +
            df["metodo_estrattivo"].map(coeff["m"]).fillna(4000)
        )

    consumo_elettricita = calcola(COEFF["elettricita"])
    consumo_acqua = calcola(COEFF["acqua"])
    emissioni_co2 = calcola(COEFF["co2"])
    costo_operativo_aud = calcola(COSTO_OPERATIVO_AUD)

    return jsonify({
        "consumo_elettricita_gwh": round(consumo_elettricita.sum() / COEFF["elettricita"]["div"], 3),
        "consumo_acqua_ml": round(consumo_acqua.sum() / COEFF["acqua"]["div"], 3),
        "emissioni_co2_kt": round(emissioni_co2.sum() / COEFF["co2"]["div"], 3),
        "costo_operativo_totale": round(costo_operativo_aud.sum() / COSTO_OPERATIVO_AUD["div"], 3)
    })


# === API: Grafico Sicurezza ===
@blueprint_api.route("/api/grafico_sicurezza_html")
def grafico_sicurezza_html():
    conn = get_connection()
    query = """
        SELECT tipo_incidente, COUNT(*) AS numero
        FROM sicurezza
        GROUP BY tipo_incidente
        ORDER BY numero DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    fig = go.Figure([go.Pie(labels=df['tipo_incidente'], values=df['numero'], hole=0.3)])
    fig.update_layout(height=230, **plotly_layout(""))

    return pio.to_html(fig, full_html=False)

# === API: Grafico Mercato ===
@blueprint_api.route("/api/grafico_mercato_html")
def grafico_mercato_html():
    conn = get_connection()
    query = """
        SELECT tipo_minerale, data, prezzo
        FROM mercato
        ORDER BY tipo_minerale, data;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    info_minerali = {}
    minerali = df['tipo_minerale'].unique()
    palette = qualitative.Plotly
    colori_minerali = {m: palette[i % len(palette)] for i, m in enumerate(minerali)}

    for minerale in minerali:
        subset = df[df['tipo_minerale'] == minerale].sort_values('data')
        if subset.empty:
            continue

        prezzo_iniziale = subset['prezzo'].iloc[0]
        prezzo_finale = subset['prezzo'].iloc[-1]
        variazione = ((prezzo_finale - prezzo_iniziale) / prezzo_iniziale) * 100
        std_dev = subset['prezzo'].std()
        score = abs(variazione) + std_dev

        competizione = (
            "Alta" if score > 20 else
            "Media" if score >= 10 else
            "Bassa"
        )

        info_minerali[minerale] = {
            "variazione": round(variazione, 2),
            "competizione": competizione,
            "subset": subset
        }

    fig = go.Figure()
    for minerale, info in info_minerali.items():
        fig.add_trace(go.Scatter(
            x=info["subset"]['data'],
            y=info["subset"]['prezzo'],
            mode='lines+markers',
            name=f"{minerale} ({info['competizione']}, Δ{info['variazione']:+.1f}%)",
            line=dict(color=colori_minerali.get(minerale, "gray"))
        ))

    fig.update_layout(**plotly_layout(
        title="",
        xaxis_title="Data",
        yaxis_title="Prezzo (€)",
        legend_title="Minerale (Competizione, Δ%)",
        xaxis=dict(tickformat="%b %Y", tickangle=45),
        height=500,
        margin=dict(t=60, b=100, l=60, r=20)
    ))

    return pio.to_html(fig, full_html=False)

# === API: Scarica Report Produzione ===
@blueprint_api.route("/api/miniera/<int:miniera_id>/report")
def scarica_report_produzione(miniera_id):
    conn = psycopg2.connect(**config())
    query = """
        SELECT p.*
        FROM produzione p
        WHERE p.id_miniera = %s
        ORDER BY p.data;
    """
    df = pd.read_sql_query(query, conn, params=(miniera_id,))
    conn.close()

    if df.empty:
        return "Nessun dato disponibile per questa miniera.", 404

    # Salva il CSV in memoria
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    filename = f"report_miniera_{miniera_id}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
