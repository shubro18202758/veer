/**
 * packs.map — the GU strings (FIX-E-PERF2): the ONE copy that runs. The
 * server render, vite dev and the node tests import it from ./packs.map.ts; the
 * production browser fetches it as its own chunk (lib/i18n/load.ts). Values
 * are byte-identical to the pre-split module (tests/perf2.unit.mjs pins the
 * key count and a content hash per module and language).
 * ./packs.map.ts keeps a never-registered text mirror of this block for
 * two AST-reading tests; tests/perf2.unit.mjs pins both copies.
 */

import type { MapKey } from './packs.map';
type Fn = (...args: unknown[]) => string;
type Pack = Record<string, string | ((...args: unknown[]) => string)>;

export const gu: Record<MapKey, string | Fn> = {
	ge_imagery_photoreal: 'વાસ્તવિક 3D શહેર · Google',
	ge_imagery_photoreal_loading: 'વાસ્તવિક 3D · લોડ થાય છે',
	ge_imagery_ion: 'ion હવાઈ ચિત્ર · 3D ભૂપ્રદેશ',
	ge_imagery_osm: 'OSM · ડાર્ક',
	ge_imagery_osm_fallback: 'OSM ડાર્ક (વૈકલ્પિક)',
	ge_imagery_offline: 'ઑફલાઇન યોજનાકીય મોડ',

	map_toolbar: 'નકશાનાં સાધનો',
	map_tool_select: 'પસંદ કરો',
	map_tool_shape: 'આકારની અંદર પસંદ કરો',
	map_tool_shape_menu: 'આકારના વિકલ્પો',
	map_tool_shape_select: 'આકારની અંદર પસંદ કરો',
	map_tool_shape_filter: 'આકાર સુધી મર્યાદિત કરો',
	map_tool_shape_clear: 'આકાર ફિલ્ટર દૂર કરો',
	map_tool_shape_hint: 'નકશા પર બિંદુઓ પસંદ કરો, પછી આકાર બંધ કરવા ડબલ-ક્લિક કરો',
	map_tool_search_around: 'પસંદગીની આસપાસ શોધો',
	map_tool_search_around_none: 'પહેલાં કોઈ વસ્તુ પસંદ કરો',
	map_tool_measure: 'અંતર માપો',
	map_tool_measure_hint: 'નકશા પર બિંદુઓ પસંદ કરો; પૂરું કરવા ડબલ-ક્લિક અથવા Esc',
	map_tool_layers: 'સ્તરો',
	map_tool_legend: 'સંકેત-સૂચિ',
	map_tool_follow: 'પસંદગીને અનુસરો',
	map_tool_follow_none: 'અનુસરવા માટે કંઈક પસંદ કરો',
	map_tool_following: (name) => (name != null && name !== '' ? `${String(name)} ને અનુસરે છે` : 'પસંદગીને અનુસરે છે'),
	map_follow_no_position: (name) =>
		name != null && name !== ''
			? `${String(name)} નું નકશા પર કોઈ સ્થાન નથી, અનુસરણ શક્ય નથી`
			: 'પસંદગીનું નકશા પર કોઈ સ્થાન નથી, અનુસરણ શક્ય નથી',
	map_tool_tour: 'માર્ગદર્શિત પ્રવાસ',
	map_tool_tour_stop: 'માર્ગદર્શિત પ્રવાસ રોકો',
	map_tool_exit: 'નકશા મોડમાંથી બહાર',
	map_mode_live: 'લાઇવ',
	map_mode_window: 'લાઇવ નથી',
	map_mode_replay: (run) => (run != null ? `રીપ્લે · રન ${String(run)}` : 'રીપ્લે'),
	map_mode_live_tip: 'લાઇવ. સમય-મર્યાદા અથવા રીપ્લે માટે ટાઇમલાઇન ખોલો.',
	map_mode_window_tip: 'સમય-મર્યાદા લાગુ છે. લાઇવ પર પાછા જવા ટાઇમલાઇન ખોલો.',
	map_mode_replay_tip: 'રેકોર્ડ કરેલી ટેપ તેની પોતાની સમય-અક્ષ પર ચાલે છે.',

	// FIX-E-LOOKUP: "દૃશ્ય … (દૃશ્ય ફિલ્ટર)" નહીં — દૃશ્ય શબ્દ એક વાર; ફિલ્ટર વિઝ્યુઅલ ફિલ્ટર
	map_tool_thermal: 'થર્મલ-શૈલી દૃશ્ય',
	map_tool_thermal_tip: 'થર્મલ-શૈલી દૃશ્ય — ફક્ત એક વિઝ્યુઅલ ફિલ્ટર, કોઈ થર્મલ સેન્સર નથી',
	map_thermal_on: 'થર્મલ-શૈલી દૃશ્ય (વિઝ્યુઅલ ફિલ્ટર)',
	map_flir_note: 'વિઝ્યુઅલ ફિલ્ટર, કોઈ થર્મલ સેન્સર નથી',
	map_flir_off: 'સામાન્ય રંગો',
	map_flir_whot: 'થર્મલ શૈલી, સફેદ ગરમ',
	map_flir_bhot: 'થર્મલ શૈલી, કાળું ગરમ',
	map_flir_iron: 'થર્મલ શૈલી, આયર્નબો',
	map_pal_raw: 'સામાન્ય રંગો',
	map_pal_whot: 'સફેદ ગરમ',
	map_pal_bhot: 'કાળું ગરમ',
	map_pal_iron: 'આયર્નબો',

	map_zoom_in: 'ઝૂમ ઇન',
	map_zoom_out: 'ઝૂમ આઉટ',
	map_reset_north: 'ઉત્તર દિશા પર પાછા',
	map_rule_note: 'ફક્ત વાહનો · દંડ માટે નામાંકિત અધિકારી જરૂરી',
	map_rule_note_short: 'ફક્ત વાહનો',
	map_imagery_not_live: 'લાઇવ છબી નથી',
	map_scale: 'માપ',
	map_cursor: 'સ્થાન',

	map_layers_title: 'સ્તરો',
	map_basemap_title: 'આધાર નકશો',
	map_basemap_photoreal: 'વાસ્તવિક',
	map_basemap_streets: 'રસ્તાઓ',
	map_basemap_dark: 'ડાર્ક',
	map_basemap_needs_key: 'આ ડેક પર Cesium ion કી જરૂરી છે',
	map_group_traffic: 'ટ્રાફિક',
	map_group_enforcement: 'અમલીકરણ',
	map_group_response: 'પ્રતિભાવ',
	map_group_corridors: 'કોરિડોર',
	map_group_intelligence: 'નોંધાયેલી ઘટનાઓ',
	map_layer_flow: 'ટ્રાફિક પ્રવાહ',
	map_layer_signals: 'જંક્શન અને સિગ્નલ',
	map_layer_anomalies: 'ફીડ વિસંગતિઓ',
	map_layer_traces: 'નિરીક્ષણ યાદીનાં વાહનો',
	map_layer_enforcement: 'નિર્ણય બાકી',
	map_layer_cameras: 'ANPR કેમેરા',
	map_layer_units: 'એકમો',
	map_layer_dispatch: 'રવાનગીઓ',
	map_layer_events: 'ઘટનાઓ અને માર્ગો',
	map_layer_convoy: 'કાફલો',
	map_layer_photoreal: 'વાસ્તવિક 3D શહેર',
	map_layer_paused: 'રીપ્લે ચાલે ત્યાં સુધી અટકેલું',
	map_layer_feed_down: 'ફીડમાં સમસ્યા',

	map_legend_title: 'સંકેત-સૂચિ',
	map_legend_flow: 'ટ્રાફિક પ્રવાહ: મુક્ત → જામ',
	map_legend_flow_simulated: 'ટ્રાફિક પ્રવાહ (સિમ્યુલેટેડ): મુક્ત → જામ',
	map_legend_markers: 'ચિહ્નો',
	map_legend_alert: 'નિરીક્ષણ યાદીનું વાહન અને તેનાં રીડિંગ',
	map_legend_decision: 'એક નિર્ણય બાકી છે',
	map_legend_selected: 'પસંદ કરેલું',
	map_legend_neutral: 'અન્ય વસ્તુઓ: પ્રકાર ચિહ્નથી',
	map_legend_cluster: 'એક જ સ્થાનનાં ચિહ્નો',
	map_legend_route: 'કાફલો અને તેનો માર્ગ',
	map_legend_event: 'કોરિડોર ઘટનાઓ',
	map_legend_close: 'સંકેત-સૂચિ બંધ કરો',

	map_cluster_list: (n) => `અહીં ${String(n)} વસ્તુઓ`,
	map_cluster_spread: 'ફેલાવવા માટે ક્લિક કરો',

	map_proposal_head: (label) => `નકશા પર પ્રસ્તાવ · ${String(label)}`,
	map_proposal_tier: (tier) => `${String(tier)} સ્તર`,
	map_proposal_note: 'તમે લાગુ કરો ત્યાં સુધી કંઈ બદલાતું નથી',

	map_replay_banner: (run) => (run != null ? `રીપ્લે · રન ${String(run)}` : 'રીપ્લે'),
	map_replay_emulated: 'ઇમ્યુલેટેડ',
	map_live_paused: 'લાઇવ સ્તરો અટકેલાં',
	map_live_paused_hint: 'ટેપ ચાલે ત્યારે લાઇવ સ્તરો અટકે છે. ઇનબૉક્સ અને લાઇવ પટ્ટી લાઇવ રહે છે.',

	map_measure_total: (km) => `અંતર ${String(km)}`,
	map_shape_selected: (n) => `આકારમાં ${String(n)} પસંદ કર્યાં`,
	map_shape_filtered: (n) => `આકારની અંદર ${String(n)} બતાવ્યાં`,
};
