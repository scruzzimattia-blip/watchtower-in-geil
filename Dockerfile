# Basis-Image fuer Python.
FROM python:3.11-slim

# Arbeitsverzeichnis festlegen.
WORKDIR /app

# Abhaengigkeiten kopieren und installieren.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode und Version kopieren.
COPY app/ app/
COPY VERSION .

# Umgebungsvariable fuer Python (Pufferung deaktivieren fuer Docker-Logs).
ENV PYTHONUNBUFFERED=1

# Einstiegspunkt definieren.
CMD ["python", "-m", "app.main"]
