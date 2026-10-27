/**
 * Reference photographs of real places (static/photos; credits and licences in static/photos/NOTICE.md). A photo is
 * ALWAYS shown with "Reference photo · not live" and its credit, never where a live camera or a map is expected, and
 * never as the current situation: it shows what the place looks like, not what is happening there.
 */
import { PHOTO_ROWS } from './photos.data';

export interface PlacePhoto {
	slug: string;
	title: string;
	/** The curated place key (riverfront, old_city, motera_stadium …). */
	place: string;
	lat: number;
	lon: number;
	/** The coordinates are the photo's own place (false: the city's centroid; never matched by distance). */
	near: boolean;
	author: string;
	license: string;
	licenseUrl: string;
	/** The Wikimedia Commons file page. */
	source: string;
	/** "Photo: <author> · <licence> · Wikimedia Commons". */
	credit: string;
}

export const PHOTOS: readonly PlacePhoto[] = PHOTO_ROWS;
const BY_SLUG = new Map(PHOTOS.map((p) => [p.slug, p]));

export function photoBySlug(slug: string | null | undefined): PlacePhoto | null {
	return (slug && BY_SLUG.get(slug)) || null;
}

export function photoSrc(p: PlacePhoto, w: 640 | 1600 = 640): string {
	return `/photos/${p.slug}-${w}.webp`;
}

export function photoSrcset(p: PlacePhoto): string {
	return `${photoSrc(p, 640)} 640w, ${photoSrc(p, 1600)} 1600w`;
}

/** The riverfront has a day, a dusk and a night photograph: the one that matches the IST hour. */
function variant(list: readonly PlacePhoto[], hour: number | null): PlacePhoto | null {
	if (!list.length) return null;
	if (hour == null || list.length === 1) return list[0];
	const want = hour >= 7 && hour < 17 ? 'day' : hour >= 17 && hour < 20 ? 'dusk' : 'night';
	return list.find((p) => p.slug.endsWith(`-${want}`)) ?? list[0];
}

/** A photo of a curated place key. */
export function photoForPlace(place: string | null | undefined, hour: number | null = null): PlacePhoto | null {
	if (!place) return null;
	return variant(
		PHOTOS.filter((p) => p.place === place),
		hour,
	);
}

const R = 6_371_000;
function metres(aLon: number, aLat: number, bLon: number, bLat: number): number {
	const r = Math.PI / 180;
	const dLat = (bLat - aLat) * r;
	const dLon = (bLon - aLon) * r;
	const h = Math.sin(dLat / 2) ** 2 + Math.cos(aLat * r) * Math.cos(bLat * r) * Math.sin(dLon / 2) ** 2;
	return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** The nearest photographed place within `maxM` metres of a point (only photos whose coordinates are their own). */
export function photoNear(lon: number | null | undefined, lat: number | null | undefined, maxM = 900, hour: number | null = null): PlacePhoto | null {
	if (lon == null || lat == null || !Number.isFinite(lon) || !Number.isFinite(lat)) return null;
	let best: PlacePhoto | null = null;
	let bestD = Infinity;
	for (const p of PHOTOS) {
		if (!p.near) continue;
		const d = metres(lon, lat, p.lon, p.lat);
		if (d < bestD) {
			best = p;
			bestD = d;
		}
	}
	if (!best || bestD > maxM) return null;
	return best.place === 'riverfront' ? variant(PHOTOS.filter((p) => p.place === 'riverfront'), hour) : best;
}

/** Place names in a title or a road name that have a photograph (word-bounded, case-insensitive). */
const WORDS: readonly [RegExp, string][] = [
	[/\briver\s?front\b/i, 'riverfront'],
	[/\batal\b/i, 'atal_bridge'],
	[/\b(ashram road|nehru bridge|ellis\s?bridge)\b/i, 'ashram_road'],
	[/\bkankaria\b/i, 'kankaria'],
	[/\b(motera|narendra modi stadium|stadium)\b/i, 'motera_stadium'],
	[/\b(kalupur|ahmedabad junction|railway station)\b/i, 'kalupur'],
	[/\b(teen darwaja|teen darwaza|three gates|bhadra|lal darwaja|lal darwaza|manek chowk|old city|walled city)\b/i, 'old_city'],
	[/\b(pol|pols)\b/i, 'pols'],
	[/\b(airport|svpi)\b/i, 'airport'],
	[/\b(gandhinagar|mahatma mandir)\b/i, 'gandhinagar'],
	[/\b(gandhi ashram|sabarmati ashram)\b/i, 'gandhi_ashram'],
	[/\bmetro\b/i, 'metro'],
];

/** A photo for the first place named in a text (a title, a road, a destination). */
export function photoForText(text: string | null | undefined, hour: number | null = null): PlacePhoto | null {
	if (!text) return null;
	for (const [re, place] of WORDS) if (re.test(text)) return photoForPlace(place, hour);
	return null;
}
