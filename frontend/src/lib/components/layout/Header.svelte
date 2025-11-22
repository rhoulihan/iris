<script lang="ts">
	/**
	 * Header component with logo, navigation, and user menu
	 */
	import { page } from '$app/stores';
	import ThemeToggle from '../ui/ThemeToggle.svelte';

	interface Props {
		/** Application logo URL */
		logo?: string;
		/** Application title */
		title?: string;
		/** Whether to show navigation */
		showNav?: boolean;
		/** User name for display */
		userName?: string;
	}

	let { logo, title = 'IRIS', showNav = true, userName }: Props = $props();

	const navItems = [
		{ path: '/', label: 'Dashboard' },
		{ path: '/analyze', label: 'Analyze' },
		{ path: '/sessions', label: 'Sessions' },
		{ path: '/recommendations', label: 'Recommendations' },
		{ path: '/config', label: 'Config' }
	];

	function isActive(path: string): boolean {
		return $page.url.pathname === path;
	}
</script>

<header class="navbar bg-base-100 shadow-lg">
	<div class="flex-1">
		<a data-sveltekit-preload-data href="/" class="btn btn-ghost text-xl">
			{#if logo}
				<img src={logo} alt="{title} Logo" class="h-8 w-8" />
			{/if}
			<span class="font-bold">{title}</span>
		</a>
	</div>

	{#if showNav}
		<div class="flex-none hidden lg:flex">
			<ul class="menu menu-horizontal px-1">
				{#each navItems as item (item.path)}
					<li>
						<a
							data-sveltekit-preload-data
							href={item.path}
							class:active={isActive(item.path)}
							class="transition-colors"
						>
							{item.label}
						</a>
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	<div class="flex-none gap-2 flex">
		<!-- Theme Toggle -->
		<ThemeToggle size="sm" />

		{#if userName}
			<div class="dropdown dropdown-end">
				<div tabindex="0" role="button" class="btn btn-ghost btn-circle avatar">
					<div
						class="w-10 rounded-full bg-primary text-primary-content flex items-center justify-center"
					>
						<span class="text-lg font-semibold">{userName.charAt(0).toUpperCase()}</span>
					</div>
				</div>
				<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
				<ul
					tabindex="0"
					class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52"
				>
					<li class="menu-title">
						<span>{userName}</span>
					</li>
					<li><a data-sveltekit-preload-data href="/config">Settings</a></li>
					<li><a data-sveltekit-preload-data href="/logout">Logout</a></li>
				</ul>
			</div>
		{:else}
			<a data-sveltekit-preload-data href="/login" class="btn btn-primary btn-sm">Login</a>
		{/if}
	</div>
</header>
