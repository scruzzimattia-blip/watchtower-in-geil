# Watchtower-in-geil

Ein schlanker Watchtower-Klon in Python, der Docker-Container automatisch auf neue Image-Versionen prueft und diese aktualisiert.

## Funktionen
- Nutzt die Docker-Socket-Schnittstelle.
- Automatische Erkennung von zu ueberwachenden Containern via Labels.
- Pullt die neusten Images und startet Container bei Bedarf neu.
- Behaelt wichtige Konfigurationen wie Umgebungsvariablen, Ports und Volumes bei.
- Vollstaendige CI/CD-Pipeline via GitHub Actions (GHCR).

## Installation & Betrieb (Docker)

Sie koennen das Image direkt aus der GitHub Container Registry ziehen:

```bash
docker pull ghcr.io/scruzzimattia-blip/watchtower-in-geil:latest
```

Um den Watchtower-Klon als Container zu starten, muss der Docker-Socket gemountet werden:

```bash
docker run -d \
  --name watchtower-in-geil \
  -v /var/run/docker.sock:/var/run/docker.sock \
  ghcr.io/scruzzimattia-blip/watchtower-in-geil:latest
```

### Konfiguration
Das Tool kann ueber Umgebungsvariablen konfiguriert werden:
- `POLL_INTERVAL`: Zeitabstand zwischen den Pruefungen in Sekunden (Standard: 300).
- `WATCH_LABEL`: Label, nach dem gesucht werden soll (Standard: `com.watchtower.enable`).

### Betrieb mit Docker Compose

Sie koennen den Watchtower-Klon auch ganz einfach mit Docker Compose starten:

```yaml
# docker-compose.yml
services:
  watchtower-in-geil:
    image: ghcr.io/scruzzimattia-blip/watchtower-in-geil:latest
    container_name: watchtower-in-geil
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - POLL_INTERVAL=300
```

Starten Sie den Dienst anschliessend mit:
```bash
docker compose up -d
```
Damit ein Container aktualisiert wird, muss er mit dem entsprechenden Label gestartet werden:

```bash
docker run -d \
  --name mein-app-container \
  --label com.watchtower.enable=true \
  nginx:latest
```

## Lokale Entwicklung
1. Repository klonen.
2. Abhaengigkeiten installieren: `pip install -r requirements.txt`.
3. Starten: `python -m app.main`.

## Wichtige Hinweise
- Im gesamten Projekt wird "ss" statt "ß" verwendet.
- Achten Sie darauf, dass der Benutzer, der das Tool ausfuehrt, Zugriff auf `/var/run/docker.sock` hat.
