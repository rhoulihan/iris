<script lang="ts">
	/**
	 * Checkbox component
	 */

	interface Props {
		/** Checked state */
		checked?: boolean;
		/** Checkbox label */
		label?: string;
		/** Whether checkbox is disabled */
		disabled?: boolean;
		/** Checkbox size */
		size?: 'xs' | 'sm' | 'md' | 'lg';
		/** Checkbox color */
		color?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error';
		/** Additional CSS classes */
		class?: string;
		/** Change handler */
		onchange?: () => void;
	}

	let {
		checked = $bindable(false),
		label,
		disabled = false,
		size = 'md',
		color = 'primary',
		class: className = '',
		onchange
	}: Props = $props();

	const sizeClass = size === 'md' ? '' : `checkbox-${size}`;
	const colorClass = `checkbox-${color}`;
	const checkboxClasses = `checkbox ${sizeClass} ${colorClass} ${className}`.trim();
</script>

<div class="form-control">
	<label class="label cursor-pointer justify-start gap-3">
		<input type="checkbox" class={checkboxClasses} bind:checked {disabled} {onchange} />
		{#if label}
			<span class="label-text">{label}</span>
		{/if}
	</label>
</div>
