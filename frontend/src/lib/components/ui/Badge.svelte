<script lang="ts">
	/**
	 * Badge component for status indicators
	 */
	import type { Snippet } from 'svelte';
	import { STATUS_COLORS } from '$lib/utils/constants';

	interface Props {
		/** Badge variant/color */
		variant?: keyof typeof STATUS_COLORS | 'primary' | 'secondary' | 'accent' | 'info' | 'ghost';
		/** Badge size */
		size?: 'xs' | 'sm' | 'md' | 'lg';
		/** Whether badge is outlined */
		outline?: boolean;
		/** Additional CSS classes */
		class?: string;
		/** Badge content */
		children?: Snippet;
	}

	let {
		variant = 'primary',
		size = 'md',
		outline = false,
		class: className = '',
		children
	}: Props = $props();

	// Get badge color from constants if it's a status
	const badgeColor =
		variant in STATUS_COLORS
			? STATUS_COLORS[variant as keyof typeof STATUS_COLORS]
			: `badge-${variant}`;
	const sizeClass = size === 'md' ? '' : `badge-${size}`;
	const classes =
		`badge ${badgeColor} ${sizeClass} ${outline ? 'badge-outline' : ''} ${className}`.trim();
</script>

<div class={classes}>
	{#if children}
		{@render children()}
	{/if}
</div>
