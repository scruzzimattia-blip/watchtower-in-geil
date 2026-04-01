# Lighthouse - Projekt-Kontext & Regeln

Diese Datei dient als zentrales Gedaechtnis fuer Gemini CLI und enthaelt alles Wissenswerte fuer die Arbeit an diesem Projekt.

## 1. Projekt-Beschreibung
Lighthouse ist ein hochperformanter, asynchroner Docker-Container-Update-Dienst in Python. Er ueberwacht laufende Container und aktualisiert sie automatisch auf neue Image-Versionen.

## 2. Technischer Stack
- **Sprache:** Python 3.11+
- **Architektur:** Vollstaendig asynchron via `asyncio`.
- **Docker-API:** `aiodocker` (asynchroner Client).
- **Benachrichtigungen:** `apprise` (unterstuetzt >100 Dienste).
- **Monitoring:** Prometheus Metriken via `prometheus_client`.
- **Scheduling:** Unterstuetzt Intervalle und Cron-Ausdruecke via `croniter`.

## 3. Kernfunktionen (Must-Know)
- **Rollback:** Vor jedem Update wird der alte Container in `*_backup` umbenannt. Schlaegt der Healthcheck des neuen fehl, erfolgt ein automatisches Rollback.
- **Lifecycle Hooks:** Nutzt Labels (`com.lighthouse.pre-update`, `com.lighthouse.post-update`) fuer Befehlsausfuehrungen im Container.
- **Abhaengigkeiten:** Beruecksichtigt `depends_on`-Hierarchien bei parallelen Updates.

## 4. Verbindliche Automatisierung
- **Versioning:** Vor jedem Push in `main` oder `develop` muss die Version in `VERSION` erhoeht werden (nur bei funktionalen Aenderungen).
- **Qualitaetssicherung:** Vor jedem Commit MUSS ein erfolgreiches Linting (`ruff check .`) und alle Tests (`pytest tests/`) durchlaufen.
- **Commits:** Erfolgen grundsaetzlich automatisch, sofern nicht anders angewiesen.

## 5. Coding- & Dokumentations-Standards
- **Rechtschreibung:** Ausnahmslos "ss" statt "ß" verwenden (Code, Kommentare, Dokumentation).
- **Testing:** Alle neuen Features muessen durch asynchrone Tests (`pytest-asyncio`) in `tests/` abgesichert werden.
- **Linter:** Strikte Einhaltung der Ruff-Regeln (`pyproject.toml`).
