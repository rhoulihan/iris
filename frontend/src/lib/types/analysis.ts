/**
 * Analysis-related types and interfaces
 * Based on WEB_CONSOLE_REQUIREMENTS.md data models
 */

export interface AnalysisSession {
	id: string;
	name: string;
	description?: string;
	status: 'pending' | 'running' | 'completed' | 'failed';
	created_at: string;
	started_at?: string;
	completed_at?: string;
	snapshot_id?: string;
	workload_source: 'snapshot' | 'simulation' | 'live';
	total_queries?: number;
	total_tables?: number;
	recommendation_count?: number;
	estimated_savings?: number;
	error_message?: string;
}

export interface SessionDetail extends AnalysisSession {
	recommendations: Array<{
		id: string;
		pattern_type: string;
		confidence: number;
		estimated_savings: number;
	}>;
	workload_stats: {
		query_count: number;
		table_count: number;
		avg_queries_per_table: number;
		date_range: {
			start: string;
			end: string;
		};
	};
}

export interface CreateAnalysisRequest {
	name: string;
	description?: string;
	workload_source: 'snapshot' | 'simulation' | 'connection';
	snapshot_id?: string;
	simulation_id?: string;
	connection_id?: string;
	config?: AnalysisConfig;
}

export interface AnalysisConfig {
	min_confidence?: number;
	detectors?: string[];
	create_snapshot?: boolean;
	pattern_detector?: {
		min_total_queries?: number;
		min_pattern_query_count?: number;
		min_table_query_count?: number;
		low_volume_confidence_penalty?: number;
		snapshot_confidence_min_hours?: number;
	};
}
