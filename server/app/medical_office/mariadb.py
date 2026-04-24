"""
MariaDB adapter — STUB. Not connected to Medical Office until Papa runs
`tooling/extract-mo-schema.sh` on the practice server and we map the
records below to MO's actual column names.

Until then every method raises SchemaNotGrounded so we never silently
return wrong results. Selecting this adapter via MEDICAL_OFFICE_ADAPTER=mariadb
will fail loudly — by design.
"""
from __future__ import annotations

from .adapter import MedicalOfficeAdapter
from .schema import SchemaNotGrounded


class MariaDBAdapter(MedicalOfficeAdapter):
    name = "mariadb"
    grounded_kinds = ()  # nothing is grounded yet

    def __init__(self):
        # We deliberately don't open a connection at construction time.
        # The connection string + credentials come in a follow-up commit
        # after Papa provides them.
        pass

    def _not_yet(self) -> SchemaNotGrounded:
        return SchemaNotGrounded(
            "MariaDB adapter is awaiting MO schema extraction. "
            "Run tooling/extract-mo-schema.sh on the practice server, then "
            "map the columns in server/app/medical_office/mariadb.py."
        )

    def get_patient(self, patient_id):           raise self._not_yet()
    def search_patients(self, query, limit=20):  raise self._not_yet()
    def list_patients(self, limit=50, offset=0): raise self._not_yet()
    def list_faelle_for_patient(self, pid):      raise self._not_yet()
    def list_befunde_for_patient(self, pid):     raise self._not_yet()
    def list_positions_for_fall(self, fid):      raise self._not_yet()
    def list_positions_for_quartal(self, q):     raise self._not_yet()
