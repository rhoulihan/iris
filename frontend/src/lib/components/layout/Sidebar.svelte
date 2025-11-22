<script lang="ts">
	/**
	 * Sidebar component with collapsible navigation
	 */
	import { page } from '$app/stores';

	interface NavItem {
		path: string;
		label: string;
		icon?: string;
		children?: NavItem[];
	}

	interface Props {
		/** Whether sidebar is collapsed */
		collapsed?: boolean;
		/** Navigation items */
		items?: NavItem[];
	}

	const defaultItems: NavItem[] = [
		{ path: '/', label: 'Dashboard', icon: '📊' },
		{ path: '/analyze', label: 'New Analysis', icon: '🔍' },
		{
			path: '/sessions',
			label: 'Analysis History',
			icon: '📁',
			children: [
				{ path: '/sessions', label: 'All Sessions' },
				{ path: '/sessions/recent', label: 'Recent' }
			]
		},
		{
			path: '/recommendations',
			label: 'Recommendations',
			icon: '💡',
			children: [
				{ path: '/recommendations', label: 'All' },
				{ path: '/recommendations/approved', label: 'Approved' },
				{ path: '/recommendations/pending', label: 'Pending' }
			]
		},
		{ path: '/simulations', label: 'Simulations', icon: '🧪' },
		{ path: '/connections', label: 'Connections', icon: '🔌' },
		{ path: '/config', label: 'Configuration', icon: '⚙️' }
	];

	let { collapsed = $bindable(false), items = defaultItems }: Props = $props();

	let expandedSections = $state<string[]>([]);

	function isActive(itemPath: string): boolean {
		return $page.url.pathname === itemPath || $page.url.pathname.startsWith(itemPath + '/');
	}

	function toggleSection(path: string): void {
		if (expandedSections.includes(path)) {
			expandedSections = expandedSections.filter((p) => p !== path);
		} else {
			expandedSections = [...expandedSections, path];
		}
	}

	function toggleCollapse(): void {
		collapsed = !collapsed;
	}
</script>

<aside
	class="bg-base-200 min-h-screen transition-all duration-300 {collapsed
		? 'w-16'
		: 'w-64'} flex flex-col"
>
	<!-- Toggle button -->
	<div class="p-4 flex justify-end">
		<button
			onclick={toggleCollapse}
			class="btn btn-ghost btn-sm btn-circle"
			aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
		>
			{collapsed ? '→' : '←'}
		</button>
	</div>

	<!-- Navigation -->
	<nav class="flex-1 overflow-y-auto">
		<ul class="menu p-2">
			{#each items as item (item.path)}
				<li>
					{#if item.children && item.children.length > 0}
						<!-- Section with children -->
						<details open={expandedSections.includes(item.path)}>
							<summary
								onclick={(e) => {
									e.preventDefault();
									toggleSection(item.path);
								}}
								class:active={isActive(item.path)}
							>
								{#if !collapsed}
									<span class="mr-2">{item.icon}</span>
									<span>{item.label}</span>
								{:else}
									<span title={item.label}>{item.icon}</span>
								{/if}
							</summary>
							{#if !collapsed}
								<ul>
									{#each item.children as child (child.path)}
										<li>
											<a
												data-sveltekit-preload-data
												href={child.path}
												class:active={isActive(child.path)}
											>
												{child.label}
											</a>
										</li>
									{/each}
								</ul>
							{/if}
						</details>
					{:else}
						<!-- Simple link -->
						<a data-sveltekit-preload-data href={item.path} class:active={isActive(item.path)}>
							{#if !collapsed}
								<span class="mr-2">{item.icon}</span>
								<span>{item.label}</span>
							{:else}
								<span title={item.label}>{item.icon}</span>
							{/if}
						</a>
					{/if}
				</li>
			{/each}
		</ul>
	</nav>

	<!-- Version info at bottom -->
	{#if !collapsed}
		<div class="p-4 text-center text-xs text-base-content/50">
			<p>IRIS v1.0.0</p>
			<p class="mt-1">Phase 6: Web Console</p>
		</div>
	{/if}
</aside>
