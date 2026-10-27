/**
 * packs.ui — the GU strings (FIX-E-PERF2): the ONE copy that runs. The
 * server render, vite dev and the node tests import it from ./packs.ui.ts; the
 * production browser fetches it as its own chunk (lib/i18n/load.ts). Values
 * are byte-identical to the pre-split module (tests/perf2.unit.mjs pins the
 * key count and a content hash per module and language).
 */

import type { UiKey } from './packs.ui';
type Fn = (...args: unknown[]) => string;
export const gu: Record<UiKey, string | Fn> = {
	ui_close: 'બંધ કરો',
	ui_dismiss: 'દૂર કરો',
	ui_remove: 'દૂર કરો',
	ui_clear: 'સાફ કરો',
	ui_cancel: 'રદ કરો',
	ui_confirm: 'પુષ્ટિ કરો',
	ui_loading: 'લોડ થઈ રહ્યું છે',
	ui_more: 'વધુ',
	ui_err_404_title: 'પાનું મળ્યું નથી',
	ui_err_404_body: 'આ સરનામે કોઈ પાનું નથી. બારમાંથી કોઈ મોડ્યુલ ખોલો, અથવા કૉરિડોર વર્કસ્પેસ પર જાઓ.',
	ui_err_title: 'આ પાનું બતાવી શકાયું નહીં',
	ui_err_body: 'તેને લોડ કરતી વખતે કંઈક ખોટું થયું. પાનું ફરી લોડ કરો, અથવા કૉરિડોર વર્કસ્પેસ પર જાઓ.',
	ui_err_home: 'કૉરિડોર વર્કસ્પેસ ખોલો',
	ui_expand: 'ખોલો',
	ui_collapse: 'સંકેલો',
	ui_show_details: 'વિગતો બતાવો',
	ui_hide_details: 'વિગતો છુપાવો',
	ui_sort_asc: 'ચડતા ક્રમમાં',
	ui_sort_desc: 'ઊતરતા ક્રમમાં',
	ui_sort_by: (col: unknown) => `${String(col)} મુજબ ગોઠવો`,
	ui_table_empty: 'બતાવવા માટે કંઈ નથી',
	ui_location: 'સ્થાન',
	ui_notifications: 'સૂચનાઓ',
	ui_resize: 'કદ બદલો',
	ui_trend: 'વલણ',

	ui_masked: 'છુપાયેલું',
	ui_masked_tip: 'ડ્યુટી અધિકારીનું નામ આપવામાં ન આવે ત્યાં સુધી નોંધણી નંબર છુપાયેલો છે.',

	ui_prov_emulated: 'ઇમ્યુલેટેડ',
	ui_prov_simulated: 'સિમ્યુલેટેડ',
	ui_prov_test: 'પરીક્ષણ',
	ui_prov_osint: 'ખુલ્લો સ્રોત',
	ui_prov_emulated_tip: 'સિનારિયો ઇમ્યુલેટરમાંથી. ફીલ્ડ રીડિંગ નથી.',
	ui_prov_simulated_tip: 'સિમ્યુલેટેડ ટ્રાફિક ફીડ: કૃત્રિમ અવલોકનો.',
	ui_prov_test_tip: 'અભ્યાસ અથવા પરીક્ષણ ડેટા.',
	ui_prov_osint_tip: 'ખુલ્લા સ્રોતોમાંથી. હજી કોઈ ચકાસણી સ્થિતિ નથી.',
	ui_prov_unknown: 'અજાણ્યો સ્રોત',
	ui_prov_unknown_tip: 'આ પંક્તિનો સ્રોત આ કન્સોલ ઓળખતું નથી.',
	ui_verif_unverified: 'અચકાસાયેલ OSINT',
	ui_verif_news: 'સમાચારમાં નોંધાયેલ',
	ui_verif_official: 'સત્તાવાર, ચકાસાયેલ',
	ui_verif_confirmed: 'અધિકારી દ્વારા પુષ્ટિ',
	ui_verif_unverified_tip: 'ખુલ્લા સ્રોતનો અહેવાલ, સમાચાર કે સત્તાવાર સ્રોતથી પુષ્ટિ નથી.',
	ui_verif_news_tip: 'સમાચાર માધ્યમો દ્વારા નોંધાયેલ. સત્તાવાર સ્રોતથી ચકાસાયેલ નથી.',
	ui_verif_official_tip: 'સત્તાવાર સ્રોત દ્વારા જારી, જેમ કે જાહેર ચેતવણી.',
	ui_verif_confirmed_tip: 'નામ આપેલા અધિકારી દ્વારા પુષ્ટિ.',

	ui_eye_show: 'બતાવો',
	ui_eye_hide: 'છુપાવો',
	ui_eye_none: 'હમણાં કોઈ નથી',

	ui_time_ist: 'IST',
	ui_time_hint: 'IST, 24-કલાકની ઘડિયાળ',
	ui_time_invalid: 'સમય hh:mm તરીકે લખો',
	ui_time_invalid_s: 'સમય hh:mm:ss તરીકે લખો',

	ui_now: 'હમણાં',
	ui_ago: (x: unknown) => `${String(x)} પહેલાં`,
	ui_in: (x: unknown) => `${String(x)}માં`,
	ui_unit_s: 'સેકન્ડ',
	ui_unit_min: 'મિનિટ',
	ui_unit_h: 'કલાક',
	ui_unit_d: 'દિવસ',

	ui_hotkeys_title: 'કીબોર્ડ શૉર્ટકટ',
	ui_hk_global: 'સામાન્ય',
	ui_hk_docks: 'પેનલ',
	ui_hk_lists: 'યાદીઓ અને કોષ્ટકો',
	ui_hk_omnibar: 'વસ્તુઓ અને આદેશો શોધો',
	ui_hk_search: 'શોધ પર જાઓ',
	ui_hk_help: 'શૉર્ટકટ બતાવો',
	ui_hk_escape: 'બંધ કરો, પછી સાફ કરો',
	ui_hk_left_dock: 'ડાબી પેનલ બતાવો અથવા છુપાવો',
	ui_hk_right_dock: 'જમણી પેનલ બતાવો અથવા છુપાવો',
	ui_hk_timeline: 'ટાઇમલાઇન બતાવો અથવા છુપાવો',
	ui_hk_next: 'આગળની પ્રવિષ્ટિ',
	ui_hk_prev: 'પાછલી પ્રવિષ્ટિ',
	ui_hk_open: 'પ્રવિષ્ટિ ખોલો',
	ui_hk_rule: 'કોઈ એક કીથી મંજૂરી, અનમાસ્ક, દંડ, ડિસ્પેચ કે પ્રકાશન થતું નથી.',

	ui_fig_report: (n: unknown) => `${n} અહેવાલ`,
	ui_fig_reports: (n: unknown) => `${n} અહેવાલો`,
	ui_fig_context_note: 'જિલ્લા ચેતવણી લાગુ'
};
