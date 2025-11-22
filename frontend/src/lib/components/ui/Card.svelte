<script lang="ts">
	/**
	 * Card component with header, content, and footer slots
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		/** Card title */
		title?: string;
		/** Whether card has shadow */
		shadow?: boolean;
		/** Whether card is bordered */
		bordered?: boolean;
		/** Whether card is compact */
		compact?: boolean;
		/** Additional CSS classes */
		class?: string;
		/** Header content slot */
		header?: Snippet;
		/** Main content slot */
		children?: Snippet;
		/** Footer content slot */
		footer?: Snippet;
		/** Actions slot (right side of header) */
		actions?: Snippet;
	}

	let {
		title,
		shadow = true,
		bordered = false,
		compact = false,
		class: className = '',
		header,
		children,
		footer,
		actions
	}: Props = $props();

	const classes =
		`card bg-base-100 ${shadow ? 'shadow-xl' : ''} ${bordered ? 'bordered' : ''} ${compact ? 'card-compact' : ''} ${className}`.trim();
</script>

<div class={classes}>
	{#if header || title || actions}
		<div class="card-body">
			<div class="flex justify-between items-center">
				{#if header}
					{@render header()}
				{:else if title}
					<h2 class="card-title">{title}</h2>
				{/if}
				{#if actions}
					<div class="card-actions">
						{@render actions()}
					</div>
				{/if}
			</div>
		</div>
	{/if}

	{#if children}
		<div class="card-body {title || header || actions ? 'pt-0' : ''}">
			{@render children()}
		</div>
	{/if}

	{#if footer}
		<div class="card-body pt-0">
			<div class="card-actions justify-end">
				{@render footer()}
			</div>
		</div>
	{/if}
</div>
