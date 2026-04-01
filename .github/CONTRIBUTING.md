# Mitwirken an Lighthouse

Herzlich willkommen! Wir freuen uns sehr, dass du Interesse daran hast, Lighthouse zu verbessern. Als Open-Source-Projekt lebt Lighthouse von der Gemeinschaft.

Bitte nimm dir einen Moment Zeit, um diese Richtlinien zu lesen, damit der Prozess fuer alle Beteiligten reibungslos verlaeuft.

## Inhaltsverzeichnis
- [Code of Conduct](#code-of-conduct)
- [Fehler melden (Bug Reports)](#fehler-melden)
- [Funktionen vorschlagen (Feature Requests)](#funktionen-vorschlagen)
- [Lokale Entwicklung (Local Setup)](#lokale-entwicklung)
- [Pull Request Richtlinien](#pull-request-richtlinien)

## Code of Conduct
Durch die Teilnahme an diesem Projekt erklaerst du dich damit einverstanden, die Community-Standards zu wahren und respektvoll mit anderen umzugehen.

## Fehler melden
Wenn du einen Fehler findest, nutze bitte unsere [Bug Report Vorlage](https://github.com/scruzzimattia-blip/Lighthouse/issues/new?template=bug_report.yml). Achte darauf:
- Den Fehler mit einer klaren Ueberschrift zu beschreiben.
- Die Schritte zur Reproduktion genau aufzufuehren.
- Deine Docker-Version und dein Betriebssystem zu nennen.

## Funktionen vorschlagen
Wir sind immer offen fuer neue Ideen! Nutze fuer Vorschlaege die [Feature Request Vorlage](https://github.com/scruzzimattia-blip/Lighthouse/issues/new?template=feature_request.yml). Beschreibe bitte den Anwendungsfall und warum diese Funktion fuer Lighthouse wertvoll waere.

## Lokale Entwicklung
Um lokal am Projekt zu arbeiten, befolge bitte diese Schritte:

1. **Repository forken und klonen:**
   ```bash
   git clone https://github.com/DEIN_USER/Lighthouse.git
   cd Lighthouse
   ```

2. **Virtuelle Umgebung erstellen:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   ```

3. **Abhaengigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Linting und Tests:**
   Bevor du Code einreichst, muessen der Linter und die Tests erfolgreich durchlaufen:
   ```bash
   ruff check .
   pytest tests/
   ```

## Pull Request Richtlinien
- Erstelle fuer jede Aenderung einen eigenen Branch (z. B. `feat/meine-funktion` oder `fix/behebung-fehler`).
- Achte auf aussagekraeftige Commit-Nachrichten.
- Dokumentiere neue Funktionen in der `README.md`.
- **Wichtig:** Verwende im gesamten Projekt ausschliesslich "ss" statt "ß" in Kommentaren und Dokumentationen.
- Stelle sicher, dass die CI (GitHub Actions) fuer deinen PR erfolgreich ist.

Vielen Dank fuer deine Unterstuetzung!
