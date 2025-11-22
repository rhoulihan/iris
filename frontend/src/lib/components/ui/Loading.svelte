<script lang="ts">
	/**
	 * Loading spinner component
	 */

	interface Props {
		/** Loading spinner size */
		size?: 'xs' | 'sm' | 'md' | 'lg';
		/** Loading spinner type */
		type?: 'spinner' | 'dots' | 'ring' | 'ball' | 'bars';
		/** Loading text */
		text?: string;
		/** Whether loading takes full screen */
		fullScreen?: boolean;
		/** Additional CSS classes */
		class?: string;
	}

	let {
		size = 'md',
		type = 'spinner',
		text,
		fullScreen = false,
		class: className = ''
	}: Props = $props();

	const sizeClass = size === 'md' ? '' : `loading-${size}`;
	const loadingClasses = `loading loading-${type} ${sizeClass} ${className}`.trim();

	const containerClasses = fullScreen
		? 'fixed inset-0 flex items-center justify-center bg-base-100/80 z-50'
		: 'flex items-center justify-center';
</script>

<div class={containerClasses}>
	<div class="flex flex-col items-center gap-4">
		<span class={loadingClasses}></span>
		{#if text}
			<p class="text-base-content/70">{text}</p>
		{/if}
	</div>
</div>
