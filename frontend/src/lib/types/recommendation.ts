/**
 * Recommendation-related types and interfaces
 * Based on WEB_CONSOLE_REQUIREMENTS.md data models
 */

export interface Recommendation {
	id: string;
	session_id: string;
	pattern_type: 'LOB_CLIFF' | 'JOIN_DIMENSION' | 'DOCUMENT_RELATIONAL' | 'DUALITY_VIEW';
	table_name: string;
	confidence: number;
	estimated_savings: number;
	status: 'pending' | 'approved' | 'rejected' | 'implemented';
	created_at: string;
	reviewed_at?: string;
	reviewed_by?: string;
	implementation_notes?: string;
}

export interface RecommendationDetail extends Recommendation {
	pattern_metrics: {
		lob_size_mb?: number;
		query_count?: number;
		access_pattern?: string;
		json_column_count?: number;
		join_count?: number;
		[key: string]: string | number | undefined;
	};
	implementation: {
		sql_preview: string;
		estimated_downtime: string;
		required_privileges: string[];
		rollback_plan: string;
	};
	impact_analysis: {
		performance_improvement: string;
		storage_reduction: string;
		maintenance_impact: string;
	};
}

export interface RecommendationFilter {
	session_id?: string;
	pattern_type?: string;
	status?: string;
	min_confidence?: number;
	min_savings?: number;
}

export interface BulkRecommendationAction {
	recommendation_ids: string[];
	action: 'approve' | 'reject' | 'export';
	notes?: string;
}
