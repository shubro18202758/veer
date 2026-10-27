/**
 * The map-style strings (V3-P4C) — the few words of MapStyleSwitch, in all three languages in one tiny file because the
 * switch also sits in the header menu of every V3 page (so these cannot wait for the /map pack, packs.map3). Registered
 * additively (registerPack; first registration wins). Every key starts with `v3ms_`. Same copy rules as the /map pack:
 * sentence case, at most one " · " per string, and the honest label — satellite imagery is a photograph taken some time
 * ago, never a live image.
 */
import { registerPack } from '$lib/i18n/strings';

export const MAPSTYLE_PACKS = {
	en: {
		v3ms_label: 'Map style',
		v3ms_satellite: 'Satellite',
		v3ms_map: 'Map',
		v3ms_tip_satellite: 'Natural-colour satellite imagery · not a live image',
		v3ms_tip_map: 'The night map, drawn from OpenStreetMap',
		v3ms_needs_key: 'Needs the Cesium ion key on this deck',
		v3ms_paused: 'Satellite imagery is paused for this session. The map shows instead.',
		v3ms_hint: 'Applies to the maps on Home, Decide and the pages of a vehicle or a place.',
	},
	hi: {
		v3ms_label: 'मानचित्र शैली',
		v3ms_satellite: 'उपग्रह',
		v3ms_map: 'मानचित्र',
		v3ms_tip_satellite: 'प्राकृतिक रंगों में उपग्रह चित्र · लाइव चित्र नहीं',
		v3ms_tip_map: 'रात का मानचित्र, OpenStreetMap से बना',
		v3ms_needs_key: 'इस डेक पर Cesium ion कुंजी आवश्यक है',
		v3ms_paused: 'इस सत्र के लिए उपग्रह चित्र रुके हैं। इसके बदले मानचित्र दिखेगा।',
		v3ms_hint: 'होम, निर्णय और वाहन या स्थान के पन्नों के मानचित्रों पर लागू।',
	},
	gu: {
		v3ms_label: 'નકશાની શૈલી',
		v3ms_satellite: 'ઉપગ્રહ',
		v3ms_map: 'નકશો',
		v3ms_tip_satellite: 'કુદરતી રંગોમાં ઉપગ્રહ છબી · લાઇવ છબી નથી',
		v3ms_tip_map: 'રાત્રિનો નકશો, OpenStreetMap પરથી બનેલો',
		v3ms_needs_key: 'આ ડેક પર Cesium ion કી જરૂરી છે',
		v3ms_paused: 'આ સત્ર માટે ઉપગ્રહ છબી થોભાવી છે. તેના બદલે નકશો દેખાશે.',
		v3ms_hint: 'હોમ, નિર્ણય અને વાહન કે સ્થળના પાનાંના નકશા પર લાગુ.',
	},
} as const;

for (const [code, pack] of Object.entries(MAPSTYLE_PACKS)) registerPack(code, pack);
