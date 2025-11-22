<script lang="ts">
	// Dashboard / Home Page - Sprint 1.1
</script>

<div class="container mx-auto p-6">
	<h1 class="text-4xl font-bold mb-6">IRIS Web Console</h1>

	<div class="alert alert-info mb-6">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			class="stroke-current shrink-0 w-6 h-6"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
			></path>
		</svg>
		<span>✅ Tailwind CSS + DaisyUI is working! Phase 1 Sprint 1.1 in progress.</span>
	</div>

	<div class="stats shadow w-full mb-6">
		<div class="stat">
			<div class="stat-title">Total Analyses</div>
			<div class="stat-value">0</div>
			<div class="stat-desc">All-time</div>
		</div>

		<div class="stat">
			<div class="stat-title">Recommendations</div>
			<div class="stat-value">0</div>
			<div class="stat-desc">Pending review</div>
		</div>

		<div class="stat">
			<div class="stat-title">Estimated Savings</div>
			<div class="stat-value">$0</div>
			<div class="stat-desc">From approved recommendations</div>
		</div>
	</div>

	<div class="flex gap-4">
		<button class="btn btn-primary">New Analysis</button>
		<button class="btn btn-outline">View Recommendations</button>
		<button class="btn btn-outline">Simulations</button>
	</div>
</div>
