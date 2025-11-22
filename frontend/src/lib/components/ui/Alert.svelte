<script lang="ts">
	/**
	 * Alert component for displaying messages
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		/** Alert type */
		type?: 'info' | 'success' | 'warning' | 'error';
		/** Alert title */
		title?: string;
		/** Whether alert is dismissible */
		dismissible?: boolean;
		/** Dismiss callback */
		ondismiss?: () => void;
		/** Additional CSS classes */
		class?: string;
		/** Alert content */
		children?: Snippet;
	}

	let {
		type = 'info',
		title,
		dismissible = false,
		ondismiss,
		class: className = '',
		children
	}: Props = $props();

	let visible = $state(true);

	const classes = `alert alert-${type} ${className}`.trim();

	function handleDismiss() {
		visible = false;
		ondismiss?.();
	}
</script>

{#if visible}
	<div class={classes} role="alert">
		<span class="text-xl"
			>{type === 'info'
				? '  ℹ️'
				: type === 'success'
					? '✅'
					: type === 'warning'
						? '⚠️'
						: '❌'}</span
		>
		<div class="flex-1">
			{#if title}
				<h3 class="font-bold">{title}</h3>
			{/if}
			{#if children}
				<div class="text-sm">
					{@render children()}
				</div>
			{/if}
		</div>
		{#if dismissible}
			<button class="btn btn-sm btn-circle btn-ghost" onclick={handleDismiss} aria-label="Dismiss">
				✕
			</button>
		{/if}
	</div>
{/if}
