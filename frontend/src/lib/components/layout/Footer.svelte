<script lang="ts">
	/**
	 * Footer component with version info and links
	 */

	interface Props {
		/** Application version */
		version?: string;
		/** Build date */
		buildDate?: string;
		/** Show links */
		showLinks?: boolean;
	}

	let { version = '1.0.0', buildDate, showLinks = true }: Props = $props();

	const currentYear = new Date().getFullYear();

	const links = [
		{ href: '/docs', label: 'Documentation' },
		{ href: 'https://github.com/rhoulihan/iris', label: 'GitHub', external: true },
		{ href: '/support', label: 'Support' },
		{ href: '/about', label: 'About' }
	];
</script>

<footer class="footer footer-center p-4 bg-base-200 text-base-content">
	<div class="grid grid-flow-col gap-4">
		{#if showLinks}
			{#each links as link (link.href)}
				<a
					data-sveltekit-preload-data={link.external ? undefined : ''}
					href={link.href}
					class="link link-hover text-sm"
					target={link.external ? '_blank' : undefined}
					rel={link.external ? 'noopener noreferrer' : undefined}
				>
					{link.label}
				</a>
			{/each}
		{/if}
	</div>
	<div class="text-xs text-base-content/70">
		<p>
			IRIS v{version}
			{#if buildDate}
				• Built {buildDate}
			{/if}
		</p>
		<p class="mt-1">© {currentYear} IRIS Development Team • Oracle Database Optimization</p>
	</div>
</footer>
