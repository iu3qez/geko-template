<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	interface Props extends HTMLButtonAttributes {
		variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
		size?: 'sm' | 'md' | 'lg';
		loading?: boolean;
		children: Snippet;
	}

	let {
		variant = 'primary',
		size = 'md',
		loading = false,
		disabled = false,
		children,
		...rest
	}: Props = $props();
</script>

<button
	class="btn btn-{variant} btn-{size}"
	disabled={disabled || loading}
	{...rest}
>
	{#if loading}
		<span class="spinner"></span>
	{/if}
	{@render children()}
</button>

<style>
	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		font-family: var(--font-display);
		font-weight: 500;
		text-decoration: none;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Sizes */
	.btn-sm {
		padding: var(--space-2) var(--space-4);
		font-size: var(--text-xs);
	}

	.btn-md {
		padding: var(--space-3) var(--space-6);
		font-size: var(--text-sm);
	}

	.btn-lg {
		padding: var(--space-4) var(--space-8);
		font-size: var(--text-lg);
	}

	/* Variants */
	.btn-primary {
		background-color: var(--geko-gold);
		color: var(--geko-white);
	}

	.btn-primary:hover:not(:disabled) {
		background-color: var(--geko-gold-dark);
	}

	.btn-secondary {
		background-color: var(--geko-magenta);
		color: var(--geko-white);
	}

	.btn-secondary:hover:not(:disabled) {
		background-color: var(--geko-magenta-dark);
	}

	.btn-outline {
		background-color: transparent;
		color: var(--geko-gold);
		border: 2px solid var(--geko-gold);
	}

	.btn-outline:hover:not(:disabled) {
		background-color: var(--geko-gold);
		color: var(--geko-white);
	}

	.btn-ghost {
		background-color: transparent;
		color: var(--geko-dark);
	}

	.btn-ghost:hover:not(:disabled) {
		background-color: rgba(0, 0, 0, 0.05);
	}

	.btn-danger {
		background-color: var(--color-danger);
		color: var(--geko-white);
	}

	.btn-danger:hover:not(:disabled) {
		background-color: #a52020;
	}

	/* Spinner */
	.spinner {
		width: 1em;
		height: 1em;
		border: 2px solid currentColor;
		border-top-color: transparent;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
