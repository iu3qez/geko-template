<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'gold' | 'magenta' | 'success' | 'warning' | 'danger' | 'info';
		children: Snippet;
	}

	let { variant = 'gold', children }: Props = $props();
</script>

<span class="badge badge-{variant}">
	{@render children()}
</span>

<style>
	.badge {
		display: inline-flex;
		align-items: center;
		padding: var(--space-1) var(--space-3);
		font-family: var(--font-display);
		font-size: var(--text-xs);
		font-weight: 500;
		border-radius: var(--radius-full);
	}

	.badge-gold {
		background-color: var(--geko-gold);
		color: var(--geko-white);
	}

	.badge-magenta {
		background-color: var(--geko-magenta);
		color: var(--geko-white);
	}

	.badge-success {
		background-color: var(--color-success-light);
		color: var(--color-success);
	}

	.badge-warning {
		background-color: var(--color-warning-light);
		color: var(--color-warning);
	}

	.badge-danger {
		background-color: var(--color-danger-light);
		color: var(--color-danger);
	}

	.badge-info {
		background-color: var(--color-info-light);
		color: var(--color-info);
	}
</style>
