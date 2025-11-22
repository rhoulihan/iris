<script lang="ts">
	/**
	 * Theme toggle component for switching between light/dark/auto themes
	 */
	import { theme, setTheme, type Theme } from '$lib/stores/theme';
	import Button from './Button.svelte';

	interface Props {
		/** Show labels next to icons */
		showLabels?: boolean;
		/** Button size */
		size?: 'xs' | 'sm' | 'md' | 'lg';
	}

	let { showLabels = false, size = 'sm' }: Props = $props();

	const themes: { value: Theme; icon: string; label: string }[] = [
		{ value: 'light', icon: '☀️', label: 'Light' },
		{ value: 'dark', icon: '🌙', label: 'Dark' },
		{ value: 'auto', icon: '🔄', label: 'Auto' }
	];

	function handleThemeChange(newTheme: Theme) {
		setTheme(newTheme);
	}
</script>

<div class="flex gap-1">
	{#each themes as { value, icon, label } (value)}
		<Button
			variant={$theme === value ? 'primary' : 'ghost'}
			{size}
			onclick={() => handleThemeChange(value)}
			class="gap-1"
		>
			<span>{icon}</span>
			{#if showLabels}
				<span class="hidden sm:inline">{label}</span>
			{/if}
		</Button>
	{/each}
</div>
