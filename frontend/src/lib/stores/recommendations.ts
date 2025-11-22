/**
 * Recommendations store
 * Manages state for recommendations
 */

import { writable, derived } from 'svelte/store';
import type { Recommendation } from '$lib/types';

interface RecommendationsState {
	recommendations: Recommendation[];
	loading: boolean;
	error: string | null;
	filters: {
		pattern_type?: string;
		status?: string;
		min_confidence?: number;
	};
}

const initialState: RecommendationsState = {
	recommendations: [],
	loading: false,
	error: null,
	filters: {}
};

function createRecommendationsStore() {
	const { subscribe, set, update } = writable<RecommendationsState>(initialState);

	return {
		subscribe,
		setRecommendations: (recommendations: Recommendation[]) => {
			update((state) => ({ ...state, recommendations, error: null }));
		},
		setLoading: (loading: boolean) => {
			update((state) => ({ ...state, loading }));
		},
		setError: (error: string | null) => {
			update((state) => ({ ...state, error }));
		},
		updateRecommendation: (id: string, updates: Partial<Recommendation>) => {
			update((state) => ({
				...state,
				recommendations: state.recommendations.map((r) => (r.id === id ? { ...r, ...updates } : r))
			}));
		},
		setFilters: (filters: RecommendationsState['filters']) => {
			update((state) => ({ ...state, filters }));
		},
		reset: () => set(initialState)
	};
}

export const recommendationsStore = createRecommendationsStore();

// Derived stores
export const pendingRecommendations = derived(recommendationsStore, ($store) =>
	$store.recommendations.filter((r) => r.status === 'pending')
);

export const approvedRecommendations = derived(recommendationsStore, ($store) =>
	$store.recommendations.filter((r) => r.status === 'approved')
);

export const totalEstimatedSavings = derived(recommendationsStore, ($store) =>
	$store.recommendations
		.filter((r) => r.status === 'approved')
		.reduce((sum, r) => sum + r.estimated_savings, 0)
);

export const filteredRecommendations = derived(recommendationsStore, ($store) => {
	let filtered = $store.recommendations;

	if ($store.filters.pattern_type) {
		filtered = filtered.filter((r) => r.pattern_type === $store.filters.pattern_type);
	}

	if ($store.filters.status) {
		filtered = filtered.filter((r) => r.status === $store.filters.status);
	}

	if ($store.filters.min_confidence !== undefined) {
		filtered = filtered.filter((r) => r.confidence >= $store.filters.min_confidence!);
	}

	return filtered;
});
