---
name: Tumorscout / extrax — direkter MO-DB-Read als etabliertes Pattern
description: Marktbestätigung dass direkter read-only MariaDB-Zugriff auf Medical Office ein etabliertes, ToS-konformes, vom Markt akzeptiertes Pattern ist
type: reference
originSessionId: f5bdb875-89ff-475c-b6fa-6c94427cf63b
---
# Tumorscout / axaris extrax als Architektur-Präzedenzfall

**Tumorscout GmbH** (Berlin, gegr. 2021) ist eine Web-Plattform für Krebsregister-Meldungen. Der Daten-Extraktions-Layer ist **axaris extrax** (axaris software & systeme GmbH, Ulm), ein Plugin das **direkt die PVS-MariaDB read-only liest, täglich automatisch**.

**Medical Office (INDAMED) ist explizit in der extrax-PVS-Liste** unterstützt. Mechanismus = direkter DB-Read, **nicht xDT, nicht KBV-Schnittstelle**.

**Geschäftsmodell**: lokales Plugin liest PVS, Web-UI orchestriert, Daten verbleiben lokal beim Arzt.

**Warum das relevant ist für unsere Arbeit:**
- Marktbestätigung dass direkter MO-DB-Read ToS-konform und etabliert ist — wir müssen Sunday's Schema-Dump nicht rechtfertigen, sondern können auf den axaris-Präzedenzfall verweisen
- Tumorscout's Geschäftsmodell ist exakt unseres, nur in einer extrem spezifischen Niche (Krebsregister-Meldungen). Wir wollen breiter
- d-uo Tumordokumentations-System ist im Urologie-Segment der direkteste Konkurrent von Tumorscout — kostenlos für Berufsverbands-Mitglieder. **Bei Papa abklären ob er d-uo-Mitglied ist**, um zu wissen ob Krebsregister-Meldung als eigener Process Sinn macht oder schon abgedeckt ist.

**Sources** (verifiziert 2026-04-26):
- https://tumorscout.de/
- https://www.axaris.de/index.php/extrax/
- https://www.axaris.de/wp-content/uploads/success_story_extrax_tumorscout.pdf
- https://d-uo.de/tumordokumentations-system/
