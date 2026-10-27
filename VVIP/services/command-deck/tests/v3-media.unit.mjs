/**
 * V3 imagery gate (V3-P7) — zero browser.
 *
 *   node tests/v3-media.unit.mjs
 *
 *   1. ARTWORK       static/artwork/{vehicles,events,scenes}: every event kind the deck can draw has its 16:9 key art,
 *                    every vehicle class its studio shot (and every protection class its convoy composition), the
 *                    five Home scenes exist; each SVG is labelled (role="img" + aria-label), holds no <image> (never
 *                    a photo or a camera frame), no <text> (no words in images), no script, no external reference, no
 *                    person word, no navy and no purple; each ≤ 40 KB and the set ≤ 900 KB.
 *   2. DETERMINISTIC when the generator is on this machine (redesign/v3/assets/build_artwork.py), re-running it into a
 *                    temp folder reproduces static/artwork byte for byte.
 *   3. PHOTOS        every photo row has its author, licence, licence URL, source page and credit; both sizes exist in
 *                    static/photos; static/photos/NOTICE.md names each one with its licence; nothing in static/photos
 *                    is unlisted; the photos left out for a legible mark or a face stay out.
 *   4. MARKS         every file in static/logos has a row and every row a file; NOTICE.md names each; the ownership
 *                    credit line is in the pack.
 *   5. HONESTY       a photo is drawn only by Cover.svelte (which always prints "Reference photo · not live" and the
 *                    credit); the public pages load imagery from their own origin only.
 *   6. PACKS         packs.media EN / HI / GU carry the same keys; every v3i_ key the code uses exists; HI holds no
 *                    Gujarati and GU no Devanagari; nothing left in English.
 *
 * Exits 0 with `ok <name>` lines, 1 on any failure.
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs';
import { createRequire } from 'node:module';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DECK = path.resolve(HERE, '..');
const ART = path.join(DECK, 'static/artwork');
const PHOTOS_DIR = path.join(DECK, 'static/photos');
const LOGOS_DIR = path.join(DECK, 'static/logos');
const GENERATOR = '/home/sandy050405/argus/veer/.veer-orchestration/redesign/v3/assets/build_artwork.py';
const OUT = path.join(HERE, 'artifacts', 'v3-media-bundle.mjs');

let failures = 0;
function ok(name, cond, detail = '') {
	if (cond) console.log(`ok   ${name}${detail ? ` — ${detail}` : ''}`);
	else {
		failures++;
		console.error(`FAIL ${name}${detail ? ` — ${detail}` : ''}`);
	}
}

const walk = (dir, filter = () => true) => {
	const out = [];
	const go = (d) => {
		for (const f of readdirSync(d).sort()) {
			const p = path.join(d, f);
			if (statSync(p).isDirectory()) go(p);
			else if (filter(p)) out.push(p);
		}
	};
	if (existsSync(dir)) go(dir);
	return out;
};

mkdirSync(path.dirname(OUT), { recursive: true });
const esbuild = createRequire(path.join(DECK, 'package.json'))('esbuild');
const built = await esbuild.build({
	stdin: {
		contents: [
			`export * as art from './src/lib/v3/media/art';`,
			`export * as photos from './src/lib/v3/media/photos';`,
			`export * as logos from './src/lib/v3/media/logos';`,
			`export * as packs from './src/lib/v3/media/packs.media';`,
			`export { hi } from './src/lib/v3/media/packs.media.hi';`,
			`export { gu } from './src/lib/v3/media/packs.media.gu';`,
			`export { EVENT_ART } from './src/lib/v3/home/model';`,
		].join('\n'),
		resolveDir: DECK,
		loader: 'ts',
		sourcefile: 'v3-media-entry.ts',
	},
	absWorkingDir: DECK,
	alias: { $lib: './src/lib' },
	bundle: true,
	format: 'esm',
	platform: 'node',
	outfile: OUT,
	logLevel: 'silent',
	external: ['$app/*', 'svelte', 'svelte/*'],
	define: { 'import.meta.env.SSR': 'true' },
});
ok('bundle builds (media/art, photos, logos, packs.media)', built.errors.length === 0, built.errors.map((e) => e.text).join(' | '));
const M = await import(`${pathToFileURL(OUT).href}?t=${Date.now()}`);

// ── colour helpers ───────────────────────────────────────────────────────────

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
/** Navy (a dark, saturated blue) or purple: the neutral grounds never carry either. */
const navyOrPurple = (hex) => {
	const c = hsl(hex);
	return (c.h >= 250 && c.h <= 320 && c.s > 0.25 && c.l > 0.08) || (c.h >= 205 && c.h < 250 && c.s > 0.35 && c.l < 0.3);
};

// ── 1. artwork ───────────────────────────────────────────────────────────────

const svgs = walk(ART, (p) => p.endsWith('.svg'));
const rel = (p) => path.relative(ART, p);
{
	const groups = { events: M.art.KEY_ART_KINDS.length, vehicles: M.art.VEHICLE_SHOTS.length, scenes: 5 };
	for (const [g, n] of Object.entries(groups)) {
		const have = svgs.filter((f) => path.basename(path.dirname(f)) === g).length;
		ok(`artwork/${g}: ${n} files`, have === n, `${have}`);
	}
	const missingKind = [...M.art.KEY_ART_KINDS, ...M.EVENT_ART].filter((k) => !existsSync(path.join(ART, 'events', `${M.art.keyArtKind(k)}.svg`)));
	ok('every event kind the deck draws (Home tiles, corridor and OSINT kinds) has its key art', missingKind.length === 0, missingKind.join(', ') || `${M.EVENT_ART.size} kinds`);
	const deckClasses = ['ambulance', 'auto_rickshaw', 'bus', 'car', 'fire_tender', 'patrol', 'suv', 'tempo', 'truck', 'two_wheeler', 'motorcycle', 'scooter', 'lcv', 'hgv', 'jeep', 'unknown-class'];
	const missingCls = deckClasses.filter((c) => !existsSync(path.join(ART, 'vehicles', `${M.art.vehicleShotClass(c)}.svg`)));
	ok('every vehicle class (and alias) has its studio shot; an unknown class falls back to the car', missingCls.length === 0 && M.art.vehicleShotClass('unknown-class') === 'car', missingCls.join(', '));
	const conv = ['Z+', 'Z', 'Y', 'X'].map((c) => M.art.convoyShot(c));
	ok('every protection class has its convoy composition', conv.every((c) => existsSync(path.join(ART, 'vehicles', `${c}.svg`))) && new Set(conv).size === 4, conv.join(', '));
	ok('every Home scene exists and the hour picks one', ['dawn', 'day', 'dusk', 'night', 'all-clear'].every((s) => existsSync(path.join(ART, 'scenes', `${s}.svg`))) && M.art.sceneFor(6) === 'dawn' && M.art.sceneFor(12) === 'day' && M.art.sceneFor(18) === 'dusk' && M.art.sceneFor(23) === 'night');
	const issues = [];
	for (const f of svgs) {
		const s = readFileSync(f, 'utf8');
		const r = rel(f);
		if (!/<svg\b[^>]*\brole="img"/.test(s) || !/<svg\b[^>]*\baria-label="[^"]{8,}"/.test(s)) issues.push(`${r}: no role/label`);
		if (/<image\b/i.test(s)) issues.push(`${r}: <image>`);
		if (/<text\b/i.test(s)) issues.push(`${r}: <text>`);
		if (/<script\b|\bon\w+=|javascript:/i.test(s)) issues.push(`${r}: script`);
		if (/(href|src)="(https?:|\/\/)/i.test(s) || /url\((?!#)/.test(s)) issues.push(`${r}: external ref`);
		if (/\b(person|people|face|faces|human|man|woman|men|women)\b/i.test(s)) issues.push(`${r}: person word`);
		for (const m of s.matchAll(/#[0-9a-fA-F]{6}\b/g)) if (navyOrPurple(m[0])) issues.push(`${r}: navy/purple ${m[0]}`);
		if (statSync(f).size > 40_960) issues.push(`${r}: ${(statSync(f).size / 1024).toFixed(1)} KB > 40 KB`);
	}
	ok('every artwork SVG: labelled, no <image>/<text>/script/external ref, no person word, no navy or purple, ≤ 40 KB', issues.length === 0, issues.slice(0, 6).join(' | ') || `${svgs.length} files`);
	const total = svgs.reduce((n, f) => n + statSync(f).size, 0);
	ok('the artwork set ≤ 900 KB', total <= 900 * 1024, `${(total / 1024).toFixed(1)} KB`);
}

// ── 2. deterministic ─────────────────────────────────────────────────────────

if (existsSync(GENERATOR)) {
	const tmp = mkdtempSync(path.join(os.tmpdir(), 'v3-art-'));
	try {
		execFileSync('python3', ['-I', '-c', `import importlib.util;spec=importlib.util.spec_from_file_location('ba', ${JSON.stringify(GENERATOR)});m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=${JSON.stringify(tmp)};m.main()`], { stdio: 'pipe' });
		const fresh = walk(tmp);
		const differ = fresh.filter((f) => {
			const twin = path.join(ART, path.relative(tmp, f));
			return !existsSync(twin) || readFileSync(twin, 'utf8') !== readFileSync(f, 'utf8');
		});
		ok('the generator reproduces static/artwork byte for byte', fresh.length === svgs.length && differ.length === 0, differ.slice(0, 4).map((f) => path.relative(tmp, f)).join(', ') || `${fresh.length} files`);
	} catch (e) {
		ok('the generator runs', false, String(e.message).slice(0, 200));
	} finally {
		rmSync(tmp, { recursive: true, force: true });
	}
} else {
	console.log('skip determinism — the generator is not on this machine');
}

// ── 3. photos ────────────────────────────────────────────────────────────────

{
	const rows = M.photos.PHOTOS;
	const notice = existsSync(path.join(PHOTOS_DIR, 'NOTICE.md')) ? readFileSync(path.join(PHOTOS_DIR, 'NOTICE.md'), 'utf8') : '';
	const bad = [];
	for (const p of rows) {
		for (const k of ['author', 'license', 'licenseUrl', 'source', 'credit', 'title', 'place']) if (!p[k] || !String(p[k]).trim()) bad.push(`${p.slug}: no ${k}`);
		if (!/^https:\/\/creativecommons\.org\/|^https:\/\/commons\.wikimedia\.org\//.test(p.licenseUrl)) bad.push(`${p.slug}: licence URL`);
		if (!p.credit.includes(p.license)) bad.push(`${p.slug}: credit without licence`);
		for (const w of [640, 1600]) if (!existsSync(path.join(PHOTOS_DIR, `${p.slug}-${w}.webp`))) bad.push(`${p.slug}-${w}.webp missing`);
		if (!notice.includes(`**${p.slug}**`) || !notice.includes(p.license)) bad.push(`${p.slug}: not in NOTICE`);
	}
	ok(`every photo (${rows.length}) has author, licence, licence URL, source and credit; both sizes exist; NOTICE names it`, rows.length >= 15 && bad.length === 0, bad.slice(0, 6).join(' | '));
	const listed = new Set(rows.flatMap((p) => [`${p.slug}-640.webp`, `${p.slug}-1600.webp`]));
	const stray = readdirSync(PHOTOS_DIR).filter((f) => f !== 'NOTICE.md' && !listed.has(f));
	ok('nothing in static/photos is unlisted', stray.length === 0, stray.join(', '));
	const excluded = ['city-traffic-street', 'auto-rickshaws-old-city', 'sg-highway-iscon-flyover', 'monsoon-waterlogged-street'];
	ok('the photos with a legible registration mark, a face or a passenger stay out', excluded.every((s) => !rows.some((p) => p.slug === s) && !existsSync(path.join(PHOTOS_DIR, `${s}-640.webp`))));
	ok('a riverfront point finds its photo; a far point finds none', M.photos.photoNear(72.5723, 23.0341, 900, 12)?.place === 'riverfront' && M.photos.photoNear(72.9, 23.4, 900, 12) === null);
	const bytes = readdirSync(PHOTOS_DIR).reduce((n, f) => n + statSync(path.join(PHOTOS_DIR, f)).size, 0);
	ok('static/photos ≤ 6 MB', bytes <= 6 * 1024 * 1024, `${(bytes / 1048576).toFixed(2)} MB`);
}

// ── 4. marks ─────────────────────────────────────────────────────────────────

{
	const rows = M.logos.MARKS;
	const files = readdirSync(LOGOS_DIR).filter((f) => f !== 'NOTICE.md');
	const notice = existsSync(path.join(LOGOS_DIR, 'NOTICE.md')) ? readFileSync(path.join(LOGOS_DIR, 'NOTICE.md'), 'utf8') : '';
	const noRow = files.filter((f) => !rows.some((m) => m.src === `/logos/${f}`));
	const noFile = rows.filter((m) => !existsSync(path.join(DECK, 'static', m.src)));
	const noNotice = rows.filter((m) => !notice.includes(`**${m.key.replace(/_/g, '-')}**`));
	ok(`every mark file has a row and every row a file (${rows.length})`, rows.length > 0 && noRow.length === 0 && noFile.length === 0, [...noRow, ...noFile.map((m) => m.key)].join(', '));
	ok('NOTICE.md names every mark and carries the ownership line', noNotice.length === 0 && /belong to their owners/.test(notice) && /not affiliated with or endorsed by/.test(notice), noNotice.map((m) => m.key).join(', '));
	ok('the roles the deck speaks of find their marks (police, 108, municipal, disaster, Sachet, IMD)', ['police', '108', 'municipal', 'disaster'].every((r) => M.logos.markFor(r)) && M.logos.sourceMark('sachet.ndma.gov.in')?.key === 'ndma_sachet' && M.logos.sourceMark('mausam.imd.gov.in')?.key === 'imd');
	ok('fire, ERSS 112 and the volunteers keep the generic badge (no mark on file)', ['fire', '112', 'jan_rakshak', 'volunteers'].every((r) => M.logos.markFor(r) === null));
	ok('the ownership credit line is in the pack', /belong to their owners\. Veer is a prototype and is not affiliated with or endorsed by them\./.test(M.packs.MEDIA_PACKS.en.v3i_marks_credit));
}

// ── 5. honesty ───────────────────────────────────────────────────────────────

{
	const code = walk(path.join(DECK, 'src'), (p) => /\.(svelte|ts)$/.test(p));
	const drawsPhoto = code.filter((f) => !/media\/(photos|photos\.data|Cover)\.(ts|svelte)$/.test(f) && /photoSrc(set)?\(|\/photos\/[a-z0-9-]+-(640|1600)\.webp/.test(readFileSync(f, 'utf8')));
	ok('a photo is drawn only by Cover.svelte', drawsPhoto.length === 0, drawsPhoto.map((f) => path.relative(DECK, f)).join(', '));
	const cover = readFileSync(path.join(DECK, 'src/lib/v3/media/Cover.svelte'), 'utf8');
	const photoBranch = cover.slice(cover.indexOf('{#if photo}'), cover.indexOf('{:else}'));
	ok('Cover prints "Reference photo · not live" and the credit on every photo', /v3i_ref_photo/.test(photoBranch) && /photo\.credit/.test(photoBranch) && !/\{#if[^}]*compact[^}]*\}[\s\S]*v3i_ref_photo/.test(photoBranch));
	const pub = [...walk(path.join(DECK, 'src/routes/(public)'), (p) => /\.svelte$/.test(p)), ...walk(path.join(DECK, 'src/lib/citizen'), (p) => /\.svelte$/.test(p)), ...walk(path.join(DECK, 'src/lib/v3/public'), (p) => /\.svelte$/.test(p))];
	const offsite = pub.filter((f) => /<img[^>]+src="(https?:)?\/\//.test(readFileSync(f, 'utf8')));
	ok('public pages load imagery from their own origin only', offsite.length === 0, offsite.map((f) => path.relative(DECK, f)).join(', '));
}

// ── 6. packs ─────────────────────────────────────────────────────────────────

{
	const en = Object.keys(M.packs.MEDIA_PACKS.en);
	const hi = Object.keys(M.hi);
	const gu = Object.keys(M.gu);
	const same = (a, b) => a.length === b.length && a.every((k) => b.includes(k));
	ok('packs.media: EN / HI / GU carry the same keys', same(en, hi) && same(en, gu), `${en.length} keys`);
	ok('packs.media: every key starts with v3i_', en.every((k) => k.startsWith('v3i_')));
	const code = walk(path.join(DECK, 'src'), (p) => /\.(svelte|ts)$/.test(p) && !/packs\.media/.test(p));
	const used = new Set();
	const prefixes = new Set();
	for (const f of code) {
		const s = readFileSync(f, 'utf8');
		for (const m of s.matchAll(/['"`](v3i_[a-z0-9_-]+)['"`]/g)) used.add(m[1]);
		for (const m of s.matchAll(/`(v3i_[a-z0-9_]+)\$\{/g)) prefixes.add(m[1]);
	}
	const missing = [...used].filter((k) => !en.includes(k));
	ok('every literal v3i_ key the code uses exists in the pack', missing.length === 0, missing.join(', ') || `${used.size} used`);
	const dyn = { v3i_scene_: ['dawn', 'day', 'dusk', 'night', 'all-clear'], v3i_cls_: M.art.VEHICLE_SHOTS, v3i_agency_: ['police', 'ems', 'municipal', 'disaster', 'imd', 'metro', 'brts', 'amts', 'osm', 'citizens'] };
	const dynMissing = Object.entries(dyn).flatMap(([p, list]) => list.map((x) => `${p}${x}`).filter((k) => !en.includes(k)));
	ok('every dynamic v3i_ key (scenes, vehicle classes, agencies) exists', dynMissing.length === 0 && [...prefixes].every((p) => p in dyn), dynMissing.join(', ') || [...prefixes].join(', '));
	const text = (v) => (typeof v === 'function' ? v('‹x›', '‹y›') : v);
	const untranslated = (pack) => en.filter((k) => text(M.packs.MEDIA_PACKS.en[k]) === text(pack[k]) && /[a-z]{4}/.test(text(M.packs.MEDIA_PACKS.en[k])));
	const u = [...untranslated(M.hi), ...untranslated(M.gu)];
	ok('HI and GU are translated (no EN sentence left in place)', u.length === 0, u.slice(0, 6).join(', '));
	const leakHi = Object.values(M.hi).map(text).filter((s) => /[઀-૿]/.test(String(s)));
	const leakGu = Object.values(M.gu).map(text).filter((s) => /[ऀ-ॿ]/.test(String(s)));
	ok('no Gujarati in the HI pack and no Devanagari in the GU pack', leakHi.length === 0 && leakGu.length === 0);
}

console.log(failures ? `\n${failures} FAILED` : '\nv3-media: ALL OK');
process.exit(failures ? 1 : 0);
