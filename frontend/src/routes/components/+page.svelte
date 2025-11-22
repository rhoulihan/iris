<script lang="ts">
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Alert from '$lib/components/ui/Alert.svelte';
	import Modal from '$lib/components/ui/Modal.svelte';
	import Table from '$lib/components/ui/Table.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import Checkbox from '$lib/components/ui/Checkbox.svelte';
	import Loading from '$lib/components/ui/Loading.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';

	// Modal state
	let modalOpen = $state(false);

	// Table data
	type TableRow = { id: number; name: string; status: string; value: number };
	const tableData: TableRow[] = [
		{ id: 1, name: 'Analysis A', status: 'Complete', value: 95 },
		{ id: 2, name: 'Analysis B', status: 'Pending', value: 42 },
		{ id: 3, name: 'Analysis C', status: 'Complete', value: 78 }
	];

	const tableColumns = [
		{ key: 'id' as const, label: 'ID', sortable: true },
		{ key: 'name' as const, label: 'Name', sortable: true },
		{ key: 'status' as const, label: 'Status', sortable: true },
		{ key: 'value' as const, label: 'Value', sortable: true }
	];

	// Select options
	const selectOptions = [
		{ value: '1', label: 'Option 1' },
		{ value: '2', label: 'Option 2' },
		{ value: '3', label: 'Option 3' }
	];

	// Form state
	let inputValue = $state('');
	let selectValue = $state('');
	let checkboxValue = $state(false);
</script>

<div class="container mx-auto p-6 space-y-8">
	<div>
		<h1 class="text-4xl font-bold mb-2">Component Showcase</h1>
		<p class="text-base-content/70">
			All UI components from Sprint 1.2 - Base UI Components & Layout
		</p>
	</div>

	<!-- Buttons -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Buttons</h2>
		{/snippet}

		<div class="flex flex-wrap gap-3">
			<Button variant="primary">Primary</Button>
			<Button variant="secondary">Secondary</Button>
			<Button variant="accent">Accent</Button>
			<Button variant="success">Success</Button>
			<Button variant="warning">Warning</Button>
			<Button variant="error">Error</Button>
			<Button variant="ghost">Ghost</Button>
			<Button variant="link">Link</Button>
			<Button variant="outline">Outline</Button>
		</div>

		<div class="flex flex-wrap gap-3 mt-4">
			<Button size="xs">Extra Small</Button>
			<Button size="sm">Small</Button>
			<Button size="md">Medium</Button>
			<Button size="lg">Large</Button>
			<Button loading>Loading</Button>
			<Button disabled>Disabled</Button>
		</div>
	</Card>

	<!-- Badges -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Badges</h2>
		{/snippet}

		<div class="flex flex-wrap gap-3">
			<Badge variant="primary">Primary</Badge>
			<Badge variant="secondary">Secondary</Badge>
			<Badge variant="accent">Accent</Badge>
			<Badge variant="completed">Completed</Badge>
			<Badge variant="pending">Pending</Badge>
			<Badge variant="error">Error</Badge>
			<Badge variant="info">Info</Badge>
			<Badge variant="ghost">Ghost</Badge>
		</div>

		<div class="flex flex-wrap gap-3 mt-4">
			<Badge size="sm">Small</Badge>
			<Badge size="md">Medium</Badge>
			<Badge size="lg">Large</Badge>
			<Badge outline>Outline</Badge>
		</div>
	</Card>

	<!-- Alerts -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Alerts</h2>
		{/snippet}

		<div class="space-y-3">
			<Alert type="info" title="Information">This is an informational alert message.</Alert>
			<Alert type="success" title="Success!">Your operation completed successfully.</Alert>
			<Alert type="warning" title="Warning">Please review before proceeding.</Alert>
			<Alert type="error" title="Error" dismissible>
				An error occurred. This alert can be dismissed.
			</Alert>
		</div>
	</Card>

	<!-- Cards -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Cards</h2>
		{/snippet}

		<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
			<Card bordered>
				{#snippet header()}
					<h3 class="font-bold">Card with Border</h3>
				{/snippet}
				<p>This card has a border.</p>
			</Card>

			<Card shadow>
				{#snippet header()}
					<h3 class="font-bold">Card with Shadow</h3>
				{/snippet}
				<p>This card has a shadow.</p>
			</Card>

			<Card compact>
				{#snippet header()}
					<h3 class="font-bold">Compact Card</h3>
				{/snippet}
				<p>This is a compact card.</p>
				{#snippet actions()}
					<Button size="sm">Action</Button>
				{/snippet}
			</Card>
		</div>
	</Card>

	<!-- Form Inputs -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Form Inputs</h2>
		{/snippet}

		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			<Input
				label="Text Input"
				placeholder="Enter text..."
				bind:value={inputValue}
				helper="This is helper text"
				fullWidth
			/>

			<Input type="email" label="Email Input" placeholder="your@email.com" required fullWidth />

			<Select
				label="Select Dropdown"
				placeholder="Choose an option..."
				options={selectOptions}
				bind:value={selectValue}
				fullWidth
			/>

			<div>
				<label class="label">
					<span class="label-text">Checkboxes</span>
				</label>
				<div class="space-y-2">
					<Checkbox label="Option 1" bind:checked={checkboxValue} color="primary" />
					<Checkbox label="Option 2 (Secondary)" color="secondary" />
					<Checkbox label="Option 3 (Accent)" color="accent" />
				</div>
			</div>
		</div>
	</Card>

	<!-- Table -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Table</h2>
		{/snippet}

		<Table columns={tableColumns} data={tableData} zebra compact />
	</Card>

	<!-- Modal -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Modal</h2>
		{/snippet}

		<Button onclick={() => (modalOpen = true)}>Open Modal</Button>

		<Modal bind:open={modalOpen} title="Example Modal">
			<p class="py-4">
				This is a modal dialog. You can click outside, press Escape, or use the buttons below to
				close it.
			</p>

			{#snippet actions()}
				<Button variant="ghost" onclick={() => (modalOpen = false)}>Cancel</Button>
				<Button variant="primary" onclick={() => (modalOpen = false)}>Confirm</Button>
			{/snippet}
		</Modal>
	</Card>

	<!-- Loading States -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Loading Indicators</h2>
		{/snippet}

		<div class="flex flex-wrap gap-6 items-center">
			<div class="text-center">
				<Loading type="spinner" />
				<p class="text-sm mt-2">Spinner</p>
			</div>
			<div class="text-center">
				<Loading type="dots" />
				<p class="text-sm mt-2">Dots</p>
			</div>
			<div class="text-center">
				<Loading type="ring" />
				<p class="text-sm mt-2">Ring</p>
			</div>
			<div class="text-center">
				<Loading type="ball" />
				<p class="text-sm mt-2">Ball</p>
			</div>
			<div class="text-center">
				<Loading type="bars" />
				<p class="text-sm mt-2">Bars</p>
			</div>
		</div>

		<div class="flex gap-3 mt-6">
			<Loading size="xs" />
			<Loading size="sm" />
			<Loading size="md" />
			<Loading size="lg" />
		</div>
	</Card>

	<!-- Empty State -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Empty State</h2>
		{/snippet}

		<EmptyState
			icon="📭"
			title="No Data Available"
			description="There are no items to display at this time. Try creating a new analysis to get started."
		>
			{#snippet actions()}
				<Button variant="primary">Create New Analysis</Button>
			{/snippet}
		</EmptyState>
	</Card>

	<!-- Theme Toggle (already in header) -->
	<Card>
		{#snippet header()}
			<h2 class="text-2xl font-bold">Theme System</h2>
		{/snippet}

		<p class="mb-4">
			The theme toggle is located in the header (top-right corner). It supports three modes:
		</p>
		<ul class="list-disc list-inside space-y-2">
			<li><strong>Light:</strong> Light theme</li>
			<li><strong>Dark:</strong> Dark theme</li>
			<li><strong>Auto:</strong> Automatically follows your system preference</li>
		</ul>
		<p class="mt-4 text-sm text-base-content/70">
			Theme preference is saved in localStorage and persists across sessions.
		</p>
	</Card>
</div>
