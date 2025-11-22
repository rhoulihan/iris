import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],

	server: {
		port: 5173,
		host: true,
		proxy: {
			// Proxy API requests to backend during development
			'/api': {
				target: process.env.VITE_API_URL || 'http://localhost:8000',
				changeOrigin: true
			},
			'/health': {
				target: process.env.VITE_API_URL || 'http://localhost:8000',
				changeOrigin: true
			}
		}
	},

	build: {
		target: 'esnext',
		minify: 'esbuild',
		sourcemap: true,
		rollupOptions: {
			output: {
				manualChunks: {
					// Vendor chunking for better caching
					'svelte-vendor': ['svelte']
					// Add 'chart-vendor': ['chart.js'] when Chart.js is installed
				}
			}
		}
	},

	preview: {
		port: 4173,
		host: true
	}
});
