# IT-Briefing — Vorlage für Bestandspraxis

Dieses Dokument wird an den bestehenden IT-Dienstleister der Praxis gesendet,
sobald die Fernzugriffsinfrastruktur eingerichtet wurde. Ziel: Transparenz,
Vertrauen, klare Abgrenzung der Verantwortlichkeiten.

**Wann senden:** Unmittelbar nach dem On-Site-Termin, bevor der IT-Dienstleister
die neue Software auf dem Server bemerkt und eigenständig nachfragt.

**An:** IT-Dienstleister (direkt oder über den Arzt)
**CC:** Praxisinhaber / Auftraggeber

Vorlage unten — Platzhalter in `[eckigen Klammern]` ersetzen.

---

<!-- BEGINN VORLAGE — alles unterhalb für den IT-Dienstleister -->

**Liminal Consulting — David Rug**
Karlsruhe | david.rug98@icloud.com
[Datum]

**Betreff: Information über neu installierte Software auf dem Praxisserver [Servername] — [Praxisname]**

Sehr geehrte Damen und Herren,

ich kontaktiere Sie im Auftrag von [Praxisinhaber, z. B. Dr. med. Vorname Nachname],
der/die mich als IT-Berater für die Praxis [Praxisname] beauftragt hat.

Im Rahmen meiner Tätigkeit habe ich am [Datum des On-Site-Termins] auf dem
Praxisserver ([Servername], intern [interne IP]) folgende Änderungen vorgenommen.
Ich informiere Sie hierüber aus Transparenzgründen und stehe für Rückfragen
gerne zur Verfügung.

---

**1. Installierte Software: Cloudflare Tunnel Client (`cloudflared.exe`)**

- **Installationspfad:** `C:\Program Files\cloudflared\cloudflared.exe`
- **Windows-Dienst:** `cloudflared` (Starttyp: Automatisch)
- **Zweck:** Verschlüsselter Fernzugriff ausschließlich für meine Beratungstätigkeit

Der Cloudflare Tunnel Client stellt eine ausgehende, verschlüsselte Verbindung
(TLS 1.3) zum Cloudflare-Netzwerk her. Über diese Verbindung kann ich per
Remote Desktop (RDP) auf den Server zugreifen, um Wartungs- und
Entwicklungsarbeiten im Auftrag der Praxis durchzuführen.

**Sicherheitsrelevante Eigenschaften:**

- Ausschließlich **ausgehende** Verbindungen — keine neuen eingehenden Ports,
  keine Änderungen an der Firewall oder am Router
- Zugang nur nach **Zwei-Faktor-Authentifizierung** (E-Mail-Bestätigung über
  Cloudflare Access — die Plattform derselben Firma, die u. a. den
  Internetzugang vieler Unternehmen absichert)
- Zugang ausschließlich für die E-Mail-Adresse `david.rug98@icloud.com` —
  kein weiterer Nutzer ist autorisiert
- Der Dienst kann jederzeit über `services.msc` gestoppt oder deinstalliert
  werden: `cloudflared.exe service uninstall`

**2. Angelegter Windows-Benutzer: `david-consult`**

- **Typ:** Lokales Konto (kein Domänenkonto)
- **Gruppen:** Administratoren, Remotedesktopbenutzer
- **Zweck:** Dedizierter RDP-Benutzer für meine Beratungssessions —
  getrennt vom Praxiskonto, um Aktivitäten klar zuzuordnen und
  den laufenden Betrieb nicht zu beeinträchtigen

---

**Abgrenzung der Verantwortlichkeiten**

Meine Tätigkeit beschränkt sich auf Beratungs- und Entwicklungsleistungen
im Auftrag der Praxis. Ich greife ausschließlich auf Systeme und Daten zu,
für die mir der Praxisinhaber ausdrücklich Zugang erteilt hat.

Die Verantwortung für die allgemeine IT-Infrastruktur, Datensicherung,
Netzwerksicherheit und den laufenden Betrieb der Praxissysteme verbleibt
selbstverständlich bei Ihnen als beauftragtem IT-Dienstleister.

Bei Fragen oder Bedenken stehe ich Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen,

David Rug
Liminal Consulting
david.rug98@icloud.com

*CC: [Praxisinhaber]*

<!-- ENDE VORLAGE -->

---

## Hinweise zur Verwendung

**Ton:** Formal, sachlich, nicht defensiv. Der IT-Dienstleister soll das Gefühl
haben, informiert zu werden — nicht, konfrontiert zu werden.

**Timing:** Senden bevor er die Software selbst entdeckt. Wer zuerst informiert,
wirkt professionell. Wer reaktiv erklärt, wirkt verdächtig.

**Anpassungen je nach Typ:**

- **Typ A (Territorial):** Praxisinhaber als CC sichtbar machen — zeigt, dass
  der Arzt die Maßnahme kennt und gebilligt hat. Schützt dich.
- **Typ B (Pragmatisch):** Dokument reicht so. Kein Follow-up nötig.
- **Typ C (Kollaborativ):** Kurze persönliche Zeile ergänzen, z. B. ob er
  Fragen zur Architektur hat — öffnet Gesprächsraum.

**Für jede neue Praxis:** Dieses Template mit den spezifischen Werten befüllen
und als PDF senden (nicht als .md). Dateiname: `IT-Information_[Praxisname]_[Datum].pdf`
