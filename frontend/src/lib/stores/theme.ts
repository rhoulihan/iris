/**
 * Theme store
 * Manages dark/light theme state
 */

import { writable } from 'svelte/store';
import { browser } from '$app/environment';

type Theme = 'light' | 'dark';

function createThemeStore() {
	// Initialize from localStorage if in browser, otherwise default to light
	const initialTheme: Theme = browser
		? ((localStorage.getItem('theme') as Theme) || 'light')
		: 'light';

	const { subscribe, set } = writable<Theme>(initialTheme);

	return {
		subscribe,
		setTheme: (theme: Theme) => {
			if (browser) {
				localStorage.setItem('theme', theme);
				document.documentElement.setAttribute('data-theme', theme);
			}
			set(theme);
		},
		toggle: () => {
			let currentTheme: Theme = 'light';
			const unsubscribe = subscribe((value) => {
				currentTheme = value;
			});
			unsubscribe();

			const newTheme: Theme = currentTheme === 'light' ? 'dark' : 'light';

			if (browser) {
				localStorage.setItem('theme', newTheme);
				document.documentElement.setAttribute('data-theme', newTheme);
			}
			set(newTheme);
		}
	};
}

export const themeStore = createThemeStore();

// Initialize theme on page load
if (browser) {
	const theme = (localStorage.getItem('theme') as Theme) || 'light';
	document.documentElement.setAttribute('data-theme', theme);
}
