<script lang="ts" generics="T extends Record<string, any>">
	/**
	 * Data table component with sorting support
	 */
	import type { Snippet } from 'svelte';

	interface Column<T> {
		key: keyof T;
		label: string;
		sortable?: boolean;
		render?: () => string;
	}

	interface Props<T> {
		/** Table columns */
		columns: Column<T>[];
		/** Table data */
		data: T[];
		/** Whether table has zebra coloring */
		zebra?: boolean;
		/** Whether table is compact */
		compact?: boolean;
		/** Row click handler */
		onRowClick?: (_row: T) => void;
		/** Empty state content */
		empty?: Snippet;
		/** Additional CSS classes */
		class?: string;
	}

	let {
		columns,
		data,
		zebra = true,
		compact = false,
		onRowClick,
		empty,
		class: className = ''
	}: Props<T> = $props();

	let sortColumn = $state<keyof T | null>(null);
	let sortDirection = $state<'asc' | 'desc'>('asc');

	const tableClasses =
		`table ${zebra ? 'table-zebra' : ''} ${compact ? 'table-compact' : ''} ${className}`.trim();

	function handleSort(column: Column<T>) {
		if (!column.sortable) return;

		if (sortColumn === column.key) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column.key;
			sortDirection = 'asc';
		}
	}

	const sortedData = $derived(() => {
		if (!sortColumn) return data;

		const col = String(sortColumn);
		return [...data].sort((a, b) => {
			const aVal = String(a[col as keyof T]);
			const bVal = String(b[col as keyof T]);

			if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
			if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
			return 0;
		});
	});
</script>

<div class="overflow-x-auto">
	<table class={tableClasses}>
		<thead>
			<tr>
				{#each columns as column (column.key)}
					<th class:cursor-pointer={column.sortable} onclick={() => handleSort(column)}>
						<div class="flex items-center gap-2">
							<span>{column.label}</span>
							{#if column.sortable && sortColumn === column.key}
								<span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
							{/if}
						</div>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#if sortedData().length === 0}
				<tr>
					<td colspan={columns.length} class="text-center py-8">
						{#if empty}
							{@render empty()}
						{:else}
							<p class="text-base-content/50">No data available</p>
						{/if}
					</td>
				</tr>
			{:else}
				{#each sortedData() as row, idx (idx)}
					<tr
						class:hover={!!onRowClick}
						class:cursor-pointer={!!onRowClick}
						onclick={() => onRowClick?.(row)}
					>
						{#each columns as column (column.key)}
							<td>
								{#if column.render}
									{column.render()}
								{:else}
									{row[column.key]}
								{/if}
							</td>
						{/each}
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>
