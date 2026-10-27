/**
 * The few strings the operator bar adds under the V3 shell (V3-P6B): the Analyst sub-nav's names. Everything else the
 * bar prints reuses the deck's existing keys (shell_band, shell_inbox_*, shell_data, shell_policies, nav_ops, shell_live …),
 * so no existing string changes. EN, HI and GU together (five keys, so no per-language chunk); registered additively.
 * Every key starts with `v3s_`.
 */
import { registerPack } from '$lib/i18n/strings';

const en = {
	v3s_analyst_nav: 'Analyst views',
	v3s_tab_workspace: 'Workspace',
	v3s_tab_wall: 'Situation wall',
	v3s_tab_city: 'City map',
	v3s_tab_assistant: 'Assistant',
};

const hi = {
	v3s_analyst_nav: 'विश्लेषक के दृश्य',
	v3s_tab_workspace: 'कार्यक्षेत्र',
	v3s_tab_wall: 'स्थिति दीवार',
	v3s_tab_city: 'शहर का मानचित्र',
	v3s_tab_assistant: 'सहायक',
};

const gu = {
	v3s_analyst_nav: 'વિશ્લેષકના દૃશ્યો',
	v3s_tab_workspace: 'કાર્યક્ષેત્ર',
	v3s_tab_wall: 'સ્થિતિ દીવાલ',
	v3s_tab_city: 'શહેરનો નકશો',
	v3s_tab_assistant: 'સહાયક',
};

registerPack('en', en);
registerPack('hi', hi);
registerPack('gu', gu);

export const SHELL_PACKS = { en, hi, gu };
