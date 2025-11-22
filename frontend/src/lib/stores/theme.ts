/**
 * Theme store for managing light/dark/auto theme switching
 */
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Theme = 'light' | 'dark' | 'auto';

const THEME_STORAGE_KEY = 'iris-theme';

// Initialize theme from localStorage or default to 'auto'
function getInitialTheme(): Theme {
	if (!browser) return 'auto';

	const stored = localStorage.getItem(THEME_STORAGE_KEY);
	if (stored === 'light' || stored === 'dark' || stored === 'auto') {
		return stored;
	}
	return 'auto';
}

// Create the theme store
export const theme = writable<Theme>(getInitialTheme());

// Subscribe to theme changes and update localStorage + DOM
theme.subscribe((value) => {
	if (!browser) return;

	// Save to localStorage
	localStorage.setItem(THEME_STORAGE_KEY, value);

	// Determine the actual theme to apply
	let actualTheme: 'light' | 'dark';
	if (value === 'auto') {
		// Use system preference
		actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
	} else {
		actualTheme = value;
	}

	// Apply theme to document
	document.documentElement.setAttribute('data-theme', actualTheme);
});

// Listen for system theme changes when in auto mode
if (browser) {
	const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
	mediaQuery.addEventListener('change', (e) => {
		theme.update((currentTheme) => {
			if (currentTheme === 'auto') {
				// Trigger a refresh by re-setting the theme
				const actualTheme = e.matches ? 'dark' : 'light';
				document.documentElement.setAttribute('data-theme', actualTheme);
			}
			return currentTheme;
		});
	});
}

// Export helper functions
export function setTheme(newTheme: Theme) {
	theme.set(newTheme);
}

export function toggleTheme() {
	theme.update((current) => {
		if (current === 'light') return 'dark';
		if (current === 'dark') return 'auto';
		return 'light';
	});
}
