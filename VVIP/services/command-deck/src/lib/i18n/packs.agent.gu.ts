/**
 * packs.agent — the GU strings (FIX-E-PERF2): the ONE copy that runs. The
 * server render, vite dev and the node tests import it from ./packs.agent.ts; the
 * production browser fetches it as its own chunk (lib/i18n/load.ts). Values
 * are byte-identical to the pre-split module (tests/perf2.unit.mjs pins the
 * key count and a content hash per module and language).
 * ./packs.agent.ts keeps a never-registered text mirror of this block for
 * two AST-reading tests; tests/perf2.unit.mjs pins both copies.
 */

type Pack = Record<string, string | ((...args: unknown[]) => string)>;

export const gu: Pack = {
	agent_suggests: 'AI નું સૂચન',
	agent_apply: 'લાગુ કરો',
	agent_dismiss: 'નકારો',
	agent_applied: 'લાગુ કર્યું',
	agent_dismissed: 'નકાર્યું',
	agent_ack_failed: 'અહીં લાગુ કર્યું — ઓડિટ પાવતી બ્રેઇન સુધી ન પહોંચી',
	agent_proposal: 'માત્ર પ્રસ્તાવ — માનવ લાગુ કરે ત્યાં સુધી કંઈ ખસતું નથી',
	agent_from: (tier) => `એજન્ટ તરફથી (${tier} સ્તર)`,
	agent_more: (n) => `+${n} વધુ`,
	agent_open_map: 'નકશા પર ખોલો',
	agent_queue_note: 'AI સૂચનો સિટી કમાન્ડ કેનવાસ પર રાહ જુએ છે',
	agent_verb_canvas_fly_to: 'અહીં જાઓ',
	agent_verb_canvas_track_entity: 'ટ્રેક કરો',
	agent_verb_canvas_highlight: 'હાઇલાઇટ કરો',
	agent_verb_canvas_annotate: 'નોંધ',
	agent_verb_canvas_set_sensor: 'થર્મલ-શૈલી દૃશ્ય',
	agent_verb_canvas_toggle_layer: 'સ્તર',
	agent_note_label: 'AI નોંધ',

	chat_suggest_title: 'અજમાવો',
	chat_suggest_traffic: 'આ કોરિડોર પર લાઇવ ટ્રાફિક',
	chat_suggest_interception: 'ઇન્ટરસેપ્શન યોજના',
	chat_suggest_closures: 'બંધ માર્ગોની સ્થિતિ',
	chat_suggest_map: 'નકશા પર બતાવો',
	chat_suggest_stolen: 'ચોરાયેલું વાહન નકશા પર બતાવો',
	chat_suggest_events: 'કઈ ઘટનાઓ સક્રિય છે?',
	chat_suggest_units: 'યુનિટ ક્યાં છે?',
	chat_cited: 'સંદર્ભ',
	chat_directives: 'નકશા પર પ્રસ્તાવિત',
	chat_open_city: 'સિટી કમાન્ડમાં ખોલો',

	pal_title: 'કમાન્ડ પેલેટ',
	// FIX-E-LOOKUP: ઉદાહરણ થર્મલ-શૈલી દૃશ્ય અને તેના પેલેટનું નામ બોલે છે — કોઈ સેન્સર નહીં
	pal_placeholder: 'fly to a plate or junction · show police units near Relief Road · layer cameras off · થર્મલ-શૈલી દૃશ્ય: આયર્નબો · ask …',
	pal_hint: '⌘K / Ctrl+K · ↑↓ પસંદ કરો · Enter ચલાવો · Esc બંધ કરો',
	pal_fly: 'અહીં જાઓ',
	pal_units: 'યુનિટ બતાવો',
	pal_layer: 'સ્તર',
	pal_sensor: 'થર્મલ-શૈલી દૃશ્ય',
	pal_ask: 'એજન્ટને પૂછો',
	pal_no_match: 'કોઈ વાહન, જંકશન, રસ્તો કે એકમ મેળ ખાતું નથી',
	pal_vehicles_only: 'માત્ર વાહનો (ANPR નંબર પ્લેટ) — કોઈ વ્યક્તિની શોધ થતી નથી',
	pal_sent: 'એજન્ટને મોકલ્યું — તેના સૂચનો આ કેનવાસ પર આવશે',
	pal_units_near: (n, road) => `${road} પાસે ${n} યુનિટ`,
	pal_none_near: (road) => `અત્યારે ${road} પાસે કોઈ યુનિટ નથી`,
	pal_unknown_road: 'નેટવર્ક પર આ નામનો કોઈ રસ્તો નથી',

	dossier_explain: 'આ સમજાવો',
	dossier_explaining: 'સમજાવી રહ્યું છે…',
	dossier_explain_cancel: 'રદ કરો',
	dossier_explain_masked: 'પ્લેટ છુપાયેલી છે — નામિત ડ્યુટી અધિકારી તેને જુએ છે',
	dossier_explain_failed: 'એજન્ટે જવાબ ન આપ્યો',
	dossier_explain_by: 'એજન્ટનો જવાબ',
	dossier_test: 'પરીક્ષણ',
	dossier_session_officer: 'સાઇન-ઇન ડ્યુટી અધિકારી',

	canvas_live_paused: 'લાઇવ થોભ્યું',
	canvas_live_paused_hint: 'રીપ્લે કેનવાસ પર છે — LIVE પર લાઇવ સ્તરો ફરી ચાલશે',
	canvas_ama_title:
		'સક્રિય મૂવમેન્ટ અનુકૂલન — સ્થિતિ → હિસ્ટેરેસિસ → નીતિ મર્યાદાઓ → ટ્વિન શેડો-તપાસ (ફેલ-ક્લોઝ્ડ) → ઑડિટેડ સંગ્રહ. ઉંમર = બેન્ડના સૌથી નવા રીડિંગ પછીનો સમય (ઘટનાનું તાજું સ્થિતિ રીડિંગ, અથવા શહેર બેન્ડનું તાજું એન્જિન મૂલ્યાંકન) — બેન્ડ કેટલા સમયથી ટક્યો છે તે નહીં. STALE = 10 મિનિટથી કોઈ નવું રીડિંગ નથી.',
};
