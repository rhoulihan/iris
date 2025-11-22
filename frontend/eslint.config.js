import js from '@eslint/js';
import ts from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import svelte from 'eslint-plugin-svelte';
import svelteParser from 'svelte-eslint-parser';
import security from 'eslint-plugin-security';
import globals from 'globals';

export default [
	js.configs.recommended,
	security.configs.recommended,
	{
		files: ['**/*.js', '**/*.ts'],
		languageOptions: {
			parser: tsParser,
			parserOptions: {
				sourceType: 'module',
				ecmaVersion: 2020
			},
			globals: {
				...globals.browser,
				...globals.es2017,
				...globals.node,
				RequestInit: 'readonly',
				Response: 'readonly',
				Request: 'readonly',
				fetch: 'readonly'
			}
		},
		plugins: {
			'@typescript-eslint': ts,
			security
		},
		rules: {
			...ts.configs.recommended.rules,
			'@typescript-eslint/no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_',
					varsIgnorePattern: '^_'
				}
			],
			// Security rules (can be customized)
			'security/detect-object-injection': 'warn',
			'security/detect-non-literal-regexp': 'warn',
			'security/detect-unsafe-regex': 'error'
		}
	},
	...svelte.configs['flat/recommended'],
	{
		files: ['**/*.svelte'],
		languageOptions: {
			parser: svelteParser,
			parserOptions: {
				parser: tsParser
			}
		}
	},
	{
		// Allow require() in config files
		files: ['*.config.js', '*.config.ts'],
		rules: {
			'@typescript-eslint/no-require-imports': 'off'
		}
	},
	{
		ignores: ['dist', 'build', '.svelte-kit', 'node_modules']
	}
];
