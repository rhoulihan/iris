/**
 * Validation utility functions
 */

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	return emailRegex.test(email);
}

/**
 * Validate hostname format
 * Using a simpler regex to avoid ReDoS attacks
 */
export function isValidHostname(hostname: string): boolean {
	// Simplified hostname validation to prevent ReDoS
	// Allows alphanumeric, dots, and hyphens in valid positions
	if (hostname.length > 253) return false;

	// Regex is safe: bounded quantifiers {0,61} prevent ReDoS
	const hostnameRegex =
		// eslint-disable-next-line security/detect-unsafe-regex
		/^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

	return hostnameRegex.test(hostname);
}

/**
 * Validate port number
 */
export function isValidPort(port: number): boolean {
	return Number.isInteger(port) && port >= 1 && port <= 65535;
}

/**
 * Validate Oracle service name format
 */
export function isValidServiceName(serviceName: string): boolean {
	// Basic validation: alphanumeric, underscores, dots
	const serviceNameRegex = /^[a-zA-Z0-9_.]+$/;
	return serviceNameRegex.test(serviceName) && serviceName.length > 0;
}

/**
 * Validate confidence threshold (0-1)
 */
export function isValidConfidence(confidence: number): boolean {
	return typeof confidence === 'number' && confidence >= 0 && confidence <= 1;
}

/**
 * Validate required string field
 */
export function isRequired(value: string | undefined | null): boolean {
	return value !== undefined && value !== null && value.trim().length > 0;
}

/**
 * Validate minimum value
 */
export function isMinValue(value: number, min: number): boolean {
	return typeof value === 'number' && value >= min;
}

/**
 * Validate maximum value
 */
export function isMaxValue(value: number, max: number): boolean {
	return typeof value === 'number' && value <= max;
}
