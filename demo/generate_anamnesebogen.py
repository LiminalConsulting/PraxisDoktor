"""Generate a realistic filled-out German urology Anamnesebogen PDF for demo purposes."""
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=20)

# --- Header ---
pdf.set_font("Helvetica", "B", 14)
pdf.cell(0, 10, "Urologische Praxis Dr. med. Michael Rug", ln=True, align="C")
pdf.set_font("Helvetica", "", 9)
pdf.cell(0, 5, "Musterstr. 12  |  80331 Muenchen  |  Tel: 089 / 123 456 78", ln=True, align="C")
pdf.ln(3)
pdf.set_draw_color(60, 90, 70)
pdf.set_line_width(0.8)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(5)

pdf.set_font("Helvetica", "B", 13)
pdf.cell(0, 10, "Anamnesebogen / Patientenaufnahme", ln=True, align="C")
pdf.ln(3)

# --- Helper ---
def field(label, value, w_label=55, w_value=125):
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(w_label, 7, label, border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(w_value, 7, value, border="B", ln=True)

def section(title):
    pdf.ln(4)
    pdf.set_fill_color(234, 240, 236)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "  " + title, ln=True, fill=True)
    pdf.ln(2)

# --- Persoenliche Daten ---
section("Persoenliche Daten")
field("Nachname:", "Mueller")
field("Vorname:", "Hans-Peter")
field("Geburtsdatum:", "14.03.1958")
field("Geschlecht:", "maennlich")
field("Strasse / Hausnr.:", "Leopoldstr. 47")
field("PLZ / Ort:", "80802 Muenchen")
field("Telefon privat:", "089 / 987 654 32")
field("Telefon mobil:", "0171 / 234 56 78")
field("E-Mail:", "h.mueller58@gmx.de")
field("Muttersprache:", "Deutsch")

# --- Versicherung ---
section("Versicherungsdaten")
field("Versicherungsart:", "Gesetzlich versichert")
field("Krankenkasse:", "AOK Bayern")
field("Versichertennr.:", "A 123 456 789")

# --- Vorerkrankungen ---
section("Vorerkrankungen")
pdf.set_font("Helvetica", "", 9)
pdf.multi_cell(0, 5,
    "[X] Bluthochdruck (Hypertonie) - seit ca. 2012\n"
    "[X] Diabetes mellitus Typ 2 - seit 2018, Metformin\n"
    "[ ] Herzerkrankungen\n"
    "[ ] Lungenerkrankungen\n"
    "[X] Nierensteine - 2019, rechts, spontan abgegangen\n"
    "[ ] Krebserkrankungen\n"
    "[ ] Schilddruesenerkrankungen"
)

# --- Aktuelle Medikamente ---
section("Aktuelle Medikamente")
pdf.set_font("Helvetica", "", 9)
pdf.multi_cell(0, 5,
    "1. Ramipril 5mg  -  1x taeglich morgens\n"
    "2. Metformin 1000mg  -  2x taeglich (morgens/abends)\n"
    "3. Tamsulosin 0.4mg  -  1x taeglich abends"
)

# --- Allergien ---
section("Allergien / Unvertraeglichkeiten")
pdf.set_font("Helvetica", "", 9)
pdf.multi_cell(0, 5,
    "[X] Penicillin - Hautausschlag\n"
    "[ ] Kontrastmittel\n"
    "[ ] Latex\n"
    "Sonstige: keine bekannt"
)

# --- Aktuelle Beschwerden ---
section("Aktuelle urologische Beschwerden")
pdf.set_font("Helvetica", "", 9)
pdf.multi_cell(0, 5,
    "[X] Haeufiger Harndrang (besonders nachts, ca. 3-4x)\n"
    "[X] Abgeschwaechter Harnstrahl\n"
    "[X] Nachtroepfeln\n"
    "[ ] Blut im Urin\n"
    "[ ] Schmerzen beim Wasserlassen\n"
    "[X] Erektionsstoerungen - seit ca. 1 Jahr\n"
    "\n"
    "Beschwerden bestehen seit: ca. 6 Monaten, langsam zunehmend"
)

# --- Familienanamnese ---
section("Familienanamnese")
pdf.set_font("Helvetica", "", 9)
pdf.multi_cell(0, 5,
    "Vater: Prostatakarzinom mit 72 Jahren (verstorben mit 79)\n"
    "Mutter: Bluthochdruck, Diabetes\n"
    "Geschwister: 1 Bruder, gesund"
)

# --- Unterschrift ---
pdf.ln(8)
pdf.set_font("Helvetica", "", 9)
pdf.cell(95, 7, "Muenchen, den 10.04.2026", border="T", align="C")
pdf.cell(10, 7, "")
pdf.cell(85, 7, "Hans-Peter Mueller", border="T", align="C")
pdf.ln(4)
pdf.set_font("Helvetica", "", 7)
pdf.cell(95, 5, "Ort, Datum", align="C")
pdf.cell(10, 5, "")
pdf.cell(85, 5, "Unterschrift Patient", align="C")

# --- Save ---
out = "demo_anamnesebogen.pdf"
pdf.output(out)
print(f"Saved: {out}")
