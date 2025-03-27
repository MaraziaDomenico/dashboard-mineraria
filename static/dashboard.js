window.addEventListener("DOMContentLoaded", () => {
    // === MAPPA ===
    const map = L.map('map', {
        minZoom: 4,
        maxZoom: 10,
        zoomSnap: 0.5,
        maxBounds: [
            [-45, 110],
            [-10, 135]
        ],
        maxBoundsViscosity: 1.0,
        worldCopyJump: false
    }).setView([-27.0, 122.0], 4.5);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles © Esri',
        noWrap: false
    }).addTo(map);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
        attribution: '',
        noWrap: false,
        opacity: 0.9
    }).addTo(map);

    const customIcon = L.divIcon({
        className: 'custom-icon',
        iconSize: [18, 18]
    });

    function caricaMiniere() {
        fetch('/api/miniere')
            .then(response => response.json())
            .then(data => {
                data.forEach(miniera => {
                    const marker = L.marker([miniera.latitudine, miniera.longitudine], { icon: customIcon }).addTo(map);
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
                    marker.bindPopup(popupContent);
                });
            })
            .catch(error => console.error("Errore nel caricamento delle miniere:", error));
    }

    // === DASHBOARD ===
    function caricaConsumiGenerali() {
        fetch("/api/consumi_generali")
            .then(res => res.json())
            .then(dati => {
                document.getElementById("valore_elettricita").innerText = dati.consumo_elettricita_gwh;
                document.getElementById("valore_acqua").innerText = dati.consumo_acqua_ml;
                document.getElementById("valore_co2").innerText = dati.emissioni_co2_kt;
                document.getElementById("valore_costo_operativo").innerText = dati.costo_operativo_totale;
            })
            .catch(err => console.error("Errore caricamento consumi:", err));
    }

    function caricaGraficoConScript(endpoint, contenitoreGeneraleId, contenitoreInternoId) {
        const contenitore = document.getElementById(contenitoreInternoId);
        const blocco = document.getElementById(contenitoreGeneraleId);
        if (!contenitore || !blocco) return;

        fetch(endpoint)
            .then(response => response.text())
            .then(html => {
                contenitore.innerHTML = html;

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

                window.dispatchEvent(new Event('resize'));
            })
            .catch(err => {
                contenitore.innerHTML = "<p style='color:red;'>Errore nel caricamento del grafico.</p>";
                console.error(`Errore caricamento da ${endpoint}:`, err);
            });
    }

    function aggiornaDashboard() {
        caricaMiniere();
        caricaConsumiGenerali();
        caricaGraficoConScript("/api/grafico_mercato_html", "grafico_mercato", "grafico_mercato_container");
        caricaGraficoConScript("/api/grafico_produzione_html", "grafico_produzione", "grafico_produzione_container");
        caricaGraficoConScript("/api/grafico_sicurezza_html", "grafico_sicurezza", "grafico_sicurezza_container");
    }

    aggiornaDashboard();

    setInterval(() => {
        caricaConsumiGenerali();
        caricaGraficoConScript("/api/grafico_mercato_html", "grafico_mercato", "grafico_mercato_container");
        caricaGraficoConScript("/api/grafico_produzione_html", "grafico_produzione", "grafico_produzione_container");
        caricaGraficoConScript("/api/grafico_sicurezza_html", "grafico_sicurezza", "grafico_sicurezza_container");
    }, 30000);
});
