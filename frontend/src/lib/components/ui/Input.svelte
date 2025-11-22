<script lang="ts">
	/**
	 * Input component with validation support
	 */

	interface Props {
		/** Input value */
		value?: string | number;
		/** Input type */
		type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
		/** Input placeholder */
		placeholder?: string;
		/** Input label */
		label?: string;
		/** Error message */
		error?: string;
		/** Helper text */
		helper?: string;
		/** Whether input is required */
		required?: boolean;
		/** Whether input is disabled */
		disabled?: boolean;
		/** Input size */
		size?: 'xs' | 'sm' | 'md' | 'lg';
		/** Whether input takes full width */
		fullWidth?: boolean;
		/** Additional CSS classes */
		class?: string;
		/** Input change handler */
		oninput?: () => void;
	}

	let {
		value = $bindable(''),
		type = 'text',
		placeholder,
		label,
		error,
		helper,
		required = false,
		disabled = false,
		size = 'md',
		fullWidth = false,
		class: className = '',
		oninput
	}: Props = $props();

	const sizeClass = size === 'md' ? '' : `input-${size}`;
	const inputClasses =
		`input input-bordered ${sizeClass} ${error ? 'input-error' : ''} ${fullWidth ? 'w-full' : ''} ${className}`.trim();
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
	<input {type} {placeholder} {disabled} {required} class={inputClasses} bind:value {oninput} />
	{#if error}
		<!-- svelte-ignore a11y_label_has_associated_control -->
		<label class="label">
			<span class="label-text-alt text-error">{error}</span>
		</label>
	{:else if helper}
		<!-- svelte-ignore a11y_label_has_associated_control -->
		<label class="label">
			<span class="label-text-alt">{helper}</span>
		</label>
	{/if}
</div>
