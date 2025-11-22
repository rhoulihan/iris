/**
 * Utility functions for formatting data
 */

/**
 * Format a number as currency
 */
export function formatCurrency(value: number, currency = 'USD'): string {
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency
	}).format(value);
}

/**
 * Format a number with commas
 */
export function formatNumber(value: number): string {
	return new Intl.NumberFormat('en-US').format(value);
}

/**
 * Format a confidence score as a percentage
 */
export function formatConfidence(confidence: number): string {
	return `${Math.round(confidence * 100)}%`;
}

/**
 * Format a date string
 */
export function formatDate(dateString: string): string {
	const date = new Date(dateString);
	return new Intl.DateTimeFormat('en-US', {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	}).format(date);
}

/**
 * Format a date as relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string): string {
	const date = new Date(dateString);
	const now = new Date();
	const diffMs = now.getTime() - date.getTime();
	const diffSecs = Math.floor(diffMs / 1000);
	const diffMins = Math.floor(diffSecs / 60);
	const diffHours = Math.floor(diffMins / 60);
	const diffDays = Math.floor(diffHours / 24);

	if (diffSecs < 60) {
		return 'just now';
	} else if (diffMins < 60) {
		return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
	} else if (diffHours < 24) {
		return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
	} else if (diffDays < 7) {
		return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
	} else {
		return formatDate(dateString);
	}
}

/**
 * Format bytes to human-readable size
 */
export function formatBytes(bytes: number): string {
	if (bytes === 0) return '0 Bytes';

	const k = 1024;
	const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));

	// Bounds check to prevent array access issues
	const safeIndex = Math.min(i, sizes.length - 1);
	// eslint-disable-next-line security/detect-object-injection
	return `${parseFloat((bytes / Math.pow(k, safeIndex)).toFixed(2))} ${sizes[safeIndex]}`;
}

/**
 * Get confidence level label
 */
export function getConfidenceLevel(confidence: number): string {
	if (confidence >= 0.8) return 'High';
	if (confidence >= 0.6) return 'Medium';
	return 'Low';
}

/**
 * Truncate string to specified length
 */
export function truncate(str: string, maxLength: number): string {
	if (str.length <= maxLength) return str;
	return `${str.slice(0, maxLength - 3)}...`;
}
