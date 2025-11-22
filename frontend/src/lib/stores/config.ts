/**
 * Configuration store
 * Manages application configuration state
 */

import { writable } from 'svelte/store';
import type { AnalysisConfig } from '$lib/types';
import { DEFAULT_ANALYSIS_CONFIG } from '$lib/utils/constants';

interface ConfigState {
	analysisConfig: AnalysisConfig;
	loading: boolean;
	error: string | null;
}

const initialState: ConfigState = {
	analysisConfig: DEFAULT_ANALYSIS_CONFIG,
	loading: false,
	error: null
};

function createConfigStore() {
	const { subscribe, set, update } = writable<ConfigState>(initialState);

	return {
		subscribe,
		setConfig: (config: AnalysisConfig) => {
			update((state) => ({ ...state, analysisConfig: config, error: null }));
		},
		setLoading: (loading: boolean) => {
			update((state) => ({ ...state, loading }));
		},
		setError: (error: string | null) => {
			update((state) => ({ ...state, error }));
		},
		updateConfig: (updates: Partial<AnalysisConfig>) => {
			update((state) => ({
				...state,
				analysisConfig: { ...state.analysisConfig, ...updates }
			}));
		},
		reset: () => set(initialState)
	};
}

export const configStore = createConfigStore();
