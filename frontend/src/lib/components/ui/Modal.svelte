<script lang="ts">
	/**
	 * Modal dialog component
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		/** Whether modal is open */
		open?: boolean;
		/** Modal title */
		title?: string;
		/** Whether modal can be closed by clicking backdrop */
		closeOnBackdrop?: boolean;
		/** Close callback */
		onclose?: () => void;
		/** Additional CSS classes */
		class?: string;
		/** Modal content */
		children?: Snippet;
		/** Modal actions (footer buttons) */
		actions?: Snippet;
	}

	let {
		open = $bindable(false),
		title,
		closeOnBackdrop = true,
		onclose,
		class: className = '',
		children,
		actions
	}: Props = $props();

	function handleBackdropClick() {
		if (closeOnBackdrop) {
			handleClose();
		}
	}

	function handleClose() {
		open = false;
		onclose?.();
	}

	// Close on Escape key
	function handleKeydown(event: { key: string }) {
		if (event.key === 'Escape' && open) {
			handleClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div class="modal modal-open">
		<div
			class="modal-box {className}"
			role="dialog"
			aria-modal="true"
			aria-labelledby="modal-title"
		>
			{#if title}
				<h3 id="modal-title" class="font-bold text-lg mb-4">{title}</h3>
			{/if}

			{#if children}
				<div class="py-4">
					{@render children()}
				</div>
			{/if}

			{#if actions}
				<div class="modal-action">
					{@render actions()}
				</div>
			{/if}

			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
				onclick={handleClose}
				aria-label="Close"
			>
				✕
			</button>
		</div>
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="modal-backdrop bg-black/50" onclick={handleBackdropClick}></div>
	</div>
{/if}
