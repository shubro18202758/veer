/** packs.pub3 — the GU strings (see ./packs.pub3.ts). */
import type { PubKey } from './packs.pub3';

type Fn = (...args: unknown[]) => string;
const s = (v: unknown) => String(v ?? '');

export const gu: Record<PubKey, string | Fn> = {
	v3p_skip: 'પાના પર જાઓ',
	v3p_logo: 'Veer',
	v3p_lang_short_en: 'EN',
	v3p_lang_short_hi: 'हिं',
	v3p_lang_short_gu: 'ગુ',
	v3p_hold_map_alt: 'આ ઘટના માટે રોકાતા રસ્તાઓનો નકશો',
	v3p_step: (n: unknown) => `પગલું ${s(n)}`,
	v3p_sat_credit: 'નકશા ડેટા © OpenStreetMap યોગદાનકર્તાઓ',
	v3p_map_title: 'કોરિડોરનો નકશો',
	v3p_open_driver: 'ડ્રાઇવર પાનું ખોલો',
	v3p_view_tabs: 'જાહેર પાનાં',
};
