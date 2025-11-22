/**
 * Analysis sessions store
 * Manages state for analysis sessions
 */

import { writable, derived } from 'svelte/store';
import type { AnalysisSession } from '$lib/types';

interface SessionsState {
	sessions: AnalysisSession[];
	loading: boolean;
	error: string | null;
}

const initialState: SessionsState = {
	sessions: [],
	loading: false,
	error: null
};

function createSessionsStore() {
	const { subscribe, set, update } = writable<SessionsState>(initialState);

	return {
		subscribe,
		setSessions: (sessions: AnalysisSession[]) => {
			update((state) => ({ ...state, sessions, error: null }));
		},
		setLoading: (loading: boolean) => {
			update((state) => ({ ...state, loading }));
		},
		setError: (error: string | null) => {
			update((state) => ({ ...state, error }));
		},
		addSession: (session: AnalysisSession) => {
			update((state) => ({
				...state,
				sessions: [session, ...state.sessions]
			}));
		},
		updateSession: (id: string, updates: Partial<AnalysisSession>) => {
			update((state) => ({
				...state,
				sessions: state.sessions.map((s) => (s.id === id ? { ...s, ...updates } : s))
			}));
		},
		removeSession: (id: string) => {
			update((state) => ({
				...state,
				sessions: state.sessions.filter((s) => s.id !== id)
			}));
		},
		reset: () => set(initialState)
	};
}

export const sessionsStore = createSessionsStore();

// Derived stores
export const activeSessions = derived(sessionsStore, ($store) =>
	$store.sessions.filter((s) => s.status === 'running' || s.status === 'pending')
);

export const completedSessions = derived(sessionsStore, ($store) =>
	$store.sessions.filter((s) => s.status === 'completed')
);
