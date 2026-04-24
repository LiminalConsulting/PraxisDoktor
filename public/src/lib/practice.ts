/**
 * Practice content — single source of truth.
 * Editable here, propagates everywhere on the site.
 */

export const practice = {
	name: 'Urologische Praxis Dr. Rug & Dr. Bruckschen',
	shortName: 'Praxis Dr. Rug & Dr. Bruckschen',
	tagline: 'Urologie und Andrologie in Karlsruhe',

	address: {
		street: 'Kaiserstraße 142', // TODO: confirm with Papa
		zip: '76133',
		city: 'Karlsruhe'
	},

	contact: {
		phone: '+49 721 …',           // TODO
		fax: '+49 721 …',             // TODO
		email: 'praxis@uro-karlsruhe.de' // TODO
	},

	hours: [
		{ days: 'Mo – Fr', time: '08:00 – 12:00' },
		{ days: 'Mo, Di, Do', time: '14:00 – 18:00' },
		{ days: 'Mi, Fr nachmittags', time: 'nach Vereinbarung' }
	],

	doctors: [
		{
			name: 'Dr. med. Andreas Rug',
			role: 'Facharzt für Urologie',
			focus: ['Andrologie', 'Krebsvorsorge', 'Potenz- und Fruchtbarkeits-Checks'],
			bio: 'Gründer der Praxis. Langjährige Erfahrung in der ambulanten urologischen Versorgung mit Schwerpunkt auf persönlicher Betreuung.'
		},
		{
			name: 'Dr. med. … Bruckschen', // TODO confirm full name
			role: 'Fachärztin für Urologie',
			focus: ['Urologie', 'Andrologie'],
			bio: 'Gemeinsam mit Dr. Rug Trägerin der Praxis seit 2024.'
		}
	],

	services: [
		{ title: 'Krebsvorsorge', text: 'Strukturierte Vorsorgeuntersuchungen für Männer ab 45 — Prostata, Niere, Blase.' },
		{ title: 'Andrologie', text: 'Hormondiagnostik, Fruchtbarkeit, erektile Funktion. Diskret und kompetent.' },
		{ title: 'Steindiagnostik', text: 'Bildgebung und Therapieplanung bei Nieren- und Harnsteinen.' },
		{ title: 'Inkontinenz', text: 'Diagnostik und konservative Therapie bei Blasenfunktionsstörungen.' },
		{ title: 'Sonographie', text: 'Hochauflösende Ultraschalldiagnostik vor Ort.' },
		{ title: 'Kleine ambulante Eingriffe', text: 'In der Praxis durchführbare urologische Eingriffe.' }
	]
};
