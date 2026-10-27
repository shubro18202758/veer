/**
 * /welcome — the reader's language for the server render (the veer_lang cookie, read by the same pure parser the
 * browser and hooks.server.ts use; English when no choice was made). Nothing else is loaded: the page is static.
 */
import type { PageServerLoad } from './$types';
import { langFromCookieHeader } from '$lib/i18n/lang-cookie';

export const load: PageServerLoad = ({ request }) => ({
	lang: langFromCookieHeader(request.headers.get('cookie')) ?? 'en',
});
