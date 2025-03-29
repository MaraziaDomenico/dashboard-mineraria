// Quando il DOM è completamente caricato, esegue la logica
window.addEventListener("DOMContentLoaded", () => {
    // === MAPPA ===
    // Inizializza la mappa Leaflet con confini, zoom e vista iniziale
    const map = L.map('map', {
        minZoom: 4,
        maxZoom: 10,
        zoomSnap: 0.5,
        maxBounds: [ [-45, 110], [-10, 135] ], // Limiti geografici Australia
        maxBoundsViscosity: 1.0,
        worldCopyJump: false
    }).setView([-27.0, 122.0], 4.5); // Centro geografico iniziale

    // Aggiunge il layer satellitare (Esri) alla mappa
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles © Esri',
        noWrap: false
    }).addTo(map);

    // Aggiunge il layer con i confini amministrativi
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
        attribution: '',
        noWrap: false,
        opacity: 0.9
    }).addTo(map);

    // Definizione di un'icona personalizzata per i marker delle miniere
    const customIcon = L.divIcon({
        className: 'custom-icon',
        iconSize: [18, 18]
    });

    // === Caricamento marker miniere da API ===
    function caricaMiniere() {
        fetch('/api/miniere') // Richiesta all’API per ottenere la lista delle miniere
            .then(response => response.json())
            .then(data => {
                data.forEach(miniera => {
                    // Crea un marker sulla mappa con l'icona personalizzata
                    const marker = L.marker([miniera.latitudine, miniera.longitudine], { icon: customIcon }).addTo(map);

                    // Contenuto del popup informativo associato al marker
                    const popupContent = `
                        <div><strong>${miniera.nome}</strong></div>
                        <div>Minerale: ${miniera.tipo_minerale}</div>
                        <div>Stato: ${miniera.stato}</div>
                        <div>Capacità: ${miniera.capacita} ton</div>
                        <div>Lavoratori: ${miniera.numero_lavoratori}</div>
                        <div>Azienda: ${miniera.nome_azienda}</div>
                        <div style="margin-top:8px;">
                            <a href="/api/miniera/${miniera.id_miniera}/report" target="_blank" style="color:#2a93d5; text-decoration: underline;">
                                Scarica report produzione
                            </a>
                        </div>
                    `;
                    marker.bindPopup(popupContent); // Associa il popup al marker
                });
            })
            .catch(error => console.error("Errore nel caricamento delle miniere:", error));
    }

    // === Caricamento dati consumo / impatto ambientale ===
    function caricaConsumiGenerali() {
        fetch("/api/consumi_generali")
            .then(res => res.json())
            .then(dati => {
                // Inserisce i valori nei rispettivi span HTML
                document.getElementById("valore_elettricita").innerText = dati.consumo_elettricita_gwh;
                document.getElementById("valore_acqua").innerText = dati.consumo_acqua_ml;
                document.getElementById("valore_co2").innerText = dati.emissioni_co2_kt;
                document.getElementById("valore_costo_operativo").innerText = dati.costo_operativo_totale;
            })
            .catch(err => console.error("Errore caricamento consumi:", err));
    }

    // === Caricamento generico di un grafico Plotly ===
    function caricaGraficoConScript(endpoint, contenitoreGeneraleId, contenitoreInternoId) {
        const contenitore = document.getElementById(contenitoreInternoId);     // Div che conterrà il grafico
        const blocco = document.getElementById(contenitoreGeneraleId);         // Blocco grafico intero (es. grafico_produzione)
        if (!contenitore || !blocco) return;

        fetch(endpoint)  // Recupera il grafico come HTML dall’endpoint Flask
            .then(response => response.text())
            .then(html => {
                contenitore.innerHTML = html;  // Inserisce il grafico nel DOM

                // Re-inizializza eventuali script presenti nel grafico HTML
                const scripts = contenitore.querySelectorAll("script");
                scripts.forEach(oldScript => {
                    const newScript = document.createElement("script");
                    if (oldScript.src) {
                        newScript.src = oldScript.src;
                    } else {
                        newScript.textContent = oldScript.textContent;
                    }
                    document.body.appendChild(newScript);
                    oldScript.remove();
                });

                // Forza il resize per garantire il corretto rendering del grafico
                window.dispatchEvent(new Event('resize'));
            })
            .catch(err => {
                // In caso di errore, visualizza un messaggio nel contenitore
                contenitore.innerHTML = "<p style='color:red;'>Errore nel caricamento del grafico.</p>";
                console.error(`Errore caricamento da ${endpoint}:`, err);
            });
    }

    // === Funzione per aggiornare l’intera dashboard ===
    function aggiornaDashboard() {
        caricaMiniere();
        caricaConsumiGenerali();
        caricaGraficoConScript("/api/grafico_mercato_html", "grafico_mercato", "grafico_mercato_container");
        caricaGraficoConScript("/api/grafico_produzione_html", "grafico_produzione", "grafico_produzione_container");
        caricaGraficoConScript("/api/grafico_sicurezza_html", "grafico_sicurezza", "grafico_sicurezza_container");
    }

    // === Caricamento iniziale all’avvio della pagina ===
    aggiornaDashboard();

    // === Aggiornamento periodico ogni 30 secondi ===
    setInterval(() => {
        caricaConsumiGenerali();  // Solo i dati dinamici vengono aggiornati
        caricaGraficoConScript("/api/grafico_mercato_html", "grafico_mercato", "grafico_mercato_container");
        caricaGraficoConScript("/api/grafico_produzione_html", "grafico_produzione", "grafico_produzione_container");
        caricaGraficoConScript("/api/grafico_sicurezza_html", "grafico_sicurezza", "grafico_sicurezza_container");
    }, 30000); // 30.000 ms = 30 sec
});
