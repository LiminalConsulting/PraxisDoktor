# Transcript 2026-03-10 — Automation-Relevant Insights

> MFA-perspective from the first-contact visit (Frau Osmani primary, other MFAs walking by). Only items not already covered by [`transcript_2026-04-26.md`](./transcript_2026-04-26.md) + [`processes_observed.md`](./processes_observed.md) grounding are listed here. Raw transcript preserved at [`transcript_2026-03-10.md`](./transcript_2026-03-10.md).

---

## 1. Gabi: bidirectional Termin-Bug

Patients book a Termin with Gabi (MediVoice) but get **no confirmation** — SMS-Funktion was not booked, E-Mail-Bestätigung never goes out. Two failure modes observed: (a) Patient wartet auf Bestätigung, kommt nie → Slot bleibt ungenutzt; (b) Patient denkt, Termin sei nicht durch, ruft an, bucht doppelt → Doppelbuchung.

**Fix:** auto-email confirmation when `patient.email` is in Stammdaten. Maps to existing `termin_uebersicht` co_pilot.

---

## 2. Gabi: name-misrecognition without phone-fallback

Gabi mishears patient name → Eintrag landet ohne zuordenbare Patientennummer. MO's Patientensuche supports Name / Vorname / Patientennummer / Geburtsdatum — **Telefonnummer is not a search field**. So even if Gabi captured the phone correctly, MFA can't find the existing Patient that way.

**Fixes (complementary):**
- (a) Re-transcribe Gabi-Audio with practice-Patientenstamm als Vocab-Liste (faster-whisper / whisper.cpp local) → drastically reduces Namens-Fehlerrate. **Open question:** speichert MediVoice das Audio noch nach dem Live-Transkript?
- (b) Add phone-number lookup path in our Patientensuche-Layer (independent of MO's UI limitation).

---

## 3. Stornierte Termine bleiben sichtbar im Kalender

Wenn Patient storniert, verschwindet der Eintrag nicht aus Papa's Kalender-View. Frau Osmani vermutet, dass dadurch am Nachmittag Doppelbuchungen entstehen ("ich glaube, dass dadurch der Termin doppelt gebucht wird").

**Fix:** entweder farblich klar unterscheidbar machen (z.B. ausgegraut + durchgestrichen) oder per Default ausblenden, mit Toggle. Trivial im `termin_uebersicht`-View.

---

## 4. Termin-Service-Stelle (TSS) als dritter Termin-Eingangsstrom

Neben Telefon/Online-Formular und Gabi gibt es einen KV-mandated Pfad: Hausarzt gibt Patient einen Code → Patient ruft die TSS an → TSS bucht in von Papa freigegebene Slots → **MFA bekommt eine E-Mail** → muss den Termin **manuell** in den Kalender eintragen, weil die TSS-Software die Eintragung nicht selbst pusht.

**Implication:** `termin_uebersicht` braucht eine dritte Ingestion-Lane (TSS-E-Mail-Parser → strukturierter Booking-Request, von der MFA per 1-Click in den Kalender bestätigt).

---

## 5. Drucker-Auswahl als Hauptzeitfresser

Jedes Etikett / Laufzettel / Rezept / Privatschein / Kostenvoranschlag erfordert manuelles Aussuchen des richtigen Druckers. Mehrfach pro Patient, viele Patienten pro Tag. Frau Osmani: "macht mich irre."

**Fix:** Per-Dokumenttyp Drucker-Mapping (Etikett → Etikettendrucker, Laufzettel → Hauptdrucker Empfang, etc.). Kann entweder als MO-Einstellung gemacht werden (falls möglich) oder als Mini-Wrapper-App über die Patientenakte ("Drucken"-Button kennt schon Dokumenttyp + Patient + Zieldrucker). Klassische "ein Klick zu viel"-Automatisierung — kleines Leverage, sehr hohe Frequenz.

---

## 6. Briefe-Eingang-Kategorisierung beim Scannen

Jeder eingescannte Brief muss von der MFA manuell in eine Beschreibungs-Kategorie eingetragen werden. Frau Osmani: "das muss ich immer selber hängen, ich glaube das kann man automatisch machen, weil es immer was anderes ist."

**Fix:** Auto-Classify aus dem Dokumenten-Inhalt (OCR + LLM-Kategorisierung) → vorausgefüllter Kategorie-Vorschlag, MFA bestätigt per Klick. Kategorien aus dem realen Korpus inferierbar sobald wir DB-Read auf den bestehenden Bestand haben (Krankenhaus-Bericht / Pathologie-Befund / Labor / Konsiliarbrief / etc.).

---

## 7. Zugangsdaten von Krankenhäusern als wiederkehrendes E-Mail-To-Do-Pattern

Konkretes Beispiel: Krankenhaus schickt Röntgen-Zugangsdaten per E-Mail → MFA muss daraus eine To-Do für den behandelnden Arzt erzeugen, damit der die Bilder einsehen kann. Wiederkehrend, strukturierbar.

**Fix:** E-Mail-Triage erkennt "Zugangsdaten von externer Einrichtung" als eigene Kategorie → erzeugt strukturierten To-Do-Eintrag (Patient-Bezug + Login-Felder + Zielsystem-URL) in der richtigen Arzt-To-Do-Liste. Maps in das geplante `aufgaben_persoenlich` / `aufgaben_team` Modell.

---

## 8. Infoskop-Funktion teilweise kaputt

Früher konnte über Infoskop ein breites Set an Dokumenten verschickt werden (Kostenvoranschläge, OP-Einwilligungen, Anforderungs-Formulare); jetzt sind nur noch ~5 Templates verknüpft. Frau Osmani: "seitdem der Doktor die Computer hat, das steht hier gar nicht mehr... muss neu aufgesetzt werden."

**Implication:** verstärkt das bestehende strategische Framing ("Infoskop = highest-leverage replacement target" aus `papa_dad_practice_context.md`) mit konkretem MFA-side Pain-Point. Wenn die existierende Infoskop-Anbindung ohnehin schon halb kaputt ist, ist die Hürde für den Replacement niedriger.
