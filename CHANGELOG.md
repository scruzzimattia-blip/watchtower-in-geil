# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei festgehalten.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/) und dieses Projekt hält sich an [Semantic Versioning](https://semver.org/lang/de/).

## [0.6.1] - 2026-04-01
### Hinzugefügt
- `CONTRIBUTING.md` für Mitwirkende.
- Issue-Templates für Bug Reports und Feature Requests.
- MIT-Lizenz hinzugefügt.
- `CHANGELOG.md` und `SECURITY.md` erstellt.
- Pull Request Template integriert.

## [0.6.0] - 2026-04-01
### Hinzugefügt (Watchtower-Parität)
- **Lifecycle Hooks**: Unterstützung für `pre-update` und `post-update` Befehle.
- **Prometheus Metriken**: Integrierter Server für Monitoring.
- **Apprise-Integration**: Unterstützung für über 100 Benachrichtigungsdienste.
- **Abhängigkeits-Management**: Berücksichtigung von `depends_on`.
- **Remote Docker Support**: Unterstützung für `DOCKER_HOST`.
- **Container-Filter**: Whitelist/Blacklist via Namen.

## [0.5.0] - 2026-04-01
### Hinzugefügt
- Komplette Umstellung auf **AsyncIO** und `aiodocker`.
- **Robuster Rollback**: Automatisches Wiederherstellen bei fehlgeschlagenen Updates.
- **Cron-Support**: Planung via Cron-Ausdrücken.
- Zusammenfassende Berichte für Benachrichtigungen.

## [0.1.0] - 2026-03-31
### Hinzugefügt
- Initiale Version mit Basis-Docker-Update-Logik.
- Label-basierte Container-Erkennung.
- Einfache Webhook-Benachrichtigungen.
