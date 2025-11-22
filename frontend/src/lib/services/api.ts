/**
 * API client for IRIS backend
 * Provides typed methods for all backend endpoints
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIError extends Error {
	constructor(
		message: string,
		public status: number,
		public data?: unknown
	) {
		super(message);
		this.name = 'APIError';
	}
}

async function fetchAPI<T>(
	endpoint: string,
	options: RequestInit = {}
): Promise<T> {
	const url = `${API_BASE_URL}${endpoint}`;
	const headers = {
		'Content-Type': 'application/json',
		...options.headers
	};

	const response = await fetch(url, {
		...options,
		headers
	});

	if (!response.ok) {
		const errorData = await response.json().catch(() => ({}));
		throw new APIError(
			errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
			response.status,
			errorData
		);
	}

	return response.json();
}

export const api = {
	// Health check
	async health() {
		return fetchAPI<{ status: string }>('/health');
	},

	// Analysis endpoints
	analysis: {
		async list() {
			return fetchAPI<unknown[]>('/api/v1/analysis');
		},
		async get(id: string) {
			return fetchAPI<unknown>(`/api/v1/analysis/${id}`);
		},
		async create(data: unknown) {
			return fetchAPI<unknown>('/api/v1/analysis', {
				method: 'POST',
				body: JSON.stringify(data)
			});
		},
		async delete(id: string) {
			return fetchAPI<void>(`/api/v1/analysis/${id}`, {
				method: 'DELETE'
			});
		}
	},

	// Recommendations endpoints
	recommendations: {
		async list(filters?: unknown) {
			const params = new URLSearchParams(filters as Record<string, string>);
			return fetchAPI<unknown[]>(`/api/v1/recommendations?${params}`);
		},
		async get(id: string) {
			return fetchAPI<unknown>(`/api/v1/recommendations/${id}`);
		},
		async update(id: string, data: unknown) {
			return fetchAPI<unknown>(`/api/v1/recommendations/${id}`, {
				method: 'PATCH',
				body: JSON.stringify(data)
			});
		},
		async bulkAction(action: unknown) {
			return fetchAPI<unknown>('/api/v1/recommendations/bulk', {
				method: 'POST',
				body: JSON.stringify(action)
			});
		}
	},

	// Simulations endpoints
	simulations: {
		async list() {
			return fetchAPI<unknown[]>('/api/v1/simulations');
		},
		async get(id: string) {
			return fetchAPI<unknown>(`/api/v1/simulations/${id}`);
		},
		async create(data: unknown) {
			return fetchAPI<unknown>('/api/v1/simulations', {
				method: 'POST',
				body: JSON.stringify(data)
			});
		},
		async delete(id: string) {
			return fetchAPI<void>(`/api/v1/simulations/${id}`, {
				method: 'DELETE'
			});
		}
	},

	// Connections endpoints
	connections: {
		async list() {
			return fetchAPI<unknown[]>('/api/v1/connections');
		},
		async get(id: string) {
			return fetchAPI<unknown>(`/api/v1/connections/${id}`);
		},
		async create(data: unknown) {
			return fetchAPI<unknown>('/api/v1/connections', {
				method: 'POST',
				body: JSON.stringify(data)
			});
		},
		async test(id: string) {
			return fetchAPI<unknown>(`/api/v1/connections/${id}/test`, {
				method: 'POST'
			});
		},
		async delete(id: string) {
			return fetchAPI<void>(`/api/v1/connections/${id}`, {
				method: 'DELETE'
			});
		}
	},

	// Configuration endpoints
	config: {
		async get() {
			return fetchAPI<unknown>('/api/v1/config');
		},
		async update(data: unknown) {
			return fetchAPI<unknown>('/api/v1/config', {
				method: 'PATCH',
				body: JSON.stringify(data)
			});
		}
	}
};

export { APIError };
