/**
 * V3 asset gate (V3-P01; V3-SPEC §4.1, §4.4, §4.5, §10 P0) — zero browser.
 *
 *   node tests/v3-assets.unit.mjs
 *
 *   1. ILLUSTRATIONS  static/illustrations/{events,vehicles,agencies,empty,onboarding}: the 45 files of the
 *                     design's set, each a role="img" SVG with an aria-label (or a <title>); no <image>
 *                     (never a photo, never a camera frame), no <text> (no words in images, §7.8), no
 *                     script, no external reference; NO decision orange or alert red anywhere (and no
 *                     other warm, saturated hue that could read as one); every event kind Home can draw
 *                     has its tile.
 *   2. DETERMINISTIC  when the design's generator is on this machine (redesign/v3/assets/
 *                     build_illustrations.py), re-running it into a temp folder reproduces static/
 *                     illustrations byte for byte.
 *   3. BRAND          static/brand: the 8 files of §4.1; the waypoint is Veer blue (#276EF1; day #1E54B7), never orange or
 *                     red; no gradient, no filter (glow), no shield; each SVG labelled.
 *   4. GLYPHS         src/lib/v3/icons.ts: 68 glyphs, valid path data on the 24 grid, none a person.
 *   5. FONTS          V3 adds no font file (it reuses the deck's self-hosted Inter / Noto Devanagari /
 *                     Noto Gujarati, OFL, loaded once by the root layout); the (v3) layout imports only the
 *                     V3 tokens.
 *   6. WEIGHT         the illustration and brand sets stay small (static budget).
 *
 * Exits 0 with `ok <name>` lines, 1 on any failure.
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DECK = path.resolve(HERE, '..');
const ILL = path.join(DECK, 'static/illustrations');
const BRAND = path.join(DECK, 'static/brand');
const GENERATOR = '/home/sandy050405/argus/veer/.veer-orchestration/redesign/v3/assets/build_illustrations.py';

let failures = 0;
function ok(name, cond, detail = '') {
	if (cond) console.log(`ok   ${name}${detail ? ` — ${detail}` : ''}`);
	else {
		failures++;
		console.error(`FAIL ${name}${detail ? ` — ${detail}` : ''}`);
	}
}

const listSvgs = (dir) => {
	const out = [];
	const walk = (d) => {
		for (const f of readdirSync(d).sort()) {
			const p = path.join(d, f);
			if (statSync(p).isDirectory()) walk(p);
			else out.push(p);
		}
	};
	if (existsSync(dir)) walk(dir);
	return out;
};

/** HSL of a hex colour (h in degrees, s and l in 0..1). */
function hsl(hex) {
	const h = hex.replace('#', '');
	const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h.slice(0, 6);
	const [r, g, b] = [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16) / 255);
	const max = Math.max(r, g, b);
	const min = Math.min(r, g, b);
	const l = (max + min) / 2;
	const d = max - min;
	if (d === 0) return { h: 0, s: 0, l };
	const s = d / (1 - Math.abs(2 * l - 1));
	let hue = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
	hue *= 60;
	if (hue < 0) hue += 360;
	return { h: hue, s, l };
}
/** A warm, saturated colour: it could read as decision orange or alert red. */
const warm = (hex) => {
	const c = hsl(hex);
	return c.s > 0.35 && c.l > 0.25 && (c.h < 50 || c.h > 330);
};

// ── 1. illustrations ─────────────────────────────────────────────────────────

const ills = listSvgs(ILL).filter((f) => f.endsWith('.svg'));
const groups = { events: 19, vehicles: 10, agencies: 8, empty: 5, onboarding: 3 };
for (const [g, n] of Object.entries(groups)) {
	const have = ills.filter((f) => path.basename(path.dirname(f)) === g).length;
	ok(`illustrations/${g}: ${n} files`, have === n, `${have}`);
}
const issues = [];
for (const f of ills) {
	const s = readFileSync(f, 'utf8');
	const rel = path.relative(ILL, f);
	if (!/<svg\b[^>]*\brole="img"/.test(s) || !(/<svg\b[^>]*\baria-label="[^"]{3,}"/.test(s) || /<title>[^<]{3,}<\/title>/.test(s))) issues.push(`${rel}: no role/label`);
	if (/<image\b/i.test(s)) issues.push(`${rel}: <image>`);
	if (/<text\b/i.test(s)) issues.push(`${rel}: <text>`);
	if (/<script\b|on\w+=|javascript:/i.test(s)) issues.push(`${rel}: script`);
	if (/(href|src)="(https?:|\/\/)/i.test(s)) issues.push(`${rel}: external ref`);
	for (const m of s.matchAll(/#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b/g)) {
		const hex = m[0].toUpperCase();
		if (hex === '#FF9F43' || hex === '#FF5C61' || warm(hex)) issues.push(`${rel}: warm colour ${hex}`);
	}
	if (/\b(person|people|face|crowd-of-people|human)\b/i.test(s.replace(/aria-label="[^"]*"/g, ''))) issues.push(`${rel}: person word`);
}
ok('every illustration: role="img" + label, no <image>, no <text>, no script, no external ref, no orange/red', issues.length === 0, issues.slice(0, 6).join(' | ') || `${ills.length} files`);
const EVENT_KINDS = ['protected_movement', 'procession', 'mass_gathering', 'race', 'ceremonial', 'egress_surge', 'emergency_evacuation', 'work_zone', 'vehicle_pursuit', 'crime_incident', 'reported_crime', 'public_disorder', 'road_accident', 'hazard', 'flooding', 'infra_failure', 'weather', 'advisory', 'green_corridor'];
const missingArt = EVENT_KINDS.filter((k) => !existsSync(path.join(ILL, 'events', `${k}.svg`)));
ok('every event kind Home draws has its tile (16 corridor kinds + weather, advisory, green corridor)', missingArt.length === 0, missingArt.join(', '));
ok('the empty states Home uses exist (all-clear, offline)', existsSync(path.join(ILL, 'empty/all-clear.svg')) && existsSync(path.join(ILL, 'empty/offline.svg')));

// ── 2. deterministic ─────────────────────────────────────────────────────────

if (existsSync(GENERATOR)) {
	const tmp = mkdtempSync(path.join(os.tmpdir(), 'v3-ill-'));
	try {
		execFileSync('python3', ['-I', '-c', `import importlib.util;spec=importlib.util.spec_from_file_location('bi', ${JSON.stringify(GENERATOR)});m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=${JSON.stringify(tmp)};m.main()`], { stdio: 'pipe' });
		const fresh = listSvgs(tmp);
		const differ = fresh.filter((f) => {
			const twin = path.join(ILL, path.relative(tmp, f));
			return !existsSync(twin) || readFileSync(twin, 'utf8') !== readFileSync(f, 'utf8');
		});
		ok('the design generator reproduces static/illustrations byte for byte', fresh.length === ills.length && differ.length === 0, differ.slice(0, 4).map((f) => path.relative(tmp, f)).join(', ') || `${fresh.length} files`);
	} catch (e) {
		ok('the design generator runs', false, String(e.message).slice(0, 200));
	} finally {
		rmSync(tmp, { recursive: true, force: true });
	}
} else {
	console.log('skip determinism — the design generator is not on this machine');
}

// ── 3. brand ─────────────────────────────────────────────────────────────────

{
	const want = ['favicon', 'veer-app-icon', 'veer-lockup-day', 'veer-lockup', 'veer-mark-day', 'veer-mark-mono', 'veer-mark', 'veer-wordmark'];
	const have = readdirSync(BRAND).filter((f) => f.endsWith('.svg')).map((f) => f.replace(/\.svg$/, '')).sort();
	ok('static/brand: the 8 files of §4.1', JSON.stringify(have) === JSON.stringify([...want].sort()), have.join(', '));
	const bad = [];
	for (const f of have) {
		const s = readFileSync(path.join(BRAND, `${f}.svg`), 'utf8');
		// the favicon is the browser tab's icon, never inline content: it carries no label
		if (f !== 'favicon' && !/aria-label="[^"]+"|<title>/.test(s)) bad.push(`${f}: unlabelled`);
		if (/<(linearGradient|radialGradient|filter)\b/i.test(s)) bad.push(`${f}: gradient/glow`);
		if (/<image\b|<script\b/i.test(s)) bad.push(`${f}: image/script`);
		for (const m of s.matchAll(/#[0-9a-fA-F]{6}\b/g)) if (warm(m[0])) bad.push(`${f}: warm ${m[0]}`);
		// the waypoint is always Veer blue: #276EF1 on night, the day theme's blue #1E54B7 on paper
		if (/veer-mark(?!-mono)|lockup|app-icon|favicon/.test(f) && !(f.endsWith('-day') ? /#1E54B7/i : /#276EF1/i).test(s)) bad.push(`${f}: waypoint not Veer blue`);
	}
	ok('brand: labelled, Veer-blue waypoint, no orange/red, no gradient or glow, no image', bad.length === 0, bad.join(' | '));
}

// ── 4. glyphs ────────────────────────────────────────────────────────────────

{
	const src = readFileSync(path.join(DECK, 'src/lib/v3/icons.ts'), 'utf8');
	const entries = [...src.matchAll(/^\t([a-zA-Z0-9]+): '([^']+)',$/gm)].map((m) => [m[1], m[2]]);
	ok('icons.ts: 68 glyphs (§4.4)', entries.length === 68, `${entries.length}`);
	const badPath = entries.filter(([, d]) => !/^[MmLlHhVvCcSsQqTtAaZz0-9 .,-]+$/.test(d) || !/^[Mm]/.test(d));
	ok('every glyph is valid path data', badPath.length === 0, badPath.map(([k]) => k).join(', '));
	const nums = entries.flatMap(([, d]) => (d.match(/-?\d*\.?\d+/g) ?? []).map(Number));
	ok('glyphs sit on the 24-unit grid', nums.every((n) => n >= -24 && n <= 25), `max ${Math.max(...nums)}`);
	const person = entries.filter(([k]) => /person|user|people|face|human|man|woman/i.test(k));
	ok('no person glyph (vehicles only)', person.length === 0, person.map(([k]) => k).join(', '));
	for (const need of ['home', 'map', 'decide', 'spark', 'megaphone', 'analyst', 'lock', 'flask', 'shuffle', 'eyeoff', 'shield', 'badge', 'thermal', 'cube', 'volume'])
		if (!entries.some(([k]) => k === need)) ok(`glyph ${need}`, false, 'missing');
}

// ── 5. fonts ─────────────────────────────────────────────────────────────────

{
	const v3fonts = path.join(DECK, 'static/fonts/v3');
	ok('V3 adds no font file (the deck\'s own self-hosted OFL faces serve every weight it uses)', !existsSync(v3fonts) || readdirSync(v3fonts).length === 0);
	const layout = readFileSync(path.join(DECK, 'src/routes/(v3)/+layout.svelte'), 'utf8');
	ok('the (v3) layout imports the V3 tokens, never fonts.css or the v2 tokens again', /\$lib\/v3\/tokens\.css/.test(layout) && !/fonts\.css|design\/tokens\.css/.test(layout));
	for (const f of ['OFL-Inter.txt', 'OFL-NotoSansDevanagari.txt', 'OFL-NotoSansGujarati.txt']) ok(`licence present: ${f}`, existsSync(path.join(DECK, 'static/fonts', f)));
}

// ── 6. weight ────────────────────────────────────────────────────────────────

{
	const bytes = (files) => files.reduce((n, f) => n + statSync(f).size, 0);
	const ill = bytes(ills);
	const brand = bytes(listSvgs(BRAND));
	ok('illustrations ≤ 120 KB in all, brand ≤ 16 KB', ill <= 120_000 && brand <= 16_000, `${(ill / 1024).toFixed(1)} KB + ${(brand / 1024).toFixed(1)} KB`);
}

console.log(failures ? `\n${failures} FAILED` : '\nv3-assets: ALL OK');
process.exit(failures ? 1 : 0);
