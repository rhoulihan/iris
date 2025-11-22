<script lang="ts">
	/**
	 * Button component with multiple variants and sizes
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		/** Button variant style */
		variant?:
			| 'primary'
			| 'secondary'
			| 'accent'
			| 'success'
			| 'warning'
			| 'error'
			| 'ghost'
			| 'link'
			| 'outline';
		/** Button size */
		size?: 'xs' | 'sm' | 'md' | 'lg';
		/** Whether button is disabled */
		disabled?: boolean;
		/** Whether button is loading */
		loading?: boolean;
		/** Button type */
		type?: 'button' | 'submit' | 'reset';
		/** Additional CSS classes */
		class?: string;
		/** Click handler */
		onclick?: () => void;
		/** Button content */
		children?: Snippet;
	}

	let {
		variant = 'primary',
		size = 'md',
		disabled = false,
		loading = false,
		type = 'button',
		class: className = '',
		onclick,
		children
	}: Props = $props();

	// Build CSS classes
	const variantClass =
		variant === 'outline'
			? 'btn-outline'
			: variant === 'link'
				? 'btn-link'
				: variant === 'ghost'
					? 'btn-ghost'
					: `btn-${variant}`;
	const sizeClass = size === 'md' ? '' : `btn-${size}`;
	const classes = `btn ${variantClass} ${sizeClass} ${className}`.trim();
</script>

<button {type} class={classes} disabled={disabled || loading} {onclick}>
	{#if loading}
		<span class="loading loading-spinner loading-sm"></span>
	{/if}
	{#if children}
		{@render children()}
	{/if}
</button>
