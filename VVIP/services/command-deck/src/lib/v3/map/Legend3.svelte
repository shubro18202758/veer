<script lang="ts">
	/**
	 * Legend3 (V3-SPEC §5.6) — three lines, because colour means only state: orange, a decision waits; a red
	 * ring, a stolen or watchlisted vehicle; teal, a protected route. Shape and words carry it too (never colour
	 * alone). Hidden at 1366 px, where the Now list says the same in words.
	 */
	import { t } from '$lib/i18n/strings';
	import Glyph from '../Glyph.svelte';
	import './packs.map3';

	let { lang, hideLabel = null, onhide = null }: { lang: string; hideLabel?: string | null; onhide?: (() => void) | null } = $props();
</script>

<div class="lg v3-glass" role="note" aria-label={t(lang, 'v3m_legend')} data-testid="v3-legend" data-ge-keepout>
	<span><i class="dot" aria-hidden="true"></i>{t(lang, 'v3m_lg_decide')}</span>
	<span><i class="ring" aria-hidden="true"></i>{t(lang, 'v3m_lg_alert')}</span>
	<span><i class="bar" aria-hidden="true"></i>{t(lang, 'v3m_lg_route')}</span>
	{#if onhide}<button type="button" class="x" aria-label={hideLabel} title={hideLabel} onclick={onhide}><Glyph name="close" size={14} /></button>{/if}
</div>

<style>
	.lg {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: 10px 14px;
		border: 1px solid var(--v3-glass-border);
		border-radius: var(--v3-radius-m);
		background: var(--v3-glass-surface);
		box-shadow: var(--v3-elev-1);
		color: var(--v3-t2);
		font-size: var(--v3-text-micro);
		line-height: var(--v3-lh-micro);
		pointer-events: auto;
	}

	span {
		display: flex;
		align-items: center;
		gap: 8px;
		white-space: nowrap;
	}

	.x {
		position: absolute;
		top: 4px;
		right: 4px;
		display: grid;
		place-items: center;
		width: 22px;
		height: 22px;
		border: 0;
		border-radius: 11px;
		background: none;
		color: var(--v3-t2);
		cursor: pointer;
	}

	.x:hover {
		background: var(--v3-s3);
	}

	.x:focus-visible {
		outline: 2px solid var(--v3-brand);
		outline-offset: 2px;
	}

	.lg:has(.x) {
		padding-right: 32px;
	}

	i {
		display: inline-block;
		flex: none;
	}

	.dot {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: var(--v3-decide);
	}

	.ring {
		width: 12px;
		height: 12px;
		border: 3px solid var(--v3-alert);
		border-radius: 50%;
		box-sizing: border-box;
	}

	.bar {
		width: 16px;
		height: 4px;
		border-radius: 2px;
		background: var(--v3-route);
	}
</style>
