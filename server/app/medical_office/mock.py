"""
Deterministic synthetic data for development. Realistic German urology
practice. ~30 patients, mix of quarters, GKV + Privat, with intentional
coherence issues sprinkled in so the integrity checker has work to do.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional

from .adapter import MedicalOfficeAdapter
from .schema import Patient, Fall, Befund, AbrechnungPosition


def _p(id: str, nach: str, vor: str, gd: tuple[int, int, int], geschlecht: str,
       plz: str = "76133", ort: str = "Karlsruhe",
       titel: Optional[str] = None) -> Patient:
    return Patient(
        id=id, nachname=nach, vorname=vor,
        geburtsdatum=date(*gd), geschlecht=geschlecht,
        titel=titel, anrede=("Herr" if geschlecht == "M" else "Frau"),
        strasse="Musterstraße", hausnr=str((sum(map(ord, nach)) % 80) + 1),
        plz=plz, ort=ort,
        telefon_privat=f"0721 {abs(hash(id)) % 9000000 + 1000000}",
        telefon_mobil=None,
        email=f"{vor.lower()}.{nach.lower()}@example.de",
        muttersprache="Deutsch",
    )


_PATIENTS: list[Patient] = [
    _p("P-1001", "Müller",       "Hans",      (1958, 3, 12),  "M"),
    _p("P-1002", "Schmidt",      "Klaus",     (1962, 7, 4),   "M"),
    _p("P-1003", "Becker",       "Wolfgang",  (1955, 11, 23), "M", titel="Dr."),
    _p("P-1004", "Weber",        "Manfred",   (1949, 1, 30),  "M"),
    _p("P-1005", "Schneider",    "Ute",       (1971, 6, 9),   "W"),
    _p("P-1006", "Fischer",      "Renate",    (1953, 9, 17),  "W"),
    _p("P-1007", "Meyer",        "Jürgen",    (1968, 4, 25),  "M"),
    _p("P-1008", "Hoffmann",     "Karl",      (1942, 12, 1),  "M"),
    _p("P-1009", "Schulz",       "Gerda",     (1947, 8, 14),  "W"),
    _p("P-1010", "Koch",         "Stefan",    (1981, 5, 6),   "M"),
    _p("P-1011", "Bauer",        "Petra",     (1966, 10, 22), "W"),
    _p("P-1012", "Richter",      "Michael",   (1974, 2, 18),  "M"),
    _p("P-1013", "Klein",        "Andrea",    (1959, 7, 30),  "W"),
    _p("P-1014", "Wolf",         "Heinz",     (1944, 11, 5),  "M"),
    _p("P-1015", "Schröder",     "Lisa",      (1990, 3, 19),  "W"),
    _p("P-1016", "Neumann",      "Otto",      (1939, 6, 11),  "M"),
    _p("P-1017", "Schwarz",      "Brigitte",  (1957, 4, 27),  "W"),
    _p("P-1018", "Zimmermann",   "Frank",     (1965, 9, 8),   "M"),
    _p("P-1019", "Braun",        "Sabine",    (1972, 1, 14),  "W"),
    _p("P-1020", "Krüger",       "Werner",    (1951, 12, 21), "M"),
    _p("P-1021", "Hofmann",      "Doris",     (1948, 5, 3),   "W"),
    _p("P-1022", "Hartmann",     "Andreas",   (1986, 8, 16),  "M"),
    _p("P-1023", "Lange",        "Helga",     (1946, 10, 28), "W"),
    _p("P-1024", "Schmitt",      "Rolf",      (1953, 2, 7),   "M"),
    _p("P-1025", "Werner",       "Marion",    (1969, 11, 12), "W"),
    _p("P-1026", "Schmitz",      "Thomas",    (1977, 3, 24),  "M"),
    _p("P-1027", "Krause",       "Edith",     (1941, 7, 1),   "W"),
    _p("P-1028", "Meier",        "Bernd",     (1960, 4, 9),   "M"),
    _p("P-1029", "Lehmann",      "Karin",     (1963, 12, 13), "W"),
    _p("P-1030", "Schmid",       "Walter",    (1937, 6, 26),  "M"),
]
# Intentional coherence issue: P-1031 missing PLZ + has malformed phone
_PATIENTS.append(Patient(
    id="P-1031", nachname="Hansen", vorname="Lars",
    geburtsdatum=date(1981, 9, 9), geschlecht="M",
    titel=None, anrede="Herr",
    strasse="Beispielweg", hausnr="42",
    plz=None, ort="Karlsruhe",
    telefon_privat="0721-aaa-bbb",  # malformed
    telefon_mobil=None, email=None,
    muttersprache="Dänisch",
))


def _faelle_for(pid: str) -> list[Fall]:
    """Fabricate 1–3 cases per patient across recent quarters."""
    out: list[Fall] = []
    seed = sum(map(ord, pid))
    n = (seed % 3) + 1
    quartals = ["2025Q4", "2026Q1", "2026Q2"]
    for i in range(n):
        out.append(Fall(
            id=f"F-{pid[2:]}-{i+1}",
            patient_id=pid,
            quartal=quartals[i],
            fallart="GKV" if (seed + i) % 5 != 0 else "Privat",
            diagnose_codes=[
                d for d in [
                    "N40.1",  # benign prostatic hyperplasia
                    "N39.0" if i == 0 else None,  # UTI
                    "Z12.5" if (seed + i) % 4 == 0 else None,  # Vorsorge
                ] if d
            ],
            eroeffnet_am=date(2025 + i // 2, ((i * 3) % 12) + 1, 5),
        ))
    return out


def _befunde_for(pid: str) -> list[Befund]:
    out: list[Befund] = []
    seed = sum(map(ord, pid))
    if seed % 4 != 0:
        out.append(Befund(
            id=f"B-{pid[2:]}-1", patient_id=pid, fall_id=f"F-{pid[2:]}-1",
            erstellt_am=datetime(2026, 1, 15, 10, 30),
            ersteller="Dr. Rug", typ="PSA-Wert",
            inhalt=f"PSA: {2.1 + (seed % 30) / 10:.1f} ng/ml",
        ))
    if seed % 3 == 0:
        out.append(Befund(
            id=f"B-{pid[2:]}-2", patient_id=pid, fall_id=f"F-{pid[2:]}-1",
            erstellt_am=datetime(2026, 2, 8, 11, 0),
            ersteller="Dr. Rug", typ="Sono",
            inhalt="Sono Niere bds.: unauffällig. Restharn 35 ml.",
        ))
    return out


def _positions_for_fall(fall_id: str, fall: Fall) -> list[AbrechnungPosition]:
    """Fabricate billing positions, with intentional issues for the rule
    engine to find: a duplicated 03000, an over-faktor GOÄ without
    Begründung, a male-only GOP on a female patient (where applicable)."""
    seed = sum(map(ord, fall_id))
    if fall.fallart == "GKV":
        positions = [
            AbrechnungPosition(
                id=f"AP-{fall_id}-1", patient_id=fall.patient_id, fall_id=fall_id,
                leistungsdatum=fall.eroeffnet_am, katalog="EBM",
                code="03000", bezeichnung="Versichertenpauschale Hausarzt", anzahl=1,
                punkte=120, betrag_eur=14.78,
            ),
            AbrechnungPosition(
                id=f"AP-{fall_id}-2", patient_id=fall.patient_id, fall_id=fall_id,
                leistungsdatum=fall.eroeffnet_am, katalog="EBM",
                code="26310", bezeichnung="Urologische Grundpauschale", anzahl=1,
                punkte=180, betrag_eur=22.17,
            ),
        ]
        # Sprinkle a duplicate to test the rule engine
        if seed % 7 == 0:
            positions.append(AbrechnungPosition(
                id=f"AP-{fall_id}-dup", patient_id=fall.patient_id, fall_id=fall_id,
                leistungsdatum=fall.eroeffnet_am, katalog="EBM",
                code="03000", bezeichnung="Versichertenpauschale Hausarzt", anzahl=1,
                punkte=120, betrag_eur=14.78,
            ))
        return positions
    else:  # Privat → GOÄ
        positions = [
            AbrechnungPosition(
                id=f"AP-{fall_id}-1", patient_id=fall.patient_id, fall_id=fall_id,
                leistungsdatum=fall.eroeffnet_am, katalog="GOÄ",
                code="1", bezeichnung="Beratung", anzahl=1, faktor=2.3,
                betrag_eur=10.72,
            ),
            AbrechnungPosition(
                id=f"AP-{fall_id}-2", patient_id=fall.patient_id, fall_id=fall_id,
                leistungsdatum=fall.eroeffnet_am, katalog="GOÄ",
                code="410", bezeichnung="Sonographie eines Organs", anzahl=1, faktor=2.3,
                betrag_eur=20.11,
            ),
        ]
        # Over-Schwellenwert without Begründung — intentional flag-bait
        if seed % 5 == 0:
            positions.append(AbrechnungPosition(
                id=f"AP-{fall_id}-overfaktor", patient_id=fall.patient_id, fall_id=fall_id,
                leistungsdatum=fall.eroeffnet_am, katalog="GOÄ",
                code="5", bezeichnung="Symptombezogene Untersuchung", anzahl=1,
                faktor=3.5, begruendung=None, betrag_eur=15.66,
            ))
        return positions


class MockAdapter(MedicalOfficeAdapter):
    name = "mock"
    grounded_kinds = ("patient",)  # only Patient is fully grounded

    def get_patient(self, patient_id: str):
        for p in _PATIENTS:
            if p.id == patient_id:
                return p
        return None

    def search_patients(self, query: str, limit: int = 20):
        q = query.lower().strip()
        if not q:
            return _PATIENTS[:limit]
        out = []
        for p in _PATIENTS:
            hay = f"{p.nachname} {p.vorname} {p.id} {p.plz or ''}".lower()
            if q in hay:
                out.append(p)
            if len(out) >= limit:
                break
        return out

    def list_patients(self, limit: int = 50, offset: int = 0):
        return _PATIENTS[offset:offset + limit]

    def list_faelle_for_patient(self, patient_id: str):
        return _faelle_for(patient_id)

    def list_befunde_for_patient(self, patient_id: str):
        return _befunde_for(patient_id)

    def list_positions_for_fall(self, fall_id: str):
        # need the fall to know fallart — search all faelle
        for p in _PATIENTS:
            for f in _faelle_for(p.id):
                if f.id == fall_id:
                    return _positions_for_fall(fall_id, f)
        return []

    def list_positions_for_quartal(self, quartal: str):
        out: list[AbrechnungPosition] = []
        for p in _PATIENTS:
            for f in _faelle_for(p.id):
                if f.quartal == quartal:
                    out.extend(_positions_for_fall(f.id, f))
        return out
