/**
 * FIX-E-PERF2 unit test (round 2) — the per-language packs, their loading on
 * the SHIPPED (production) path, and the split icon set.
 *
 *   node tests/perf2.unit.mjs                       # the checks
 *   node tests/perf2.unit.mjs --print-golden <src>  # recompute the golden from a tree (review aid)
 *
 * 1. Strings never change, per module × language × copy. PACK_GOLDEN below
 *    was computed ONCE from main's pre-split packs (`--print-golden` on main's
 *    src, reviewed) and is written into this file: for every one of the 16
 *    pack modules and each language, the key count and a sha256 of the
 *    canonical (key, initializer source text) list. Every copy is checked ON
 *    ITS OWN against it — EN in the base module; HI and GU in the `.hi.ts` /
 *    `.gu.ts` modules (the copy that runs: the server, vite dev, the tests and
 *    the production browser all import it); and, for the four packs two AST
 *    readers still read as text (packs, packs.map, packs.workspace,
 *    packs.agent), the never-registered text mirror in the base module. No
 *    merging by key name, no git: a changed value, a dropped or added key in
 *    any one copy fails. The other twelve base modules hold no HI/GU literal
 *    at all (one source of truth).
 * 2. Loading on the production path. The pack modules, lib/i18n/load.ts and
 *    the ops store are bundled with the PRODUCTION client defines
 *    (process.env.NODE_ENV='production', import.meta.env.SSR=false) — the
 *    branch that registers every language eagerly folds away exactly as in
 *    the shipped build — and each path is driven in a fresh module instance:
 *      a. a switch (`ensureLang`) lands HI, then GU, for EVERY one of the 16
 *         modules (one sampled key per module, compared with its .hi/.gu
 *         value); while a chunk is in flight t() answers EN, never a raw key;
 *         the registration hook fires (the re-render signal);
 *      b. the cold path: `<html lang="gu">` set before the modules evaluate →
 *         every module's GU strings are in before evaluation finishes (what
 *         hydration waits for), HI is not fetched;
 *      c. the ops store's `lang` setter alone, and `adoptLangCookie()` alone
 *         (veer_lang cookie), each land the language for all 16 modules;
 *      d. a real Svelte 5 `$effect` reading t() re-runs once the chunk lands
 *         (svelte compiled for the client; flushSync), showing HI.
 * 3. Icons. `ICONS_16` / `ICONS_20` are complete, frozen and in main's order
 *    with main's path data (golden hashes); in the production bundle
 *    `isIconName` knows all 206 names before anything loads, a deferred glyph
 *    has no paths until `loadRestIcons()` lands and then every name resolves
 *    at 16 and 20 px. The first-paint half is EXACTLY the pinned
 *    first-viewport sets plus the map-marker glyphs (every KIND_ICON /
 *    EVENT_KIND_ICON glyph) plus the canvas's Layers / Legend panel glyphs. With a production build present, the server
 *    render of `/`, `/ops` and `/gods-eye` (EN/HI/GU) is collected and every
 *    glyph it draws must be in the first-paint half and in that route's
 *    pinned set (tests/perf2-prod-smoke.mjs checks the browser's first
 *    viewport for blank glyphs).
 *
 * Exits 0 with `ok` lines, 1 on any failure.
 */

import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { WORKSPACE } from './lib/routes.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DECK = path.resolve(HERE, '..');
const require = createRequire(path.join(DECK, 'package.json'));
const ts = require('typescript');

const MODULES = [
	'strings', 'strings.ops', 'strings.citizen', 'packs', 'packs.ui', 'packs.wall', 'packs.views', 'packs.decisions',
	'packs.dss', 'packs.analysis', 'packs.assistant', 'packs.osint', 'packs.corridor', 'packs.map', 'packs.workspace', 'packs.agent',
];
/** The four packs tests/thermal-toolbar.unit.mjs and tests/omnibar-lookup.unit.mjs read as text (FIX-E-PERF2 blocked request). */
const MIRRORED = new Set(['packs', 'packs.map', 'packs.workspace', 'packs.agent']);
const LANGS = ['en', 'hi', 'gu'];

// ── the canonical form of one pack literal ───────────────────────────────────

function unwrap(n) {
	while (n && (ts.isAsExpression(n) || ts.isSatisfiesExpression?.(n) || ts.isParenthesizedExpression(n))) n = n.expression;
	return n;
}

/** Top-level `[export] const <name> = { … }` object literals of a file, by name. */
function packLiterals(file) {
	const sf = ts.createSourceFile(file, readFileSync(file, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
	const out = {};
	for (const st of sf.statements) {
		if (!ts.isVariableStatement(st)) continue;
		for (const d of st.declarationList.declarations) {
			const init = unwrap(d.initializer);
			if (ts.isIdentifier(d.name) && init && ts.isObjectLiteralExpression(init)) out[d.name.text] = { sf, obj: init };
		}
	}
	return out;
}

/** key → { text (whitespace-normalised initializer source), value (a plain string literal's value, else null) }. */
function entries({ sf, obj }) {
	const map = new Map();
	let odd = 0;
	for (const p of obj.properties) {
		if (!ts.isPropertyAssignment(p) || !(ts.isIdentifier(p.name) || ts.isStringLiteral(p.name))) {
			odd++;
			continue;
		}
		const init = p.initializer;
		const lit = ts.isStringLiteral(init) || ts.isNoSubstitutionTemplateLiteral(init) ? init.text : null;
		map.set(p.name.text, { text: init.getText(sf).replace(/\s+/g, ' ').trim(), value: lit, dup: map.has(p.name.text) });
	}
	return { map, odd };
}

function digest(lit) {
	const { map, odd } = entries(lit);
	const lines = [...map.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)).map(([k, v]) => `${k}\u0000${v.text}`);
	return { count: map.size, sha: createHash('sha256').update(lines.join('\n')).digest('hex'), odd };
}

// ── --print-golden: recompute the table from a tree (main's pre-split src) ───

if (process.argv[2] === '--print-golden') {
	const dir = path.join(process.argv[3], 'lib/i18n');
	const table = {};
	for (const m of MODULES) {
		const lits = packLiterals(path.join(dir, `${m}.ts`));
		table[m] = {};
		for (const l of LANGS) {
			if (!lits[l]) throw new Error(`${m}: no const ${l} literal`);
			const d = digest(lits[l]);
			table[m][l] = [d.count, d.sha];
		}
	}
	console.log(JSON.stringify(table, null, '\t'));
	process.exit(0);
}

/**
 * The golden: main's packs before the split (VVIP main, the base this work
 * package is cut against), per module × language: [key count, sha256 of the
 * sorted (key, initializer source) list]. Recompute with --print-golden.
 */
const PACK_GOLDEN = {
	'strings': { en: [146, '9465f1f9a6e37296bedca8e42f0dfbb911b3fd9e80f7c34f7d8d325f6871cad7'], hi: [146, '7161bfb5cc17217a89a2bfcfe7a052d89b5fde5c98aa3d1137e84772b4c24315'], gu: [146, '960d18db665f80c78f5febfd6548890454f59105ce4e4aec34faa7be4f44887d'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'strings.ops': { en: [438, 'fc305b239389dcd54b2094356ae5c5327b7d4823cc14954982528a73d8e74473'], hi: [438, '876bf95fe690de10dd2d0c33a69593421d93a9cec65a06da911276257e9ca743'], gu: [438, '51797e532067896cbca356f6087af372d19ddc8da446b20d5fed6393ac97d818'] }, // 2026-10-26: bandSimulatedTag/bandSourceStale sentence case (UI-S7B blockers B2/B3) // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'strings.citizen': { en: [203, 'f5c1cc01ff9ddc182849a728a3bc5e80cbec780ddf64c79c922770c16adeaf4d'], hi: [203, '16d329515764e3953f1a3761c70e09b369671f17ccd7d959b9e23b4c36961e49'], gu: [203, '992abc1a25eb9edf52df972446b3bc4fc3b191fde9122dfe522570804ecbf0c6'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs': { en: [390, '348a559b403a8bd68b34c82f5d16379a3b82b40236b292ef4f45c43894541136'], hi: [390, '74df76908ac89e670f52121bf85d1939ddc4b7ce9dbc1740bb4487891ec16a17'], gu: [390, 'a445e6b993e2d1cfaeb76c450390000b2da04c03c99f44b988b3add229a440a4'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs.ui': { en: [77, '336571b9c2618b1f5a04460921c2071561d77c328e72959512b7757c5ab10e10'], hi: [77, '0b50bf2c25811a196aad26e73662f949fee8b30f3aab17d89ca0e55f4dbfc376'], gu: [77, 'f7b2623e4408850a907643f51635dabe974dc11511d9dc52856fd15d104c70cd'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs.wall': { en: [358, '8c0fea94361d6c25c464e0c7d213e36e453af40d947398ebc90a480a63a363c5'], hi: [358, '598aa1bf80f8aecc3c98e6b71f06876a9a12dbf454994c933257409a2f9c47b1'], gu: [358, '4fd403c06186a4ae5c728f134df748832a288b4107d44af99d37bc8688e20cf4'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs.views': { en: [229, '98a28fe74628344d747b42ff18af4fe7018a25dff31f8ee374e0d4e972a7ba08'], hi: [229, '518219e53accd6c8b5f7b4265a8fd00050ef6b1cb7c293e3e68f2aa79d57b6c2'], gu: [229, '67e6b11631a7a7863858971fb5344fe510c9a0d54887b104f861a5e034cb03d8'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs.decisions': { en: [307, '45876a3742e2f556ef013ae1ee7406c923aee7e0966b922bd2f63005be942c51'], hi: [307, 'a7092f46cee0d444173af21aacdc758e352ffccec6a797c46c7f1feaa9bc9b4a'], gu: [307, '84a3615ed25c96436d1bd41d4a8f13e5cd258f04d044bb8bb5819da2cc0f7799'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs.dss': { en: [115, 'f7f9d57a192639468f37e046b946feba9c83b637674da619f955e4c3f41175db'], hi: [115, 'b94477972ba2bd64b5afcb5998f9169ce46b4dda9d53790d1589d94f42723c99'], gu: [115, '9741c77deb9a73991124b5e71770a690ad7276ece2e0ea29b5872bff47f038aa'] },
	'packs.analysis': { en: [168, 'ab0a6e190aa07f7dcf5667963b48be3f1638c5a3da16ec70f13a5a4e48673a5b'], hi: [168, '5c7b4f06eee1a31206925b68f5fa8dd5fe7dbe3154d9bb3a443e479a3f9988c1'], gu: [168, '8552c74e03480a8e2d3abca93e7485888cea3af00c563e3f54498c83826d6091'] },
	'packs.assistant': { en: [38, '6b99c8c3d21422edb6ef0439757546e1c1e1180e1b02905c8ff29e4883a4e644'], hi: [38, '9e3f67f9f2c7365c3ca4170c0f2a95de2a79bdc124fcaf5de883b91da511becb'], gu: [38, '238a9b426148c0d2d0ad238303d324afb489ee15f156ca4d9769dd92ee1a22d2'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs.osint': { en: [72, '5249f6dddfc0d275dfe9e384bdc6ace5e28c1c9a82394960d80465c5e5c1786f'], hi: [72, '634f83c718f910d8b89ca8f8a2df497bdae2eb5dfe7ef04bec766db6d40ae0b7'], gu: [72, 'e4760eb2b15f592c97077d143691a249860dc6a9b52276ce63bd6d9498f80fc4'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs.corridor': { en: [81, '36deb937e8785adc552b58eccfaeb0f7e13fe2863a1c52443a6da398f97a82b9'], hi: [81, '38d17c10c64a8fc74a8b45ea83c4f17137cfeec2cf9926e428f422f9e30c8424'], gu: [81, '2014a7b4af1b602944e15246bbcea8ca4555330df1051429a669dbfcfe1730b4'] },
	'packs.map': { en: [101, '6cf7c2b55e7e1d74be3bf846fc644d5e67fc6a6f83650e92a03ed5409a03abb7'], hi: [101, '291c2d552140735837313581834865e3740d1a663d56cbf3d3e1ef311347413f'], gu: [101, '2bc130febb6a97f0508ecd030787b8afa4ba65164134f4c62f6a74166dfb719f'] }, // 2026-10-27: + map_imagery_not_live (the honest imagery chip on the Analyst city map; EN/HI/GU together)
	'packs.workspace': { en: [436, '85f66aca9a0739ed02895295ee15af72bbc67cab265c60f6a5dc63c9243b6fee'], hi: [436, 'cecca57d10d54cc34f8137f35566c85e3be150878e0e746b4410d7f5d6df6445'], gu: [436, '122d29ae2dd1b842e01f9b99d5dbb7638185c352dfb116cb7bc2d6367d57e308'] }, // 2026-10-26 FIX-H-DECK: audit copy fixes (F-UI, F-HONEST COPY-*, FIX-G-BRAIN/ORACLE deck items; EN/HI/GU together)
	'packs.agent': { en: [54, 'f4d6b1c26343ac2658531c768696bb70968154b45ee5bb5ec67c41a05b22b215'], hi: [54, '1363a21da89e67cd944438797c8ba76d47180416f72a3f155a9789ce9b1767b6'], gu: [54, '2df614bc41bd7d21909df4b55b3aaf433e3fce4c506151671719d538b276242e'] },
};

/**
 * The golden icon tables: main's ICONS_16 / ICONS_20 before the split — the
 * name count, a sha256 of the names in table order, and a sha256 of the
 * name+paths list in table order.
 */
const ICON_GOLDEN = {
	n16: 206,
	order16: '6522ab22c7e4f7de6d82dc1f59e82a866065145f0c92e6859f8eb575cca6985d',
	paths16: 'c987a82ad9cf052a81a006a5b6d06f31542ad85347fe467b4a3313a9529d4f16',
	n20: 24,
	paths20: '06aa6824a60a3def1800f6c4f8e7de0e26f06ff239e889c8e601d01dedbba5d2',
};

let failures = 0;
function ok(name, cond, detail = '') {
	if (cond) console.log(`ok   ${name}${detail ? ` — ${detail}` : ''}`);
	else {
		failures++;
		console.error(`FAIL ${name}${detail ? ` — ${detail}` : ''}`);
	}
}

const I18N = path.join(DECK, 'src/lib/i18n');

// ── 1. strings, per module × language × copy ─────────────────────────────────

/** One sampled key per module (a plain string in all three languages, translated), with its HI and GU values. */
const SAMPLE = {};
for (const m of MODULES) {
	const base = packLiterals(path.join(I18N, `${m}.ts`));
	const copies = [['en', 'base module', base.en]];
	for (const l of ['hi', 'gu']) {
		const f = path.join(I18N, `${m}.${l}.ts`);
		copies.push([l, `${m}.${l}.ts (the copy that runs)`, existsSync(f) ? packLiterals(f)[l] : undefined]);
		// the text mirror may go once the two AST readers read the per-language modules (blocked request): while it exists it is pinned too
		if (MIRRORED.has(m) && base[l]) copies.push([l, 'base-module text mirror', base[l]]);
	}
	for (const [l, where, lit] of copies) {
		const want = PACK_GOLDEN[m]?.[l];
		if (!lit) {
			ok(`strings: ${m} ${l} — ${where} present`, false, 'no such object literal');
			continue;
		}
		const d = digest(lit);
		ok(
			`strings: ${m} ${l} — ${where} matches main (${d.count} keys)`,
			!!want && d.count === want[0] && d.sha === want[1] && d.odd === 0,
			want ? `count ${d.count}/${want[0]} sha ${d.sha.slice(0, 12)}/${want[1].slice(0, 12)}${d.odd ? ` · ${d.odd} non-literal members` : ''}` : 'no golden',
		);
	}
	if (!MIRRORED.has(m)) ok(`strings: ${m} base module holds no HI/GU literal (one source of truth)`, !base.hi && !base.gu);
	const en = base.en && entries(base.en).map;
	const hi = existsSync(path.join(I18N, `${m}.hi.ts`)) ? entries(packLiterals(path.join(I18N, `${m}.hi.ts`)).hi).map : new Map();
	const gu = existsSync(path.join(I18N, `${m}.gu.ts`)) ? entries(packLiterals(path.join(I18N, `${m}.gu.ts`)).gu).map : new Map();
	const key = en && [...en.keys()].sort().find((k) => en.get(k).value && hi.get(k)?.value && gu.get(k)?.value && hi.get(k).value !== en.get(k).value && gu.get(k).value !== en.get(k).value);
	if (key) SAMPLE[m] = { key, en: en.get(key).value, hi: hi.get(key).value, gu: gu.get(key).value };
	ok(`strings: ${m} has a sampled key for the loading checks`, !!key, key ?? 'none');
}
for (const m of MIRRORED) {
	const src = readFileSync(path.join(I18N, `${m}.ts`), 'utf8');
	const mirror = /\nconst (hi|gu)\b/.test(src);
	ok(
		`strings: ${m}'s text mirror (if still present) is never registered — astTextMirror declared, never called`,
		!mirror || (/function astTextMirror\(\)/.test(src) && (src.match(/astTextMirror\s*\(/g) ?? []).length === 1 && !/registerPack\('(hi|gu)', (hi|gu)\)/.test(src.replace(/function astTextMirror\(\)[\s\S]*?\n\}/, ''))),
		mirror ? 'mirror present' : 'no mirror',
	);
}
// the samples must be distinct keys across modules so each probes its own module
const sampleKeys = Object.values(SAMPLE).map((s) => s.key);
ok('strings: the 16 sampled keys are distinct (each probes its own module)', new Set(sampleKeys).size === sampleKeys.length && sampleKeys.length === 16, sampleKeys.length + ' keys');

// ── 2. loading on the production path ────────────────────────────────────────

const esbuild = require('esbuild');
const OUT_DIR = process.env.PERF2_UNIT_OUT ?? path.join(os.tmpdir(), 'veer-perf2-unit');
mkdirSync(OUT_DIR, { recursive: true });
const PROD_DEFINE = { 'process.env.NODE_ENV': '"production"', 'import.meta.env.SSR': 'false', 'import.meta.env.DEV': 'false', 'import.meta.env.PROD': 'true' };
const stubApp = {
	name: 'stub-app',
	setup(b) {
		b.onResolve({ filter: /^\$(app|env)\// }, (a) => ({ path: a.path, namespace: 'stub-app' }));
		b.onLoad({ filter: /.*/, namespace: 'stub-app' }, () => ({ contents: 'export const browser = false, dev = false, building = false; export const goto = async () => {}; export const page = {}; export const navigating = {}; export const env = {};', loader: 'js' }));
	},
};
const IMPORTS = MODULES.map((m) => `import './src/lib/i18n/${m}';`).join('\n');

async function bundle(name, contents, extra = {}) {
	const outfile = path.join(OUT_DIR, `${name}.mjs`);
	const r = await esbuild.build({
		stdin: { contents, resolveDir: DECK, loader: 'ts', sourcefile: `${name}-entry.ts` },
		absWorkingDir: DECK,
		alias: { $lib: './src/lib' },
		bundle: true,
		format: 'esm',
		platform: 'node',
		define: PROD_DEFINE,
		outfile,
		logLevel: 'silent',
		loader: { '.svelte': 'empty' },
		plugins: [stubApp],
		...extra,
	});
	ok(`bundle ${name} builds with the production client defines`, r.errors.length === 0, `${r.errors.length} errors`);
	return outfile;
}
let instance = 0;
const fresh = (file) => import(`${pathToFileURL(file).href}?i=${++instance}`);

// runes as identity macros for the stores (as tests/wall.unit.mjs runs them)
globalThis.$state = Object.assign((v) => v, { raw: (v) => v, snapshot: (v) => v });
globalThis.$derived = Object.assign((v) => v, { by: (f) => f() });
globalThis.$effect = Object.assign(() => {}, { root: () => () => {}, pre: () => {} });

const covered = (t, lang) => MODULES.filter((m) => SAMPLE[m] && t(lang, SAMPLE[m].key) === SAMPLE[m][lang]);
const missingOf = (t, lang) => MODULES.filter((m) => !SAMPLE[m] || t(lang, SAMPLE[m].key) !== SAMPLE[m][lang]);
const settle = async (cond, ms = 3000) => {
	const end = Date.now() + ms;
	while (!cond() && Date.now() < end) await new Promise((r) => setTimeout(r, 10));
	return cond();
};

const LOADER = await bundle('perf2-loader', `${IMPORTS}\nexport * as L from './src/lib/i18n/load';\nexport { t } from './src/lib/i18n/strings';\n`);
{
	// a. a switch
	delete globalThis.document;
	delete globalThis.window;
	const { L, t } = await fresh(LOADER);
	let bumps = 0;
	L.setPacksRegisteredHook(() => bumps++);
	const preHi = covered(t, 'hi');
	ok('prod path: nothing but EN is registered before any language is asked for (the eager branch folded away)', preHi.length === 0, preHi.join(', ') || 'none in');
	const flight = L.ensureLang('hi');
	const during = MODULES.filter((m) => SAMPLE[m] && t('hi', SAMPLE[m].key) !== SAMPLE[m].en && t('hi', SAMPLE[m].key) !== SAMPLE[m].hi);
	ok('prod path: while the HI chunks are in flight t() answers EN — never a raw key', during.length === 0, during.join(', ') || 'EN fallback everywhere');
	await flight;
	ok('prod path: ensureLang("hi") lands HI for all 16 pack modules', missingOf(t, 'hi').length === 0, missingOf(t, 'hi').join(', ') || '16/16');
	ok('prod path: GU is not fetched by a HI switch', covered(t, 'gu').length === 0, covered(t, 'gu').join(', ') || 'none');
	ok('prod path: every landing fires the re-render signal (setPacksRegisteredHook)', bumps >= 16, `${bumps} signals`);
	await L.ensureLang('gu');
	ok('prod path: ensureLang("gu") lands GU for all 16 pack modules', missingOf(t, 'gu').length === 0, missingOf(t, 'gu').join(', ') || '16/16');
	const before = bumps;
	await L.ensureLang('hi');
	ok('prod path: a repeat call is free (no re-fetch, no extra signal)', bumps === before);
}
{
	// b. the cold path: the document's language, before the modules finish evaluating. Its own CODE-SPLIT build:
	// each language chunk is a separate file, so a chunk that is fetched but not awaited is still out when the
	// import resolves (an in-bundle chunk would land within the same microtask run and hide a missing await)
	const coldDir = path.join(OUT_DIR, 'cold');
	const coldEntry = path.join(OUT_DIR, 'perf2-cold-entry.ts');
	writeFileSync(coldEntry, MODULES.map((m) => `import '${path.join(DECK, 'src/lib/i18n', m)}';`).join('\n') + `\nexport { t } from '${path.join(DECK, 'src/lib/i18n/strings')}';\n`);
	const r = await esbuild.build({ entryPoints: { cold: coldEntry }, absWorkingDir: DECK, alias: { $lib: './src/lib' }, bundle: true, splitting: true, format: 'esm', platform: 'node', define: PROD_DEFINE, outdir: coldDir, outExtension: { '.js': '.mjs' }, logLevel: 'silent', plugins: [stubApp] });
	ok('bundle perf2-cold (code-split: one file per language chunk) builds with the production client defines', r.errors.length === 0, `${r.errors.length} errors`);
	globalThis.window = { addEventListener() {} };
	globalThis.document = { documentElement: { lang: 'gu' }, cookie: '', querySelectorAll: () => [] };
	const { t } = await import(pathToFileURL(path.join(coldDir, 'cold.mjs')).href);
	ok('cold path: <html lang="gu"> → every module\'s GU strings are in when the modules finish evaluating', missingOf(t, 'gu').length === 0, missingOf(t, 'gu').join(', ') || '16/16');
	ok('cold path: only the document\'s language is fetched (no HI)', covered(t, 'hi').length === 0, covered(t, 'hi').join(', ') || 'none');
	delete globalThis.document;
	delete globalThis.window;
}

const STORE = await bundle('perf2-store', `${IMPORTS}\nexport { ops } from './src/lib/ops/store.svelte';\nexport { t } from './src/lib/i18n/strings';\n`);
{
	// c. the ops store's setter alone
	const { ops, t } = await fresh(STORE);
	ok('store: before a switch, no HI module is in', covered(t, 'hi').length === 0);
	ops.lang = 'hi';
	await settle(() => missingOf(t, 'hi').length === 0);
	ok('store: the `lang` setter alone lands HI for all 16 pack modules', missingOf(t, 'hi').length === 0, missingOf(t, 'hi').join(', ') || '16/16');
}
{
	// c. adoptLangCookie() alone
	const { ops, t } = await fresh(STORE);
	globalThis.document = { documentElement: { lang: 'en' }, cookie: 'veer_lang=gu', querySelectorAll: () => [] };
	ops.adoptLangCookie();
	await settle(() => missingOf(t, 'gu').length === 0);
	ok('store: adoptLangCookie() alone (veer_lang=gu) lands GU for all 16 pack modules', ops.lang === 'gu' && missingOf(t, 'gu').length === 0, `lang=${ops.lang}; missing ${missingOf(t, 'gu').join(', ') || 'none'}`);
	delete globalThis.document;
}

{
	// d. a real Svelte 5 effect re-runs when the chunk lands
	const { compileModule } = require('svelte/compiler');
	// a virtual client-compiled module: one $effect that reads t()
	const PROBE_SRC = `import { t } from '$lib/i18n/strings';\nexport function watch(lang, key, out) {\n\treturn $effect.root(() => {\n\t\t$effect(() => {\n\t\t\tout.push(t(lang, key));\n\t\t});\n\t});\n}\n`;
	const runes = {
		name: 'svelte-client-runes',
		setup(b) {
			b.onResolve({ filter: /^perf2-probe$/ }, () => ({ path: 'perf2-probe.svelte.js', namespace: 'perf2-probe' }));
			b.onLoad({ filter: /.*/, namespace: 'perf2-probe' }, () => ({ contents: compileModule(PROBE_SRC, { filename: 'perf2-probe.svelte.js', generate: 'client', dev: false }).js.code, loader: 'js', resolveDir: DECK }));
			b.onLoad({ filter: /\.svelte\.(ts|js)$/ }, async (a) => {
				const src = readFileSync(a.path, 'utf8');
				const plain = a.path.endsWith('.ts') ? (await esbuild.transform(src, { loader: 'ts' })).code : src;
				return { contents: compileModule(plain, { filename: a.path, generate: 'client', dev: false }).js.code, loader: 'js', resolveDir: path.dirname(a.path) };
			});
		},
	};
	let R = null;
	try {
		const file = await bundle(
			'perf2-runes',
			`${IMPORTS}\nimport './src/lib/i18n/pack-registry.svelte';\nexport { watch } from 'perf2-probe';\nexport { ensureLang } from './src/lib/i18n/load';\nexport { flushSync } from 'svelte';\n`,
			{ plugins: [stubApp, runes], conditions: ['svelte', 'browser'] },
		);
		R = await fresh(file);
	} catch (e) {
		ok('runes: the client-compiled probe loads', false, String(e?.message ?? e).slice(0, 300));
	}
	if (R) {
		const s = SAMPLE['packs.wall'];
		const seen = [];
		const stop = R.watch('hi', s.key, seen);
		R.flushSync();
		await R.ensureLang('hi');
		R.flushSync();
		stop();
		ok('runes: a $effect reading t() ran first with EN (never the raw key) and re-ran with HI once the chunk landed', seen[0] === s.en && seen.at(-1) === s.hi, JSON.stringify(seen.map((x) => x.slice(0, 24))));
	}
}

// ── 3. icons ──────────────────────────────────────────────────────────────────

const DESIGN = path.join(DECK, 'src/lib/design');
const ICONS = await bundle('perf2-icons', `export * as I from './src/lib/design/icons';\nexport * as C from './src/lib/design/icons-core';\n`);
{
	delete globalThis.document;
	delete globalThis.window;
	const { I, C } = await fresh(ICONS);
	const names16 = Object.keys(I.ICONS_16);
	const pathsSha = (tbl) => createHash('sha256').update(Object.entries(tbl).map(([n, p]) => `${n}\u0000${(p ?? []).join('\u0001')}`).join('\n')).digest('hex');
	ok('icons: ICONS_16 is complete, frozen and in main\'s order with main\'s path data', names16.length === ICON_GOLDEN.n16 && Object.isFrozen(I.ICONS_16) && createHash('sha256').update(names16.join('\n')).digest('hex') === ICON_GOLDEN.order16 && pathsSha(I.ICONS_16) === ICON_GOLDEN.paths16, `${names16.length} names`);
	ok('icons: ICONS_20 is complete, frozen, with main\'s path data', Object.keys(I.ICONS_20).length === ICON_GOLDEN.n20 && Object.isFrozen(I.ICONS_20) && pathsSha(I.ICONS_20) === ICON_GOLDEN.paths20, `${Object.keys(I.ICONS_20).length} names`);
	ok('icons: ICON_NAMES is the full set in table order', C.ICON_NAMES.length === names16.length && C.ICON_NAMES.every((n, i) => n === names16[i]));
	const core = new Set(Object.keys(C.CORE_16));
	const deferred = names16.filter((n) => !core.has(n));
	ok('icons (prod): isIconName knows every name before anything loads, and rejects others', names16.every((n) => I.isIconName(n)) && !I.isIconName('person') && !I.isIconName('') && !I.isIconName(42), `${names16.length} names, ${deferred.length} deferred`);
	ok('icons (prod): a first-paint glyph draws at once; a deferred one has no paths until its half lands', [...core].every((n) => I.iconPaths(n, 16).paths.length > 0) && deferred.length > 0 && deferred.every((n) => I.iconPaths(n, 16).paths.length === 0 && !I.iconReady(n)));
	ok('icons (prod): nothing has asked for the deferred half yet', I.restIconsInFlight() === null && !I.restIconsLoaded());
	await I.loadRestIcons();
	const bad = names16.filter((n) => {
		const p16 = I.iconPaths(n, 16);
		const p20 = I.iconPaths(n, 20);
		return p16.paths.length === 0 || p16.paths !== I.ICONS_16[n] || p20.grid !== (I.ICONS_20[n] ? 20 : 16) || p20.paths !== (I.ICONS_20[n] ?? I.ICONS_16[n]);
	});
	ok('icons (prod): after loadRestIcons() EVERY name resolves at 16 and 20 px to main\'s drawing', bad.length === 0, bad.slice(0, 6).join(', ') || `${names16.length}/${names16.length}`);
	const pinned = new Set([...Object.values(C.FIRST_PAINT_ICONS).flat(), ...C.MAP_GLYPHS, ...C.CANVAS_PANEL_ICONS]);
	ok('icons: the first-paint half is EXACTLY the pinned first-viewport sets + the map-marker glyphs + the canvas panels\' glyphs', pinned.size === core.size && [...pinned].every((n) => core.has(n)), `${core.size} glyphs`);
	const coreHas20 = Object.keys(C.CORE_20).every((n) => core.has(n)) && [...core].every((n) => !I.ICONS_20[n] || C.CORE_20[n]);
	ok('icons: a first-paint glyph carries its 20 px drawing too (no scaled stand-in until the rest lands)', coreHas20);
	const mapNeed = [...new Set([...Object.values(I.KIND_ICON), ...Object.values(I.EVENT_KIND_ICON), 'dot', 'lock'])];
	ok('icons: every glyph a map marker can draw is first-paint (a canvas billboard cannot redraw itself)', mapNeed.every((n) => C.MAP_GLYPHS.includes(n) && core.has(n)), mapNeed.filter((n) => !core.has(n)).join(', ') || `${mapNeed.length} glyphs`);
}

// the server render of the three routes: every glyph drawn must be first-paint and pinned for that route
{
	const SERVER = path.join(DECK, '.svelte-kit/output/server/index.js');
	const MANIFEST = path.join(DECK, '.svelte-kit/output/server/manifest.js');
	if (!existsSync(SERVER) || !existsSync(MANIFEST)) {
		console.log('skip icons: server-render pin — no production build (.svelte-kit/output/server); `sem.sh deck-build 2 npm run build:cpu` then re-run');
	} else {
		// nothing the render does may reach a backend: point every upstream at the discard port
		for (const k of ['ORACLE_PORT', 'BRAIN_PORT', 'EMULATOR_PORT']) process.env[k] = '9';
		for (const k of ['VEER_OPERATOR_PIN', 'VEER_OPERATOR_PIN_FILE', 'VEER_SESSION_SECRET', 'VEER_CESIUM_ION_TOKEN']) delete process.env[k];
		globalThis.crypto ??= (await import('node:crypto')).webcrypto; // node 18: what adapter-node's shims install
		const { Server } = await import(pathToFileURL(SERVER).href);
		const { manifest } = await import(pathToFileURL(MANIFEST).href);
		const server = new Server(manifest);
		await server.init({ env: process.env });
		const C = await import(`${pathToFileURL(path.join(OUT_DIR, 'perf2-icons.mjs')).href}?i=${++instance}`).then((m) => m.C);
		const core = new Set(Object.keys(C.CORE_16));
		// FIRST_PAINT_ICONS is keyed by the LOGICAL route ('/' is the workspace's pinned set); the URL it is served at is WORKSPACE
		const pinKey = (route) => (route === WORKSPACE ? '/' : route);
		for (const route of [WORKSPACE, '/ops', '/gods-eye']) {
			const drawn = new Set();
			for (const lang of LANGS) {
				const res = await server.respond(new Request(`http://127.0.0.1${route}`, { headers: { cookie: `veer_lang=${lang}` } }), { getClientAddress: () => '127.0.0.1' });
				const html = await res.text();
				for (const m of html.matchAll(/data-icon="([a-z0-9-]+)"/g)) drawn.add(m[1]);
			}
			const notCore = [...drawn].filter((n) => !core.has(n));
			const notPinned = [...drawn].filter((n) => !C.FIRST_PAINT_ICONS[pinKey(route)].includes(n));
			ok(`icons: the server render of ${route} (EN/HI/GU) draws only first-paint glyphs pinned for the route`, drawn.size > 0 && notCore.length === 0 && notPinned.length === 0, `${drawn.size} glyphs${notCore.length ? `; not first-paint: ${notCore.join(', ')}` : ''}${notPinned.length ? `; not pinned: ${notPinned.join(', ')}` : ''}`);
		}
	}
}

if (failures) {
	console.error(`\n${failures} check(s) failed`);
	process.exit(1);
}
console.log('\nok   perf2 — every pack copy matches main, every language lands on the production path for all 16 modules, and the icon set is whole');
process.exit(0);
