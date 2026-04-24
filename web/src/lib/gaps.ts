/**
 * Single source of truth for currently-known gaps in tools.
 * Imported by tool views; rendered via <AmbiguityBanner gaps={…} />.
 *
 * When you close a gap (real adapter, real schema, real rules…),
 * remove the entry here. When you discover a new one, add it.
 */

export type Gap = {
	title: string;
	detail: string;
	closes_with?: string;
};

export const gaps = {
	patientenakte: (adapter: string, ungrounded: string[]): Gap[] => {
		const out: Gap[] = [];
		if (adapter === 'mock') {
			out.push({
				title: 'Mock-Daten',
				detail:
					'Die Patientenakte zeigt synthetische Demo-Datensätze (31 fiktive Patienten), keine echten Praxisdaten.',
				closes_with:
					'MEDICAL_OFFICE_ADAPTER=mariadb + Verbindungsdaten zu Medical Office.'
			});
		}
		if (ungrounded.includes('fall') || ungrounded.includes('befund') || ungrounded.includes('abrechnung')) {
			out.push({
				title: 'Schema unvollständig',
				detail: `Tabellen ${ungrounded.join(', ')} sind noch nicht gegen Medical Offices echte Spaltennamen abgeglichen.`,
				closes_with:
					'Schema-Extraktion auf dem Praxisserver (tooling/extract-mo-schema.sh).'
			});
		}
		return out;
	},

	rechnungspruefung: (
		adapter: string,
		ungrounded: string[],
		ruleCount: number
	): Gap[] => {
		const out: Gap[] = [];
		if (adapter === 'mock' || ungrounded.includes('abrechnung')) {
			out.push({
				title: 'Abrechnungspositionen-Schema',
				detail:
					'Echte Positionen aus Medical Office sind noch nicht angebunden. Die Prüfung läuft gegen Demo-Daten.',
				closes_with: 'MariaDB-Adapter + Schema-Mapping.'
			});
		}
		if (ruleCount === 0) {
			out.push({
				title: 'Regelbibliothek leer',
				detail:
					'Keine EBM/GOÄ-Plausibilitätsregeln implementiert. Die Prüfung erkennt nur Duplikate und fehlende Pflichtfelder.',
				closes_with:
					'Recherche-Ergebnisse aus tooling/research → server/app/billing_rules/.'
			});
		}
		return out;
	}
};
