/**
 * Simulation-related types and interfaces
 * Based on WEB_CONSOLE_REQUIREMENTS.md data models
 */

export interface Simulation {
	id: string;
	name: string;
	scenario_type: 'lob_cliff' | 'join_dimension' | 'document_relational' | 'duality_view';
	status: 'pending' | 'running' | 'completed' | 'failed';
	created_at: string;
	started_at?: string;
	completed_at?: string;
	result_summary?: {
		recommendations_found: number;
		workload_queries: number;
		execution_time_seconds: number;
	};
}

export interface SimulationDetail extends Simulation {
	config: {
		table_count?: number;
		row_count?: number;
		query_count?: number;
		lob_size_mb?: number;
		json_column_count?: number;
		join_cardinality?: number;
		[key: string]: string | number | boolean | undefined;
	};
	results: {
		recommendations: Array<{
			pattern_type: string;
			confidence: number;
			table_name: string;
		}>;
		workload_stats: {
			total_queries: number;
			total_tables: number;
			date_range: {
				start: string;
				end: string;
			};
		};
	};
}

export interface CreateSimulationRequest {
	name: string;
	scenario_type: 'lob_cliff' | 'join_dimension' | 'document_relational' | 'duality_view';
	config: Record<string, unknown>;
}
