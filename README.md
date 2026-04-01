# Lighthouse

Ein schlanker Docker-Container-Update-Dienst in Python, der laufende Instanzen automatisch auf neue Image-Versionen prueft und diese aktualisiert.

## Funktionen
- Nutzt die asynchrone Docker-API (aiodocker) fuer hohe Performance.
- Parallele Pruefung von Containern via AsyncIO.
- Automatischer Rollback: Falls ein Update fehlschlaegt (Healthcheck), wird die vorherige Version automatisch wiederhergestellt.
- Docker Compose Integration: Behaelt Labels, Netzwerke und Konfigurationen bei.
- Flexibles Scheduling: Unterstuetzt sowohl Intervalle als auch Cron-Ausdruecke.
- Zusammenfassende Benachrichtigungen via Discord/Slack Webhooks.
- Dry-Run Modus fuer Simulationen.
- Behaelt wichtige Konfigurationen wie Umgebungsvariablen, Ports und Volumes bei.
- Vollstaendige CI/CD-Pipeline via GitHub Actions (GHCR).

## Installation & Betrieb (Docker)

Sie koennen das Image direkt aus der GitHub Container Registry ziehen:

```bash
docker pull ghcr.io/scruzzimattia-blip/lighthouse:latest
```

Um Lighthouse als Container zu starten, muss der Docker-Socket gemountet werden:

```bash
docker run -d \
  --name lighthouse \
  -v /var/run/docker.sock:/var/run/docker.sock \
  ghcr.io/scruzzimattia-blip/lighthouse:latest
```

### Betrieb mit Docker Compose

Sie koennen Lighthouse auch ganz einfach mit Docker Compose starten:

```yaml
# docker-compose.yml
services:
  lighthouse:
    image: ghcr.io/scruzzimattia-blip/lighthouse:latest
    container_name: lighthouse
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - POLL_INTERVAL=300
      - WATCH_LABEL=com.lighthouse.enable
```

Starten Sie den Dienst anschliessend mit:
```bash
docker compose up -d
```

### Konfiguration
Das Tool kann ueber Umgebungsvariablen konfiguriert werden:
- `POLL_INTERVAL`: Zeitabstand zwischen den Pruefungen in Sekunden (Standard: 300).
- `CRON_SCHEDULE`: Cron-Ausdruck fuer geplante Pruefungen (z. B. `0 3 * * *` fuer 3 Uhr morgens). Ueberschreibt `POLL_INTERVAL`.
- `WATCH_LABEL`: Label, nach dem gesucht werden soll (Standard: `com.lighthouse.enable`).
- `WEBHOOK_URL`: URL fuer Benachrichtigungen (Discord/Slack).
- `DRY_RUN`: Falls `true`, werden nur Updates simuliert.
- `MAX_WORKERS`: Anzahl paralleler Pruefungen (Standard: 4).
- `SKIP_PULL_ERROR`: Falls `true`, werden Fehler beim Pull eines Images ignoriert und der Scan fortgesetzt.

### Container fuer die Ueberwachung markieren
Damit ein Container aktualisiert wird, muss er mit dem entsprechenden Label gestartet werden:

```bash
docker run -d \
  --name mein-app-container \
  --label com.lighthouse.enable=true \
  nginx:latest
```

## Lokale Entwicklung
1. Repository klonen.
2. Abhaengigkeiten installieren: `pip install -r requirements.txt`.
3. Starten: `python -m app.main`.

## Wichtige Hinweise
- Im gesamten Projekt wird "ss" statt "ß" verwendet.
- Achten Sie darauf, dass der Benutzer, der das Tool ausfuehrt, Zugriff auf `/var/run/docker.sock` hat.
