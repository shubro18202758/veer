/**
 * What the landing page (/welcome, V3-LANDING) shows, as data — the page is static content and static assets only:
 * no API call, no store, no operator code. tests/welcome.unit.mjs reads this module (the links, the pictures, the
 * captions), so a change here is a change the test sees.
 *
 * Pictures, each with its honest label:
 *   - reference photos of the city (static/photos, Wikimedia Commons): always "Reference photo · not live" + credit;
 *   - console screenshots (static/landing, NOTICE.md): a development deck on a sandbox stack running exercise data,
 *     no officer named, so every registration mark is masked — captioned "Console screenshot · exercise data";
 *   - key art (static/artwork): original illustrations, captioned "Illustration";
 *   - agency and source marks (static/logos): as-is, with the owners' credit line.
 */
import { photoBySlug, type PlacePhoto } from '../media/photos';
import { markFor, type Mark } from '../media/logos';

/** Where each door leads. The console is an operator document (its own CSP), so links into it reload. */
export const HREF = {
	console: '/',
	analyst: '/analyst',
	citizen: '/citizen',
	driver: '/driver',
	source: 'https://github.com/shubro18202758/veer',
	photoCredits: '/photos/NOTICE.md',
} as const;

/** The operator routes: a link to one of them must load a new document (data-sveltekit-reload). */
export const OPERATOR_HREFS: readonly string[] = [HREF.console, HREF.analyst];

/** The hero's photograph (night light trails on Nehru Bridge) and the closing band's (the riverfront at night). */
export const HERO_PHOTO_SLUG = 'nehru-bridge-night';
export const END_PHOTO_SLUG = 'sabarmati-riverfront-night';

export function heroPhoto(): PlacePhoto {
	const p = photoBySlug(HERO_PHOTO_SLUG);
	if (!p) throw new Error(`landing: no reference photo ${HERO_PHOTO_SLUG}`);
	return p;
}

export function endPhoto(): PlacePhoto {
	const p = photoBySlug(END_PHOTO_SLUG);
	if (!p) throw new Error(`landing: no reference photo ${END_PHOTO_SLUG}`);
	return p;
}

/** A console screenshot (static/landing): two widths, its alt text key. */
export interface Shot {
	key: 'map' | 'decide' | 'home' | 'plan';
	src: string;
	srcset: string;
	w: number;
	h: number;
	alt: string;
}

const shot = (key: Shot['key'], file: string, big: number, small: number, h: number, alt: string): Shot => ({
	key,
	src: `/landing/${file}-${small}.webp`,
	srcset: `/landing/${file}-${small}.webp ${small}w, /landing/${file}-${big}.webp ${big}w`,
	w: big,
	h,
	alt,
});

export const SHOTS: Readonly<Record<Shot['key'], Shot>> = {
	map: shot('map', 'console-map', 1600, 800, 1000, 'v3l_shot_alt_map'),
	decide: shot('decide', 'console-decide', 1600, 800, 1000, 'v3l_shot_alt_decide'),
	home: shot('home', 'console-home', 1600, 800, 1000, 'v3l_shot_alt_home'),
	plan: shot('plan', 'console-plan', 1600, 800, 1000, 'v3l_shot_alt_plan'),
};

/** The console shown in the hero window. */
export const HERO_SHOT: Shot['key'] = 'decide';

/**
 * How it works: three steps, one screen each (the hero window shows Decide, so no screen repeats), each framed as a
 * detail shot — `zoom` × the frame, centred on (`x`, `y`) % of the screenshot — so its words can be read.
 */
export const STEPS = [
	{ n: 1, key: 'see', shot: 'map', zoom: 1.45, x: 62, y: 30 },
	{ n: 2, key: 'decide', shot: 'home', zoom: 1.6, x: 18, y: 22 },
	{ n: 3, key: 'act', shot: 'plan', zoom: 1.55, x: 14, y: 72 },
] as const satisfies readonly { n: number; key: string; shot: Shot['key']; zoom: number; x: number; y: number }[];

/** For everyone: four people, each with the key art of their work and the door they use. */
export const AUDIENCES = [
	{ key: 'officer', art: '/artwork/events/protected_movement.svg', href: HREF.console, seat: 'console' },
	{ key: 'analyst', art: '/artwork/scenes/night.svg', href: HREF.analyst, seat: 'console' },
	{ key: 'citizen', art: '/artwork/events/advisory.svg', href: HREF.citizen, seat: 'public' },
	{ key: 'driver', art: '/artwork/events/green_corridor.svg', href: HREF.driver, seat: 'public' },
] as const satisfies readonly { key: string; art: string; href: string; seat: 'console' | 'public' }[];

/** The principles, each with the V3 glyph that signs it (`sign`; one glyph per noun, never a person). */
export const PRINCIPLES = [
	{ key: 'vehicles', sign: 'car' },
	{ key: 'masked', sign: 'lock' },
	{ key: 'officer', sign: 'badge' },
	{ key: 'holds', sign: 'clock' },
	{ key: 'victim', sign: 'shield' },
	{ key: 'labels', sign: 'verified' },
] as const satisfies readonly { key: string; sign: string }[];

/** Built on: four foundations, each with the marks of its sources (or the glyph that signs it). */
export const BUILT = [
	{ key: 'roads', marks: ['openstreetmap'], sign: null },
	{ key: 'city', marks: ['cesium'], sign: null },
	{ key: 'alerts', marks: ['ndma_sachet', 'imd'], sign: null },
	{ key: 'ai', marks: [], sign: 'spark' },
] as const satisfies readonly { key: string; marks: readonly string[]; sign: string | null }[];

/** The agencies and sources whose marks the row shows (static/logos; the owners' credit line sits under it). */
export const MARK_ROW = [
	'ahmedabad_city_police',
	'gujarat_police',
	'emri_108',
	'amc',
	'amts',
	'janmarg_brts',
	'gmrc',
	'gsdma',
	'ndma',
	'imd',
	'openstreetmap',
	'cesium',
] as const;

export function marks(keys: readonly string[]): Mark[] {
	return keys.map((k) => markFor(k)).filter((m): m is Mark => m !== null);
}
