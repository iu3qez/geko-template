<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		href?: string;
		children: Snippet;
		header?: Snippet;
		footer?: Snippet;
	}

	let { href, children, header, footer }: Props = $props();
</script>

{#if href}
	<a {href} class="card card-link">
		{#if header}
			<div class="card-header">
				{@render header()}
			</div>
		{/if}
		<div class="card-body">
			{@render children()}
		</div>
		{#if footer}
			<div class="card-footer">
				{@render footer()}
			</div>
		{/if}
	</a>
{:else}
	<div class="card">
		{#if header}
			<div class="card-header">
				{@render header()}
			</div>
		{/if}
		<div class="card-body">
			{@render children()}
		</div>
		{#if footer}
			<div class="card-footer">
				{@render footer()}
			</div>
		{/if}
	</div>
{/if}

<style>
	.card {
		background-color: var(--geko-white);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md);
		overflow: hidden;
	}

	.card-link {
		display: block;
		text-decoration: none;
		color: inherit;
		transition: all var(--transition-fast);
	}

	.card-link:hover {
		text-decoration: none;
		box-shadow: var(--shadow-lg);
		transform: translateY(-2px);
	}

	.card-header {
		padding: var(--space-4) var(--space-6);
		border-bottom: 1px solid var(--geko-gray-light);
	}

	.card-body {
		padding: var(--space-6);
	}

	.card-footer {
		padding: var(--space-4) var(--space-6);
		border-top: 1px solid var(--geko-gray-light);
		background-color: var(--geko-light);
	}
</style>
