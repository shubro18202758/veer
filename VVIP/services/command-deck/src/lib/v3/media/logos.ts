/**
 * Agency and data-source marks (static/logos; owners and sources in static/logos/NOTICE.md). Used as-is — trimmed and
 * resized only, never redrawn or recoloured — on a light plate where a mark needs one. The marks belong to their
 * owners; Veer is a prototype and is not affiliated with or endorsed by them (the credit line says so where credits
 * live). When a mark is missing, the caller falls back to the generic agency tile (static/illustrations/agencies).
 */
import { MARK_ROWS } from './logos.data';

export interface Mark {
	key: string;
	/** The owner's name as the owner writes it (EN; the pack has HI / GU). */
	name: string;
	src: string;
	w: number;
	h: number;
	/** 'light': a white plate (a dark or transparent mark that would vanish on the night ground); 'dark': a dark plate (white lettering); 'none'. */
	plate: 'light' | 'dark' | 'none';
}

export const MARKS: readonly Mark[] = MARK_ROWS;
const BY_KEY = new Map(MARKS.map((m) => [m.key, m]));

/** Roles the deck speaks of → the marks that stand for them, best first. */
// Ahmedabad Fire Services, ERSS 112 and the Jan Rakshak volunteers have no mark on file: they keep the generic badge.
const ROLE: Readonly<Record<string, readonly string[]>> = {
	police: ['ahmedabad_city_police', 'gujarat_police'],
	zone: ['ahmedabad_city_police', 'gujarat_police'],
	traffic: ['ahmedabad_city_police', 'gujarat_police'],
	patrol: ['ahmedabad_city_police', 'gujarat_police'],
	ems: ['emri_108'],
	'108': ['emri_108'],
	ambulance: ['emri_108'],
	emri: ['emri_108'],
	municipal: ['amc'],
	amc: ['amc'],
	disaster: ['gsdma', 'ndma'],
	sdrf: ['gsdma', 'ndma'],
	gsdma: ['gsdma'],
	ndrf: ['ndma'],
	ndma: ['ndma'],
	sachet: ['ndma_sachet'],
	imd: ['imd'],
	weather: ['imd'],
	metro: ['gmrc'],
	gmrc: ['gmrc'],
	brts: ['janmarg_brts'],
	janmarg: ['janmarg_brts'],
	amts: ['amts'],
	osm: ['openstreetmap'],
	openstreetmap: ['openstreetmap'],
	cesium: ['cesium'],
	gdelt: ['gdelt'],
	google_news: ['google_news'],
	reddit: ['reddit'],
};

/** The mark for a role, an agency or a source name (null when none is on file). */
export function markFor(role: string | null | undefined): Mark | null {
	const k = (role ?? '').toLowerCase().trim().replace(/[\s-]+/g, '_');
	if (!k) return null;
	const direct = BY_KEY.get(k);
	if (direct) return direct;
	for (const key of ROLE[k] ?? []) {
		const m = BY_KEY.get(key);
		if (m) return m;
	}
	return null;
}

/** A source's mark from its publisher / feed name or domain (Sachet, IMD, GDELT, the corporation …); null when none is on file. */
export function sourceMark(publisher: string | null | undefined): Mark | null {
	const p = (publisher ?? '').toLowerCase();
	if (!p) return null;
	if (/sachet/.test(p)) return markFor('sachet');
	if (/gsdma|gujarat state disaster/.test(p)) return markFor('gsdma');
	if (/ndma|disaster management/.test(p)) return markFor('ndma');
	if (/\bimd\b|meteorolog|mausam/.test(p)) return markFor('imd');
	if (/gdelt/.test(p)) return markFor('gdelt');
	if (/news\.google|google news/.test(p)) return markFor('google_news');
	if (/reddit/.test(p)) return markFor('reddit');
	if (/\bamc\b|municipal|ahmedabad mun|amdavad mun/.test(p)) return markFor('amc');
	if (/police/.test(p)) return markFor('police');
	if (/\b108\b|emri|ambulance/.test(p)) return markFor('108');
	if (/metro|gmrc/.test(p)) return markFor('metro');
	if (/janmarg|brts/.test(p)) return markFor('brts');
	if (/\bamts\b/.test(p)) return markFor('amts');
	return null;
}
