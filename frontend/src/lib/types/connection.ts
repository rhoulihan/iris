/**
 * Database connection types and interfaces
 */

export interface DatabaseConnection {
	id: string;
	name: string;
	host: string;
	port: number;
	service_name: string;
	username: string;
	status: 'active' | 'inactive' | 'error';
	last_tested?: string;
	created_at: string;
}

export interface CreateConnectionRequest {
	name: string;
	host: string;
	port: number;
	service_name: string;
	username: string;
	password: string;
}

export interface TestConnectionRequest {
	connection_id: string;
}

export interface TestConnectionResponse {
	success: boolean;
	message: string;
	oracle_version?: string;
}
