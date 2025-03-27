# Usa un'immagine ufficiale Python come base
FROM python:3.11-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia i file requirements prima (per ottimizzare la cache)
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il contenuto della tua app
COPY . .

# Espone la porta Flask
EXPOSE 5000

# Comando per avviare l'app
CMD ["python", "main.py"]
