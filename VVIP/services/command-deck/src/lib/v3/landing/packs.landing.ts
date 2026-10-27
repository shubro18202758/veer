/**
 * The landing page's string pack (/welcome, V3-LANDING). EN here; HI and GU in ./packs.landing.hi.ts and
 * ./packs.landing.gu.ts, complete for every key (tests/welcome.unit.mjs checks it). Registered additively through
 * registerPack(); loaded only by the landing page. Every key starts with `v3l_`.
 *
 * Copy rules (the deck's): sentence case, at most one " · " per string, titles and headings ≤ 32 characters, no
 * all-caps word outside the acronym list. Honest wording: the figures are modelled and say so; minutes returned to
 * the golden hour are never a claim about patients' outcomes; screenshots show exercise data; a reference photo is
 * never live; the agencies' marks belong to their owners (packs.media says so).
 */
import { registerPack } from '$lib/i18n/strings';
import { langChunks } from '$lib/i18n/load';

type Fn = (...args: unknown[]) => string;
export type LandingPack = Record<string, string | Fn>;

const s = (v: unknown) => String(v ?? '');

const en = {
	v3l_doc: 'Veer · Regulated, not stopped',
	v3l_meta: 'Veer gives the police, traffic, 108 and city teams of Ahmedabad one live picture of the roads. The AI proposes; a named officer decides.',
	v3l_skip: 'Skip to the page',
	v3l_logo: 'Veer',
	v3l_nav: 'Veer pages',
	v3l_lang: 'Language',
	v3l_nav_how: 'How it works',
	v3l_nav_rules: 'Principles',
	v3l_nav_citizen: 'Your road',
	v3l_nav_driver: '108 driver',
	v3l_open_console: 'Open the console',
	v3l_check_road: 'Check your road',
	v3l_hero_eyebrow: 'City operations · Ahmedabad',
	v3l_hero_h: 'Regulated, not stopped.',
	v3l_hero_sub: 'One live picture of Ahmedabad for police, traffic, 108 and the city — the AI proposes, a named officer decides.',
	v3l_hero_rule: 'Vehicles only. Plates stay masked until an officer is named.',
	v3l_shot_tag: 'Console screenshot · exercise data',
	v3l_shot_alt_map: 'Screenshot of the Veer map: the photoreal 3D city of Ahmedabad and the decisions waiting',
	v3l_shot_alt_decide: 'Screenshot of Decide: one stolen-vehicle decision on the real map, waiting for a named officer',
	v3l_shot_alt_plan: 'Screenshot of Plan a movement: the start, the destination and the protection class beside a satellite map',
	v3l_shot_alt_home: 'Screenshot of Home: the decision that needs an officer now, the city pulse and the decisions waiting',
	v3l_problem_kicker: 'The problem',
	v3l_problem_line: 'Today a protected movement freezes each junction for 15 to 45 minutes, for a passage that takes seconds.',
	v3l_problem_rule: 'The protocol already says regulated, not stopped. Veer is the tooling that makes it possible.',
	v3l_fig_hold: '2–3 min',
	v3l_fig_hold_label: 'a rolling hold per junction, in place of a freeze of 15 to 45 minutes',
	v3l_fig_delay: '100×',
	v3l_fig_delay_label: 'less junction-freeze delay for commuters, 25× to 506× across the cases',
	v3l_fig_golden: '~33,000',
	v3l_fig_golden_label: 'golden-hour minutes a year returned to 108 patients',
	v3l_modelled: 'Modelled',
	v3l_modelled_note: 'Model outputs on the real road network of Ahmedabad under stated assumptions — not field measurements, and not a claim about patient outcomes.',
	v3l_how_kicker: 'How it works',
	v3l_how_heading: 'See. Decide. Act.',
	v3l_how_lead: 'Each step is one screen, with one job and one primary button.',
	v3l_step: (n: unknown) => `Step ${s(n)}`,
	v3l_see: 'See',
	v3l_see_title: 'One live picture',
	v3l_see_body: 'The real city, live operations, official alerts and public reports about places, never people.',
	v3l_decide: 'Decide',
	v3l_decide_title: 'One decision at a time',
	v3l_decide_body: 'Soonest deadline first, what changes if you approve, and a named officer on the record.',
	v3l_act: 'Act',
	v3l_act_title: 'Rolling holds, not freezes',
	v3l_act_body: 'Plan a movement with short holds per junction, draft advisories in three languages and open a corridor window for the 108.',
	v3l_who_kicker: 'For everyone',
	v3l_who_heading: 'Four people, one picture',
	v3l_who_officer: 'Duty officer',
	v3l_who_officer_body: 'What needs me now, the real map of the place, and my name on every decision.',
	v3l_who_analyst: 'Analyst',
	v3l_who_analyst_body: 'The full workspace one click deeper: timeline, audit trail, link analysis and replay.',
	v3l_who_citizen: 'Citizen',
	v3l_who_citizen_body: 'Which roads hold, when and for how long, in plain words. No sign‑in.',
	v3l_who_driver: '108 driver',
	v3l_who_driver_body: 'Ask for a green corridor in one tap, Gujarati first, with a live countdown.',
	v3l_seat_console: 'In the console',
	v3l_seat_public: 'Public page',
	v3l_rules_kicker: 'Principles',
	v3l_rules_heading: 'Rules the code enforces',
	v3l_rule_vehicles: 'Vehicles only',
	v3l_rule_vehicles_body: 'Cameras read registration marks. No face, no person and no biometric field anywhere.',
	v3l_rule_masked: 'Plates masked',
	v3l_rule_masked_body: 'A registration mark stays masked until a duty officer is named on the console.',
	v3l_rule_officer: 'The AI proposes, an officer decides',
	v3l_rule_officer_body: 'Nothing is approved, dispatched or rerouted without a named officer.',
	v3l_rule_holds: 'No answer, the plan holds',
	v3l_rule_holds_body: 'A time-boxed proposal expires and the movement keeps its approved plan.',
	v3l_rule_victim: 'No fine on a theft victim',
	v3l_rule_victim_body: 'Reads of a stolen vehicle are evidence only. An e-challan on it is refused.',
	v3l_rule_labels: 'Honest labels',
	v3l_rule_labels_body: 'Emulated, simulated, unverified, news-reported or official: every source says which.',
	v3l_built_kicker: 'Built on',
	v3l_built_heading: 'Real roads, real sources',
	v3l_built_roads: 'Real roads',
	v3l_built_roads_body: 'The road network of Ahmedabad from OpenStreetMap: names, junctions and geometry.',
	v3l_built_city: 'The photoreal city',
	v3l_built_city_body: 'Google Photorealistic 3D Tiles through Cesium ion. A reference picture, not a live image.',
	v3l_built_alerts: 'Official alerts',
	v3l_built_alerts_body: 'Public warnings from NDMA Sachet and IMD, read when the feed is switched on.',
	v3l_built_ai: 'Local two-tier AI',
	v3l_built_ai_body: 'A strategic and a tactical model on one server beside the control room. Every answer is checked against the data.',
	v3l_marks_heading: 'Agencies and sources',
	v3l_end_heading: 'See the city move',
	v3l_end_body: 'Officers work in the console. Everyone else can check a road or ask for a corridor, with no sign‑in.',
	v3l_driver_page: 'Open the 108 driver page',
	v3l_foot_pages: 'Pages',
	v3l_foot_console: 'Console',
	v3l_foot_citizen: 'Citizen',
	v3l_foot_driver: '108 driver',
	v3l_foot_source: 'Source code on GitHub',
	v3l_foot_credits: 'Credits',
	v3l_foot_osm: 'Road data © OpenStreetMap contributors, ODbL 1.0.',
	v3l_foot_code: 'The code is open source.',
	v3l_foot_proto: 'Veer is a prototype. Every feed it emulates or simulates is labelled as such.',
	v3l_foot_shots: 'Console screenshots show exercise data, with plates masked.',
	v3l_illustration: 'Illustration',
};

export type LandingKey = keyof typeof en;

registerPack('en', en);

export const LANDING_PACK_KEYS: readonly LandingKey[] = Object.keys(en) as LandingKey[];
export const LANDING_PACKS: Record<string, LandingPack> = { en };

/** Register one language chunk (lib/i18n/load.ts's landing site; additive, first registration wins). */
export function adopt(code: 'hi' | 'gu', pack: LandingPack): void {
	LANDING_PACKS[code] = pack;
	registerPack(code, pack);
}

/*
 * Language chunks (the deck's FIX-E-PERF2 pattern): HI and GU live only in their own files. The server render and every
 * non-production run register both before this module finishes evaluating; the production browser awaits the document's
 * language and loads the other on the first switch.
 */
if (process.env.NODE_ENV !== 'production' || import.meta.env.SSR !== false) {
	adopt('hi', (await import('./packs.landing.hi')).hi);
	adopt('gu', (await import('./packs.landing.gu')).gu);
} else {
	await langChunks('packs.landing', (code) =>
		code === 'hi' ? import('./packs.landing.hi').then((c) => adopt('hi', c.hi)) : import('./packs.landing.gu').then((c) => adopt('gu', c.gu)),
	);
}
