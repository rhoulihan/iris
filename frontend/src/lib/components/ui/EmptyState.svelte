<script lang="ts">
	/**
	 * Empty state component for when there's no data
	 */
	import type { Snippet } from 'svelte';
	import Button from './Button.svelte';

	interface Props {
		/** Icon or emoji to display */
		icon?: string;
		/** Empty state title */
		title: string;
		/** Empty state description */
		description?: string;
		/** Action button text */
		actionText?: string;
		/** Action button handler */
		onAction?: () => void;
		/** Custom action buttons */
		actions?: Snippet;
		/** Additional CSS classes */
		class?: string;
	}

	let {
		icon = '📭',
		title,
		description,
		actionText,
		onAction,
		actions,
		class: className = ''
	}: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-12 px-4 {className}">
	<div class="text-6xl mb-4">{icon}</div>
	<h3 class="text-xl font-bold text-base-content mb-2">{title}</h3>
	{#if description}
		<p class="text-base-content/70 text-center max-w-md mb-6">{description}</p>
	{/if}
	{#if actions}
		<div class="flex gap-2">
			{@render actions()}
		</div>
	{:else if actionText && onAction}
		<Button variant="primary" onclick={onAction}>{actionText}</Button>
	{/if}
</div>
