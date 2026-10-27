/**
 * packs.assistant — the GU strings (FIX-E-PERF2): the ONE copy that runs. The
 * server render, vite dev and the node tests import it from ./packs.assistant.ts; the
 * production browser fetches it as its own chunk (lib/i18n/load.ts). Values
 * are byte-identical to the pre-split module (tests/perf2.unit.mjs pins the
 * key count and a content hash per module and language).
 */

type Pack = Record<string, string | ((...args: unknown[]) => string)>;

const s = (v: unknown) => String(v ?? '');
export const gu: Pack = {
	asst_tab: 'સહાયક',
	asst_page_title: 'સહાયક',
	asst_page_sub: 'તે શહેર વાંચે છે અને સૂચન કરે છે. સૂચનો ત્યાં ખુલે છે જ્યાં કોઈ વ્યક્તિ તેમને તપાસે — અહીં કંઈ લાગુ થતું નથી.',
	asst_actor: 'વીર સહાયક · માત્ર વાંચન',
	asst_context_title: 'સંદર્ભ',
	asst_context_none: 'કંઈ પસંદ નથી',
	asst_context_hint: 'સહાયકને તેના પર કેન્દ્રિત કરવા કોઈ વસ્તુ પસંદ કરો',
	asst_decisions: 'નિર્ણય રાહ જોઈ રહ્યા છે',
	asst_citations: 'સંદર્ભિત વસ્તુઓ',
	asst_clear: 'વાતચીત સાફ કરો',

	asst_scope_prefix: '',
	asst_scope: (what: unknown) => `${s(what)} અને આ દૃશ્ય પ્રત્યે મર્યાદિત`,
	asst_scope_suffix: 'અને આ દૃશ્ય પ્રત્યે મર્યાદિત',
	asst_scope_view: 'આ દૃશ્ય પ્રત્યે મર્યાદિત',

	asst_steps: 'પગલાં',
	asst_details: 'વિગતો',
	asst_details_tools: 'ટૂલ કૉલ',
	asst_lookups_label: 'લુકઅપમાં શું મળ્યું',
	asst_grounding_removed: (n) => `${String(n)} વિધાનો દૂર કર્યાં: લુકઅપમાં નહોતાં`,
	asst_details_model: 'મોડેલ',
	asst_details_tier: 'સ્તર',
	asst_details_session: 'સત્ર',
	asst_steps_toggle: 'પગલાં બતાવો',
	asst_thoughts_toggle: 'તર્ક બતાવો',

	asst_proposed_map: (what: unknown) => `નકશા પર સૂચવેલ: ${s(what)}`,
	asst_review_map: 'તેને નકશા પર જુઓ',
	asst_decision_card: 'નિર્ણય રાહ જોઈ રહ્યો છે',

	asst_cite_select_map: 'નકશા પર પસંદ કરો',

	asst_ev_state_planned: 'આયોજિત',
	asst_ev_state_active: 'સક્રિય',
	asst_ev_state_completed: 'પૂર્ણ',
	asst_ev_state_cancelled: 'રદ',
	asst_interrupted: 'અટક્યું — જવાબ પૂરો થાય તે પહેલાં પેનલ બંધ થઈ.',

	asst_empty_title: 'સહાયકને પૂછો',
	asst_sample_note: 'તપાસ માટે બનાવેલ નમૂનાનો તબક્કો. કોઈ મોડેલ ચાલ્યું નથી.',

	asst_citizen_hold_one: 'નીચે 1 એમ્યુલેટેડ અટકાવ સૂચિબદ્ધ છે.',
	asst_citizen_hold_many: (n: unknown) => `નીચે ${n} એમ્યુલેટેડ અટકાવ સૂચિબદ્ધ છે.`,

	asst_driver_choose_stretch: 'પહેલા તમારું સ્થળ પસંદ કરો — પછી કોરિડોરની વિનંતી કરો.',
};
