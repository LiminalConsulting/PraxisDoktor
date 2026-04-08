# PraxisDoktor — Patientenaufnahme-Assistent

Automatisierte Patientenaufnahme für die urologische Praxis Dr. Rug.

Nimmt das Erstgespräch auf, transkribiert es mit Whisper (lokal, Deutsch), liest den Anamnesebogen per OCR ein und extrahiert mit einem lokalen LLM (Ollama) die Patientenstammdaten — bereit zum Einfügen in MediOffice.

## Features

- **Aufnahme im Browser** — kein extra Mikrofon-Setup
- **Whisper (faster-whisper)** — Deutsch, urologisches Vokabular, läuft auf CPU
- **OCR** — Anamnesebogen per Drag & Drop einlesen (easyocr, kein Tesseract nötig)
- **Lokales LLM** — Ollama extrahiert strukturierte Felder, kein Cloud-Zugriff
- **Kopierschaltflächen** — ein Klick je Feld, dann in MediOffice einfügen
- **Sitzungsverlauf** — SQLite, alle Maschinen im LAN sehen dieselben Daten
- **Vokabular-Editor** — Begriffe im Browser hinzufügen/entfernen

## Schnellstart (Entwicklung)

```bash
# Abhängigkeiten installieren (uv erforderlich)
uv sync

# Ollama-Modell laden (einmalig)
ollama pull llama3.1:8b

# Server starten
uv run python main.py
# → http://localhost:8080
```

## Produktion (Windows)

Siehe `ANLEITUNG.txt` im Release-ZIP.

Release erstellen:
```bash
git tag v1.0.0
git push origin v1.0.0
```
GitHub Actions baut automatisch `PraxisDoktor-v1.0.0.zip` mit EXE + Ollama-Installer.

## Architektur

```
main.py          FastAPI — API-Endpunkte, Hintergrundaufgaben, SSE
transcribe.py    faster-whisper (medium, CPU, int8)
ocr.py           easyocr (Deutsch, CPU)
llm.py           Ollama-Client, Extraktions-Prompt
db.py            SQLite — Sitzungen + Vokabular
vocab.py         Vokabular-Verwaltung
static/          HTML/CSS/JS Frontend
```

## Datenschutz

- Alle Verarbeitung erfolgt lokal (kein Cloud-Zugriff)
- Audiodateien bleiben auf dem Server
- SQLite-Datenbank liegt neben der EXE
