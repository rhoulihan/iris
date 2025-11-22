<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Header from '$lib/components/layout/Header.svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import Footer from '$lib/components/layout/Footer.svelte';

	let { children } = $props();

	// Sidebar collapse state (persisted across navigation)
	let sidebarCollapsed = $state(false);

	// TODO: Get from auth store
	let userName = 'Admin';
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>IRIS - Intelligent Recommendation and Inference System</title>
</svelte:head>

<div class="min-h-screen flex flex-col">
	<!-- Header -->
	<Header {userName} />

	<!-- Main content area with sidebar -->
	<div class="flex flex-1">
		<!-- Sidebar -->
		<Sidebar bind:collapsed={sidebarCollapsed} />

		<!-- Page content -->
		<main class="flex-1 p-6 bg-base-100 overflow-y-auto">
			{@render children()}
		</main>
	</div>

	<!-- Footer -->
	<Footer />
</div>
