<script lang="ts">
	/**
	 * Select dropdown component
	 */

	interface Option {
		value: string | number;
		label: string;
		disabled?: boolean;
	}

	interface Props {
		/** Selected value */
		value?: string | number;
		/** Select options */
		options: Option[];
		/** Select label */
		label?: string;
		/** Placeholder option */
		placeholder?: string;
		/** Error message */
		error?: string;
		/** Whether select is required */
		required?: boolean;
		/** Whether select is disabled */
		disabled?: boolean;
		/** Select size */
		size?: 'xs' | 'sm' | 'md' | 'lg';
		/** Whether select takes full width */
		fullWidth?: boolean;
		/** Additional CSS classes */
		class?: string;
		/** Change handler */
		onchange?: () => void;
	}

	let {
		value = $bindable(''),
		options,
		label,
		placeholder,
		error,
		required = false,
		disabled = false,
		size = 'md',
		fullWidth = false,
		class: className = '',
		onchange
	}: Props = $props();

	const sizeClass = size === 'md' ? '' : `select-${size}`;
	const selectClasses =
		`select select-bordered ${sizeClass} ${error ? 'select-error' : ''} ${fullWidth ? 'w-full' : ''} ${className}`.trim();
</script>

<div class="form-control {fullWidth ? 'w-full' : ''}">
	{#if label}
		<!-- svelte-ignore a11y_label_has_associated_control -->
		<label class="label">
			<span class="label-text">
				{label}
				{#if required}
					<span class="text-error">*</span>
				{/if}
			</span>
		</label>
	{/if}
	<select class={selectClasses} bind:value {disabled} {required} {onchange}>
		{#if placeholder}
			<option value="" disabled selected>{placeholder}</option>
		{/if}
		{#each options as option (option.value)}
			<option value={option.value} disabled={option.disabled}>{option.label}</option>
		{/each}
	</select>
	{#if error}
		<!-- svelte-ignore a11y_label_has_associated_control -->
		<label class="label">
			<span class="label-text-alt text-error">{error}</span>
		</label>
	{/if}
</div>
