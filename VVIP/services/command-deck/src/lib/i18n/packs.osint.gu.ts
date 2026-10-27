/**
 * packs.osint — the GU strings (FIX-E-PERF2): the ONE copy that runs. The
 * server render, vite dev and the node tests import it from ./packs.osint.ts; the
 * production browser fetches it as its own chunk (lib/i18n/load.ts). Values
 * are byte-identical to the pre-split module (tests/perf2.unit.mjs pins the
 * key count and a content hash per module and language).
 */

type Fn = (...args: unknown[]) => string;
type OsintPack = Record<string, string | Fn>;
export const gu: OsintPack = {
	kind_reported_crime: 'નોંધાયેલ ગુનો',
	kind_public_disorder: 'જાહેર અવ્યવસ્થા',
	kind_road_accident: 'માર્ગ અકસ્માત',
	kind_hazard: 'જોખમ',
	kind_flooding: 'પાણી ભરાવો',
	kind_infra_failure: 'માળખાકીય નિષ્ફળતા',

	os_group_situation: 'પરિસ્થિતિ',
	os_group_verification: 'ચકાસણી',
	os_group_location: 'સ્થળ',
	os_group_sources: 'સ્ત્રોતો',
	os_group_live: 'વર્તમાન સ્થિતિ',
	os_group_place: 'સ્થળ',

	os_class: 'વર્ગ',
	os_subtype: 'ઉપપ્રકાર',
	os_correlated: 'સહસંબંધિત વર્ગો',
	os_summary: 'સારાંશ',
	os_event_kind_reported_crime: 'નોંધાયેલ ગુનો',
	os_event_kind_public_disorder: 'જાહેર અવ્યવસ્થા',
	os_event_kind_road_accident: 'માર્ગ અકસ્માત',
	os_event_kind_hazard: 'જોખમ',
	os_event_kind_flooding: 'પાણી ભરાવો',
	os_event_kind_infra_failure: 'માળખાકીય નિષ્ફળતા',
	os_event_kind_other: 'કોરિડોર ઘટના',

	os_independent_publishers: 'સ્વતંત્ર પ્રકાશકો',
	os_cross_type: 'પાર-પ્રકાર પુષ્ટિ',
	os_yes: 'હા',
	os_no: 'ના',

	os_toponym: 'સ્થળ',
	os_road: 'રસ્તો',
	os_junction: 'ચોક',
	os_geocode: 'ભૂ-સ્થળ વિશ્વસનીયતા',
	os_bucket_high: 'ઉચ્ચ',
	os_bucket_medium: 'મધ્યમ',
	os_bucket_low: 'નીચું',
	os_area_note: 'જિલ્લા-સ્તરનો અહેવાલ: કોઈ શેરી-સ્તરનું સ્થળ નહીં',

	os_source_link_withheld: 'સ્ત્રોત લિંક સાચવેલ (તેમાં કોઈ વ્યક્તિનું નામ હોઈ શકે)',
	os_context_official: 'જિલ્લા ચેતવણી લાગુ',
	os_context_report: 'જિલ્લા-સ્તરનો અહેવાલ લાગુ',
	os_fig_context_official: 'જિલ્લા ચેતવણી લાગુ',
	os_fig_context_report: 'જિલ્લા-સ્તરનો અહેવાલ લાગુ',
	os_fetch_cached: 'કૅશ કરેલ નમૂનો',
	os_tier_official: 'સત્તાવાર',
	os_tier_aggregator: 'સમાચાર એકત્રકર્તા',
	os_tier_news_regional: 'પ્રાદેશિક સમાચાર',
	os_tier_news_national: 'રાષ્ટ્રીય સમાચાર',
	os_tier_social_unverified: 'અચકાસેલ સામાજિક',

	os_pick_reported: 'નોંધાયેલ',
	os_pick_credibility: 'વિશ્વસનીયતા',
	os_pick_street: 'પ્રતિભાવ માટે નોંધાયેલ પરિસ્થિતિ.',
	os_pick_district: 'જિલ્લા-સ્તરનો અહેવાલ, જિલ્લાના સંદર્ભ બિંદુ પર દર્શાવેલ. અહેવાલ આખા જિલ્લાનો છે, આ સ્થળનો નહીં.',
	os_pick_area_ring: 'જિલ્લાના સંદર્ભ બિંદુની આસપાસ એક ચિહ્ન-વર્તુળ, અહેવાલનો વિસ્તાર નહીં.',
	os_pick_never_people: 'નોંધાયેલ પરિસ્થિતિઓ સ્થળો વિશે છે, ક્યારેય લોકો વિશે નહીં.',
	os_layer_held_one: 'એકલ-પોસ્ટ સામાજિક અહેવાલ આખા શહેરમાં રોખેલ (ક્યારેય બતાવેલ નહીં)',
	os_layer_down: 'સિટી ફ્યુઝન સેવા ઉપલબ્ધ નથી — નોંધાયેલી પરિસ્થિતિઓ બતાવી નથી',
	os_layer_on_canvas: (n: unknown) => `નકશા પર ${n} નોંધાયેલી પરિસ્થિતિઓ`,
	os_layer_area: (n: unknown) => `${n} વિસ્તાર-સ્તરની`,
	os_layer_waiting: (n: unknown) => `${n} નિર્ણયની રાહમાં`,
	os_layer_unmapped: (n: unknown) => `${n} શહેર-બિંદુ વિના`,
	os_pick_at: (place: unknown) => `${place} ખાતે`,
	os_layer_held_many: 'એકલ-પોસ્ટ સામાજિક અહેવાલો આખા શહેરમાં રોખેલ (ક્યારેય બતાવેલ નહીં)',

	os_attach: 'સ્થિતિ',
	os_attach_novel: 'નવી પરિસ્થિતિ (પહેલો અહેવાલ)',
	os_corroborates: 'કોઈ લાઇવ વસ્તુની પુષ્ટિ કરે છે',
	os_promoted_to: 'કોરિડોર ઘટના તરફ આગળ વધારાયેલ',

	os_place_name: 'નામ',
	os_place_type: 'લક્ષણ',
	os_surface_forms: 'અન્ય નામો',
	os_place_reports: 'જોડાયેલ અહેવાલો',

	os_rule_note: 'પ્રતિભાવ માટે નોંધાયેલ પરિસ્થિતિ. વીર ક્યારેય લોકોને ઓળખતું નથી.',

	os_act_search_around: 'આ સ્થળની આસપાસ શોધો',
	os_act_sources: 'સ્ત્રોત યાદી ખોલો',

	os_state_surfaced: 'ઉભરેલી',
};
