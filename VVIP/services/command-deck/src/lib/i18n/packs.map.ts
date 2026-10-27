/**
 * Map chrome string pack (EN / HI / GU) — the canvas's toolbar, navigation,
 * readout, LayerTree, legend, map proposals and replay banner (SPEC §5.3,
 * chrome="v2"), plus the honest imagery chip's words (`ge_imagery_*`, moved
 * here from gods-eye/layers/basemap.ts and converted to sentence case with
 * their test, basemap.unit.mjs).
 *
 * Every new key starts with `map_`. EN is sentence case, no ALL-CAPS word
 * outside the acronym allowlist, at most one " · " per string, titles at
 * most 32 characters (tests/copy-lint.mjs; targets file
 * style-lint.targets/s3.json). Operational names stay Latin in every
 * language (OSM, Google, ion, 3D), like the deck's other codes. Registered
 * additively through registerPack(); the core packs stay untouched.
 *
 * Copy describes only what the system does (SPEC §9.1): FLIR is a
 * thermal-STYLE rendering of the visible scene, no thermal sensor exists;
 * a map proposal moves nothing until a person applies it.
 */
import { registerPack } from './strings';
import { langChunks } from './load';

type Fn = (...args: unknown[]) => string;
type MapPack = Record<string, string | Fn>;

const en = {
	// honest imagery chip (legacy chrome) and the base-map note (v2)
	ge_imagery_photoreal: 'Photoreal 3D · Google',
	ge_imagery_photoreal_loading: 'Photoreal 3D · loading',
	ge_imagery_ion: 'Ion aerial · 3D terrain',
	ge_imagery_osm: 'OSM · dark',
	ge_imagery_osm_fallback: 'OSM dark (fallback)',
	ge_imagery_offline: 'Offline schematic mode',

	// toolbar
	map_toolbar: 'Map tools',
	map_tool_select: 'Select',
	map_tool_shape: 'Select within a shape',
	map_tool_shape_menu: 'Shape options',
	map_tool_shape_select: 'Select within shape',
	map_tool_shape_filter: 'Filter to shape',
	map_tool_shape_clear: 'Clear the shape filter',
	map_tool_shape_hint: 'Click points on the map, then double-click to close the shape',
	map_tool_search_around: 'Search around the selection',
	map_tool_search_around_none: 'Select an object first',
	map_tool_measure: 'Measure distance',
	map_tool_measure_hint: 'Click points on the map; double-click or Esc to finish',
	map_tool_layers: 'Layers',
	map_tool_legend: 'Legend',
	map_tool_follow: 'Follow the selection',
	map_tool_follow_none: 'Select something to follow',
	map_tool_following: (name) => (name != null && name !== '' ? `Following ${String(name)}` : 'Following the selection'),
	map_follow_no_position: (name) =>
		name != null && name !== '' ? `${String(name)} has no position on the map to follow` : 'The selection has no position on the map to follow',
	map_tool_tour: 'Guided tour',
	map_tool_tour_stop: 'Stop the guided tour',
	map_tool_exit: 'Exit map mode',
	map_mode_live: 'Live',
	map_mode_window: 'Not live',
	map_mode_replay: (run) => (run != null ? `Replay · run ${String(run)}` : 'Replay'),
	map_mode_live_tip: 'Live. Open the timeline to set a window or play a replay.',
	map_mode_window_tip: 'A time window is set. Open the timeline to return to live.',
	map_mode_replay_tip: 'A recorded tape is playing on its own time axis.',

	// the thermal-STYLE view: a toolbar button of its own (SPEC §16.5,
	// confirmed the other way 2026-10-25 — one click away, never a sensor)
	map_tool_thermal: 'Thermal-style view',
	map_tool_thermal_tip: 'Thermal-style view — a visual filter, no thermal sensor',
	map_thermal_on: 'Thermal-style view (visual filter)',
	map_flir_note: 'Visual filter, no thermal sensor',
	map_flir_off: 'Normal colours',
	map_flir_whot: 'Thermal style, white hot',
	map_flir_bhot: 'Thermal style, black hot',
	map_flir_iron: 'Thermal style, ironbow',
	// FIX-E-LOOKUP: the palettes in words (the omnibar's sensor command names
	// the picked palette through these — never the raw flir-* id)
	map_pal_raw: 'normal colours',
	map_pal_whot: 'white hot',
	map_pal_bhot: 'black hot',
	map_pal_iron: 'ironbow',

	// navigation and readout
	map_zoom_in: 'Zoom in',
	map_zoom_out: 'Zoom out',
	map_reset_north: 'Reset north',
	map_rule_note: 'Vehicles only · penalties need a named officer',
	map_rule_note_short: 'Vehicles only',
	map_imagery_not_live: 'not a live image',
	map_scale: 'Scale',
	map_cursor: 'Position',

	// LayerTree
	map_layers_title: 'Layers',
	map_basemap_title: 'Base map',
	map_basemap_photoreal: 'Photoreal',
	map_basemap_streets: 'Streets',
	map_basemap_dark: 'Dark',
	map_basemap_needs_key: 'Needs the Cesium ion key on this deck',
	map_group_traffic: 'Traffic',
	map_group_enforcement: 'Enforcement',
	map_group_response: 'Response',
	map_group_corridors: 'Corridors',
	map_group_intelligence: 'Reported events',
	map_layer_flow: 'Traffic flow',
	map_layer_signals: 'Junctions and signals',
	map_layer_anomalies: 'Feed anomalies',
	map_layer_traces: 'Watchlisted vehicles',
	map_layer_enforcement: 'Decisions waiting',
	map_layer_cameras: 'ANPR cameras',
	map_layer_units: 'Units',
	map_layer_dispatch: 'Dispatches',
	map_layer_events: 'Events and routes',
	map_layer_convoy: 'Convoy',
	map_layer_photoreal: 'Photoreal 3D city',
	map_layer_paused: 'Paused while the replay plays',
	map_layer_feed_down: 'Feed problem',

	// legend
	map_legend_title: 'Legend',
	map_legend_flow: 'Traffic flow: free → jammed',
	map_legend_flow_simulated: 'Traffic flow (simulated): free → jammed',
	map_legend_markers: 'Markers',
	map_legend_alert: 'Watchlisted vehicle and its reads',
	map_legend_decision: 'A decision is waiting',
	map_legend_selected: 'Selected',
	map_legend_neutral: 'Other objects: type by glyph',
	map_legend_cluster: 'Co-located markers',
	map_legend_route: 'Convoy and its route',
	map_legend_event: 'Corridor events',
	map_legend_close: 'Close the legend',

	// clusters and labels
	map_cluster_list: (n) => `${String(n)} objects here`,
	map_cluster_spread: 'Click to spread them out',

	// map proposals (the home of map proposals, SPEC §5.4)
	map_proposal_head: (label) => `Proposed on the map · ${String(label)}`,
	map_proposal_tier: (tier) => `${String(tier)} tier`,
	map_proposal_note: 'Nothing moves until you apply it',

	// replay banner (SPEC §7.3, §9: a replay names its provenance — an
	// emulator tape is an emulated recording; a live capture is never so
	// labelled)
	map_replay_banner: (run) => (run != null ? `Replay · run ${String(run)}` : 'Replay'),
	map_replay_emulated: 'Emulated',
	map_live_paused: 'live layers paused',
	map_live_paused_hint: 'The live layers stand down while the tape plays. The inbox and the live strip stay live.',

	// shape and measure results
	map_measure_total: (km) => `Distance ${String(km)}`,
	map_shape_selected: (n) => `${String(n)} selected in the shape`,
	map_shape_filtered: (n) => `${String(n)} shown inside the shape`,
} satisfies MapPack;

export type MapKey = keyof typeof en;

const hi: Record<MapKey, string | Fn> = {
	ge_imagery_photoreal: 'यथार्थ 3D शहर · Google',
	ge_imagery_photoreal_loading: 'यथार्थ 3D · लोड हो रहा है',
	ge_imagery_ion: 'ion हवाई चित्र · 3D भू-भाग',
	ge_imagery_osm: 'OSM · डार्क',
	ge_imagery_osm_fallback: 'OSM डार्क (वैकल्पिक)',
	ge_imagery_offline: 'ऑफ़लाइन योजनाबद्ध मोड',

	map_toolbar: 'मानचित्र उपकरण',
	map_tool_select: 'चुनें',
	map_tool_shape: 'आकृति के भीतर चुनें',
	map_tool_shape_menu: 'आकृति विकल्प',
	map_tool_shape_select: 'आकृति के भीतर चुनें',
	map_tool_shape_filter: 'आकृति तक सीमित करें',
	map_tool_shape_clear: 'आकृति फ़िल्टर हटाएँ',
	map_tool_shape_hint: 'मानचित्र पर बिंदु चुनें, फिर आकृति बंद करने के लिए डबल-क्लिक करें',
	map_tool_search_around: 'चयन के आसपास खोजें',
	map_tool_search_around_none: 'पहले कोई वस्तु चुनें',
	map_tool_measure: 'दूरी मापें',
	map_tool_measure_hint: 'मानचित्र पर बिंदु चुनें; समाप्त करने के लिए डबल-क्लिक या Esc',
	map_tool_layers: 'परतें',
	map_tool_legend: 'संकेत-सूची',
	map_tool_follow: 'चयन का अनुसरण करें',
	map_tool_follow_none: 'अनुसरण के लिए कुछ चुनें',
	map_tool_following: (name) => (name != null && name !== '' ? `${String(name)} का अनुसरण` : 'चयन का अनुसरण'),
	map_follow_no_position: (name) =>
		name != null && name !== ''
			? `${String(name)} की मानचित्र पर कोई स्थिति नहीं है, अनुसरण संभव नहीं`
			: 'चयन की मानचित्र पर कोई स्थिति नहीं है, अनुसरण संभव नहीं',
	map_tool_tour: 'निर्देशित भ्रमण',
	map_tool_tour_stop: 'निर्देशित भ्रमण रोकें',
	map_tool_exit: 'मानचित्र मोड से बाहर',
	map_mode_live: 'लाइव',
	map_mode_window: 'लाइव नहीं',
	map_mode_replay: (run) => (run != null ? `रीप्ले · रन ${String(run)}` : 'रीप्ले'),
	map_mode_live_tip: 'लाइव। समय-सीमा या रीप्ले के लिए टाइमलाइन खोलें।',
	map_mode_window_tip: 'समय-सीमा लगी है। लाइव पर लौटने के लिए टाइमलाइन खोलें।',
	map_mode_replay_tip: 'एक रिकॉर्ड की गई टेप अपनी समय-अक्ष पर चल रही है।',

	// FIX-E-LOOKUP: "दृश्य … (दृश्य फ़िल्टर)" नहीं — दृश्य शब्द एक बार; फ़िल्टर विज़ुअल फ़िल्टर
	map_tool_thermal: 'थर्मल-शैली दृश्य',
	map_tool_thermal_tip: 'थर्मल-शैली दृश्य — केवल एक विज़ुअल फ़िल्टर, कोई थर्मल सेंसर नहीं',
	map_thermal_on: 'थर्मल-शैली दृश्य (विज़ुअल फ़िल्टर)',
	map_flir_note: 'विज़ुअल फ़िल्टर, कोई थर्मल सेंसर नहीं',
	map_flir_off: 'सामान्य रंग',
	map_flir_whot: 'थर्मल शैली, सफ़ेद गर्म',
	map_flir_bhot: 'थर्मल शैली, काला गर्म',
	map_flir_iron: 'थर्मल शैली, आयरनबो',
	map_pal_raw: 'सामान्य रंग',
	map_pal_whot: 'सफ़ेद गर्म',
	map_pal_bhot: 'काला गर्म',
	map_pal_iron: 'आयरनबो',

	map_zoom_in: 'ज़ूम इन',
	map_zoom_out: 'ज़ूम आउट',
	map_reset_north: 'उत्तर दिशा पर लौटें',
	map_rule_note: 'केवल वाहन · दंड के लिए नामित अधिकारी आवश्यक',
	map_rule_note_short: 'केवल वाहन',
	map_imagery_not_live: 'लाइव तस्वीर नहीं',
	map_scale: 'पैमाना',
	map_cursor: 'स्थिति',

	map_layers_title: 'परतें',
	map_basemap_title: 'आधार मानचित्र',
	map_basemap_photoreal: 'यथार्थ',
	map_basemap_streets: 'सड़कें',
	map_basemap_dark: 'डार्क',
	map_basemap_needs_key: 'इस डेक पर Cesium ion कुंजी आवश्यक है',
	map_group_traffic: 'यातायात',
	map_group_enforcement: 'प्रवर्तन',
	map_group_response: 'प्रतिक्रिया',
	map_group_corridors: 'कॉरिडोर',
	map_group_intelligence: 'रिपोर्ट की गई घटनाएँ',
	map_layer_flow: 'यातायात प्रवाह',
	map_layer_signals: 'जंक्शन और सिग्नल',
	map_layer_anomalies: 'फ़ीड विसंगतियाँ',
	map_layer_traces: 'निगरानी सूची के वाहन',
	map_layer_enforcement: 'निर्णय प्रतीक्षित',
	map_layer_cameras: 'ANPR कैमरे',
	map_layer_units: 'इकाइयाँ',
	map_layer_dispatch: 'प्रेषण',
	map_layer_events: 'घटनाएँ और मार्ग',
	map_layer_convoy: 'काफ़िला',
	map_layer_photoreal: 'यथार्थ 3D शहर',
	map_layer_paused: 'रीप्ले चलते समय रुका हुआ',
	map_layer_feed_down: 'फ़ीड में समस्या',

	map_legend_title: 'संकेत-सूची',
	map_legend_flow: 'यातायात प्रवाह: मुक्त → जाम',
	map_legend_flow_simulated: 'यातायात प्रवाह (सिम्युलेटेड): मुक्त → जाम',
	map_legend_markers: 'चिह्न',
	map_legend_alert: 'निगरानी सूची का वाहन और उसकी रीडिंग',
	map_legend_decision: 'एक निर्णय प्रतीक्षित है',
	map_legend_selected: 'चयनित',
	map_legend_neutral: 'अन्य वस्तुएँ: प्रकार चिह्न से',
	map_legend_cluster: 'एक ही स्थान के चिह्न',
	map_legend_route: 'काफ़िला और उसका मार्ग',
	map_legend_event: 'कॉरिडोर घटनाएँ',
	map_legend_close: 'संकेत-सूची बंद करें',

	map_cluster_list: (n) => `यहाँ ${String(n)} वस्तुएँ`,
	map_cluster_spread: 'फैलाने के लिए क्लिक करें',

	map_proposal_head: (label) => `मानचित्र पर प्रस्ताव · ${String(label)}`,
	map_proposal_tier: (tier) => `${String(tier)} स्तर`,
	map_proposal_note: 'लागू करने तक कुछ नहीं बदलता',

	map_replay_banner: (run) => (run != null ? `रीप्ले · रन ${String(run)}` : 'रीप्ले'),
	map_replay_emulated: 'इम्यूलेटेड',
	map_live_paused: 'लाइव परतें रुकी हुई',
	map_live_paused_hint: 'टेप चलते समय लाइव परतें रुकती हैं। इनबॉक्स और लाइव पट्टी लाइव रहती हैं।',

	map_measure_total: (km) => `दूरी ${String(km)}`,
	map_shape_selected: (n) => `आकृति में ${String(n)} चयनित`,
	map_shape_filtered: (n) => `आकृति के भीतर ${String(n)} दिखाए गए`,
};

const gu: Record<MapKey, string | Fn> = {
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

registerPack('en', en);

/**
 * Register one language chunk (lib/i18n/load.ts's landing site; additive,
 * first registration wins — the core's documented semantics).
 */
export function adopt(code: 'hi' | 'gu', pack: Record<string, string | Fn>): void {
	registerPack(code, pack);
}

/*
 * Language chunks (FIX-E-PERF2): the HI and GU strings that RUN live ONLY in
 * ./packs.map.hi.ts and ./packs.map.gu.ts. The server render and every non-production
 * run (vite dev, the node test harness) register both before this module
 * finishes evaluating (SSR paints the persisted language). The production
 * browser registers the loader instead and awaits the document's language
 * before this module finishes evaluating — hydration waits for it, so a cold
 * HI/GU load never flashes English — and the other language loads on the
 * first switch (lib/i18n/load.ts). The prod client build folds the condition
 * to its else branch.
 */
if (process.env.NODE_ENV !== 'production' || import.meta.env.SSR !== false) {
	adopt('hi', (await import('./packs.map.hi')).hi);
	adopt('gu', (await import('./packs.map.gu')).gu);
} else {
	await langChunks('packs.map', (code) =>
		code === 'hi' ? import('./packs.map.hi').then((c) => adopt('hi', c.hi)) : import('./packs.map.gu').then((c) => adopt('gu', c.gu)),
	);
}

/*
 * TEXT MIRROR — not a source, never registered, never shipped. The `hi` and
 * `gu` literals above are a byte-identical copy of ./packs.map.hi.ts and
 * ./packs.map.gu.ts kept ONLY because two tests outside this work package
 * (tests/thermal-toolbar.unit.mjs, tests/omnibar-lookup.unit.mjs) read the
 * HI/GU strings as TypeScript AST off `registerPack('hi'|'gu', …)` calls in
 * THIS file. This function is never called (every bundle drops it and the
 * literals with it); tests/perf2.unit.mjs pins this copy and the shipped
 * copy, each on its own, to the reviewed golden, so the two can never drift.
 * Delete it once those tests read the per-language modules (FIX-E-PERF2
 * report, blocked request).
 */
function astTextMirror(): void {
	registerPack('hi', hi);
	registerPack('gu', gu);
}

/** Every key of the pack (tests check HI and GU cover each one). */
export const MAP_PACK_KEYS: readonly MapKey[] = Object.keys(en) as MapKey[];
