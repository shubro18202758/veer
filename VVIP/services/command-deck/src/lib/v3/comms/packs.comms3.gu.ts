/** packs.comms3 — the GU strings (see ./packs.comms3.ts). Nothing here says a draft was sent. */
import type { CommsKey } from './packs.comms3';

type Fn = (...args: unknown[]) => string;
const s = (v: unknown) => String(v ?? '');

export const gu: Record<CommsKey, string | Fn> = {
	v3c_sub: 'અધિકારીએ કૉપી કરીને મોકલવા માટેના ડ્રાફ્ટ',
	v3c_events: 'ઘટનાઓ',
	v3c_events_aria: 'જે ઘટનાઓ માટે સલાહ લખી શકાય છે',
	v3c_map_alt: (title: unknown) => `${s(title)} ની જગ્યાનો નકશો`,
	v3c_no_place: 'આ ઘટનાની હજી નકશા પર સ્થિતિ નથી',
	v3c_open_event: 'ઘટના ખોલો',
	v3c_row_withheld: 'નાગરિકોથી રોકાયેલ',
	v3c_facts_used: 'વપરાયેલ હકીકતો',
	v3c_f_kind: 'ઘટનાનો પ્રકાર',
	v3c_f_road: 'ભાગ',
	v3c_f_hold: 'રોકાણ',
	v3c_f_when: 'થી',
	v3c_f_alt: 'વૈકલ્પિક માર્ગ',
	v3c_f_unknown: 'જણાવેલ નથી',
	v3c_sheet_aria: 'ડ્રાફ્ટ રેકોર્ડ અને ડિસ્પેચ થ્રેડ',
	v3c_close: 'બંધ કરો',
	v3c_copy_lang: (name: unknown) => `${s(name)} ડ્રાફ્ટ કૉપી કરો`,
	v3c_copied_inline: 'કૉપી થયું',
	v3c_tpl_hint: 'આવી ઘટના માટે નાગરિકો આ વાંચશે',
	v3c_withheld_pick: 'તેના ડ્રાફ્ટ જોવા બીજા શ્રોતા પસંદ કરો',
};
