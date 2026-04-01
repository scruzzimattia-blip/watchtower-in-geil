# Lighthouse

Ein schlanker Docker-Container-Update-Dienst in Python, der laufende Instanzen automatisch auf neue Image-Versionen prueft und diese aktualisiert.

## Funktionen
- Nutzt die asynchrone Docker-API (aiodocker) fuer hohe Performance.
- Parallele Pruefung von Containern via AsyncIO.
- Automatischer Rollback: Falls ein Update fehlschlaegt (Healthcheck), wird die vorherige Version automatisch wiederhergestellt.
- Lifecycle Hooks: Befehle vor (`pre-update`) und nach (`post-update`) dem Update im Container ausfuehren.
- Docker Compose Integration: Behaelt Labels, Netzwerke und Konfigurationen bei.
- Abhaengigkeits-Management: Beruecksichtigt `depends_on` bei Updates.
- Flexibles Scheduling: Unterstuetzt sowohl Intervalle als auch Cron-Ausdruecke.
- Monitoring: Integrierter Prometheus Metrik-Server.
- Umfangreiche Benachrichtigungen: Unterstuetzung von ueber 100 Diensten (Telegram, Email, Discord, etc.) via Apprise.
- Remote Docker Support: Verbindung zu entfernten Docker-Hosts via TCP/TLS.
- Filter: Container gezielt via Namen ein- oder ausschliessen.
- Dry-Run Modus fuer Simulationen.

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
- `CRON_SCHEDULE`: Cron-Ausdruck fuer geplante Pruefungen (z. B. `0 3 * * *`). Ueberschreibt `POLL_INTERVAL`.
- `NOTIFICATION_URLS`: Kommagetrennte Liste von Apprise-URLs.
  - Discord: `discord://webhook_id/webhook_token`
  - Telegram: `tgram://bot_token/chat_id`
  - Gotify: `gotify://hostname/token`
  - Email: `mailto://user:pass@gmail.com`
- `METRICS_PORT`: Port fuer den Prometheus-Server (Standard: 8080).

### Beispiel: Vollstaendige docker-compose.yml
```yaml
services:
  lighthouse:
    image: ghcr.io/scruzzimattia-blip/lighthouse:latest
    container_name: lighthouse
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - CRON_SCHEDULE=0 3 * * *
      - NOTIFICATION_URLS=discord://123/abc,tgram://bot:tok/456
      - METRICS_PORT=8080
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080" # Prometheus Endpunkt
```
- `INCLUDE_CONTAINERS` / `EXCLUDE_CONTAINERS`: Kommagetrennte Liste von Containernamen.
- `DOCKER_HOST`: URL zum Docker-Socket/Host (z. B. `tcp://192.168.1.10:2375`).
- `WATCH_LABEL`: Label, nach dem gesucht werden soll (Standard: `com.lighthouse.enable`).
- `WEBHOOK_URL`: Veraltet (Nutzen Sie `NOTIFICATION_URLS`).
- `DRY_RUN`: Falls `true`, werden nur Updates simuliert.
- `MAX_WORKERS`: Anzahl paralleler Pruefungen (Standard: 4).
- `SKIP_PULL_ERROR`: Falls `true`, werden Fehler beim Pull ignoriert.

### Lifecycle Hooks
Sie koennen Befehle definieren, die vor oder nach einem Update ausgefuehrt werden:
- `com.lighthouse.pre-update`: Befehl vor dem Stoppen (z. B. `mysql -u root -p dump`).
- `com.lighthouse.post-update`: Befehl nach dem Starten (z. B. `npm run migrate`).

## 🤝 Mitwirken (Contributing)

Lighthouse ist ein Community-Projekt! Ob du Fehler behebst, neue Funktionen implementierst oder die Dokumentation verbesserst – jede Hilfe ist willkommen. 

**Warum mitwirken?**
- Verbessere deine Python- und Docker-Kenntnisse.
- Gestalte ein Tool mit, das von vielen Entwicklern genutzt wird.
- Werde Teil einer offenen und hilfsbereiten Community.

Schau in unseren [Contributing Guide](.github/CONTRIBUTING.md), um zu erfahren, wie du deine erste Entwicklungsumgebung aufsetzt und deinen ersten Pull Request einreichst. Wir freuen uns auf deine Ideen!

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

## Lizenz
Dieses Projekt ist unter der MIT-Lizenz lizenziert. Weitere Informationen findest du in der Datei [LICENSE](LICENSE).
