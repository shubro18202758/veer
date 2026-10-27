/**
 * packs.corridor — the GU strings (FIX-E-PERF2): the ONE copy that runs. The
 * server render, vite dev and the node tests import it from ./packs.corridor.ts; the
 * production browser fetches it as its own chunk (lib/i18n/load.ts). Values
 * are byte-identical to the pre-split module (tests/perf2.unit.mjs pins the
 * key count and a content hash per module and language).
 */

type Pack = Record<string, string | ((...args: unknown[]) => string)>;

const s = (v: unknown) => String(v ?? '');
const n = (v: unknown) => Number(v);
export const gu: Pack = {
	cor_tab_plan: 'યોજના',
	cor_tab_layers: 'સ્તરો',
	cor_tab_movement: 'મૂવમેન્ટ',

	cor_plan_section: 'કોરિડોર યોજના',
	cor_plan_from: 'થી',
	cor_plan_to: 'સુધી',
	cor_plan_class: 'વર્ગ',
	cor_plan_departure: 'પ્રસ્થાન (IST)',
	cor_plan_label: 'લેબલ',
	cor_label_placeholder: 'દા.ત. સ્વીકૃતિ પરીક્ષણ',
	cor_plan_label_hint: 'પરીક્ષણ / રિહર્સલ લેબલ મૂવમેન્ટના શીર્ષક તરીકે જાય છે — તેને ક્યારેય અસલી મૂવમેન્ટ બતાવવામાં આવતું નથી',
	cor_plan_officer: 'ડ્યુટી અધિકારી',
	cor_plan_btn: 'કોરિડોર પ્લાન કરો',
	cor_plan_btn_busy: 'યોજના બની રહી છે…',
	cor_plan_none: 'હજી કોઈ યોજના નથી — મૂળ અને મુકામ પસંદ કરી યોજના બનાવો.',

	cor_status_approved: 'સુરક્ષા અનુરૂપ',
	cor_status_conditional: 'શરતી',
	cor_status_hold: 'હોલ્ડ',
	cor_status_no_route: 'કોઈ માર્ગ નથી',
	cor_status_unknown: 'યોજનાબદ્ધ',

	cor_waiver: 'હું આ યોજનાના સૂચિબદ્ધ લેન-ફ્લોર ઉલ્લંઘન સ્વીકારું છું',
	cor_waiver_stamped: (who: unknown) => `${s(who)} એ લેન-ફ્લોર ઉલ્લંઘન સ્વીકાર્યા`,

	cor_hold_replan: (at: unknown) => `${s(at)} પછી ફરી યોજના બનાવો`,
	cor_hold_note: 'ડિસાઇડરે પ્રસ્થાન મુલતવી રાખ્યું. આ યોજના લોન્ચ થઈ શકતી નથી.',

	cor_no_route_note: 'આ જોડી અને વર્ગ માટે પ્લાનરને કોઈ માર્ગ મળ્યો નથી.',
	cor_no_route_next: 'આગળ: બીજું મૂળ કે મુકામ, અથવા નીચો સુરક્ષા વર્ગ પસંદ કરી ફરી યોજના બનાવો.',

	cor_launch: 'એસ્કોર્ટ શરૂ કરો',
	cor_launch_starting: 'શરૂ થાય છે…',
	cor_launch_criteria: (cls: unknown, dest: unknown) => `${s(cls)} મૂવમેન્ટને નામિત ડ્યુટી અધિકારી હેઠળ ${s(dest)} સુધી એસ્કોર્ટ કરે છે`,
	cor_launch_locked_waiver: 'પહેલા લેન-ફ્લોર ઉલ્લંઘન સ્વીકારો — યોજના શરતી છે.',
	cor_launch_locked_hold: 'ડિસાઇડરે યોજના રોકી — પછીના પ્રસ્થાન માટે ફરી યોજના બનાવો.',
	cor_launch_locked_officer: 'લોન્ચ માટે ડ્યુટી અધિકારીનું નામ આપો.',
	cor_launch_locked_no_plan: 'પહેલા કોરિડોરની યોજના બનાવો.',
	cor_stop: 'એસ્કોર્ટ રોકો',
	cor_stopping: 'અટકે છે…',
	cor_clear: 'સાફ કરો',
	cor_clearing: 'સાફ થાય છે…',
	cor_clear_hint: 'ક્લિયરન્સ પછીની પુનઃસ્થાપના: બંધી હટાવી, સિગ્નલ કાર્યક્રમ પુનઃસ્થાપિત, કોરિડોર ઇવેન્ટ બંધ',

	cor_cand_primary: 'પ્રાથમિક',
	cor_cand_alternate: (k: unknown) => `વૈકલ્પિક ${s(k)}`,
	cor_cand_adds: (roads: unknown) => `${s(roads)} ઉમેરે છે`,
	cor_cand_compliant: 'લેન ફ્લોર પૂરો',
	cor_cand_violations: (c: unknown) => `${n(c)} લેન-ફ્લોર ઉલ્લંઘન`,
	cor_cand_ai_pick: (conf: unknown) => `Veer AIની પસંદગી · વિશ્વાસ ${s(conf)}`,
	cor_cand_tactical_pick: 'ટેક્ટિકલ પ્રાથમિક',
	cor_cand_rejected: (c: unknown) => `નકારેલા માર્ગો (${n(c)})`,
	cor_cand_adds_none: 'કોઈ નવો રસ્તો ઉમેરતો નથી',
	cor_cand_roads: (c: unknown) => `${n(c)} રસ્તા${n(c) === 1 ? '' : 'ઓ'}`,

	cor_proposal_link: (title: unknown) => `એસ્કોર્ટ પ્રસ્તાવ રાહ જોશે: ${s(title)}`,
	cor_proposal_open: 'મૂવમેન્ટ ટેબમાં નિર્ણય લો',

	cor_hud_escort_live: 'એસ્કોર્ટ ચાલુ છે',
	cor_hud_planned: 'એસ્કોર્ટ યોજનાબદ્ધ',
	cor_hud_completed: 'એસ્કોર્ટ પૂર્ણ',
	cor_hud_stopped: 'એસ્કોર્ટ અટક્યો',
	cor_hud_failed: 'એસ્કોર્ટ નિષ્ફળ',
	cor_hud_speed: 'ઝડપ',
	cor_hud_speed_corridor: 'કોરિડોર સરેરાશ',
	cor_hud_progress: 'પ્રગતિ',
	cor_hud_eta: 'ETA',
	cor_hud_eta_planned: 'યોજના મુજબ',
	cor_hud_hold: 'હોલ્ડ',
	cor_hud_hold_none: 'કોઈ નહીં',
	cor_hud_hold_yes: 'રોકાયેલ',
	cor_hud_next_junction: (name: unknown, t: unknown) => `આગળનું જંક્શન ${s(name)} · ${s(t)} માં`,
	cor_hud_awaiting_gps: 'GPSની રાહ',
	cor_hud_destination: 'મુકામ',
	cor_hud_min: (m: unknown) => `${n(m)} મિનિટ`,
	cor_hud_sec: (v: unknown) => `${n(v)} સેકંડ`,
	cor_hud_legacy_brain: 'આ બ્રેન એસ્કોર્ટ નિયંત્રણ પહેલાનો છે — તેણે પોતાનું લૂપ તરત ચલાવી પૂર્ણ કર્યું.',
	cor_hud_officer_note: 'ડ્યુટી અધિકારીનું નામ જ એસ્કોર્ટ નક્કી કરે છે; AI ક્યારેય જાતે કંઈ લાગુ કરતું નથી.',
	cor_hud_nofigures: 'આ કોન્સોલ પર કોઈ લાઇવ આંકડો નથી — મૂવમેન્ટ ટૅબ ખોલો',

	cor_events_none: 'કોઈ લાઇવ કોરિડોર ઇવેન્ટ નથી',
	cor_events_focus: 'નકશા પર બતાવો',
	cor_events_focus_locked: 'લોક',
	cor_events_focus_locating: 'શોધી રહ્યા છીએ…',
	cor_events_no_spine: 'કેનવાસ પર કોઈ સ્પાઇન નથી',
	cor_events_no_canvas: 'કેનવાસ ઉપલબ્ધ નથી',
	cor_events_test_tip: (label: unknown) => `લેબલવાળું પરીક્ષણ / રિહર્સલ મૂવમેન્ટ — અસલી મૂવમેન્ટ નથી: ${s(label)}`,
	cor_events_promoted: 'ખુલ્લા સ્રોતની રિપોર્ટમાંથી પ્રમોટ થયું',
	cor_events_test: 'પરીક્ષણ',

	cor_tab_failed: 'આ પેનલ લોડ કરી શકાયું નથી.'
};
