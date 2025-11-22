/**
 * Application constants and configuration
 */

export const PATTERN_TYPES = {
	LOB_CLIFF: 'LOB Cliff',
	JOIN_DIMENSION: 'Join Dimension',
	DOCUMENT_RELATIONAL: 'Document Relational',
	DUALITY_VIEW: 'Duality View'
} as const;

export const PATTERN_DESCRIPTIONS = {
	LOB_CLIFF: 'Large objects stored in external tablespaces for improved performance',
	JOIN_DIMENSION: 'Denormalized dimension tables to reduce join overhead in analytical queries',
	DOCUMENT_RELATIONAL: 'JSON/XML documents that could benefit from relational decomposition',
	DUALITY_VIEW: 'Relational tables that could be accessed via JSON Relational Duality Views'
} as const;

export const STATUS_COLORS = {
	pending: 'badge-warning',
	running: 'badge-info',
	completed: 'badge-success',
	failed: 'badge-error',
	approved: 'badge-success',
	rejected: 'badge-error',
	implemented: 'badge-primary',
	active: 'badge-success',
	inactive: 'badge-ghost',
	error: 'badge-error'
} as const;

export const CONFIDENCE_THRESHOLDS = {
	HIGH: 0.8,
	MEDIUM: 0.6,
	LOW: 0.4
} as const;

export const DEFAULT_ANALYSIS_CONFIG = {
	min_confidence: 0.6,
	detectors: ['LOB_CLIFF', 'JOIN_DIMENSION', 'DOCUMENT_RELATIONAL', 'DUALITY_VIEW'] as string[],
	create_snapshot: true,
	pattern_detector: {
		min_total_queries: 5000,
		min_pattern_query_count: 50,
		min_table_query_count: 20,
		low_volume_confidence_penalty: 0.3,
		snapshot_confidence_min_hours: 24.0
	}
};

export const ROUTES = {
	HOME: '/',
	ANALYZE: '/analyze',
	SESSIONS: '/sessions',
	SESSION_DETAIL: '/sessions/:id',
	RECOMMENDATIONS: '/recommendations',
	RECOMMENDATION_DETAIL: '/recommendations/:id',
	SIMULATIONS: '/simulations',
	SIMULATION_DETAIL: '/simulations/:id',
	CONNECTIONS: '/connections',
	CONFIG: '/config',
	LOGIN: '/login'
} as const;
