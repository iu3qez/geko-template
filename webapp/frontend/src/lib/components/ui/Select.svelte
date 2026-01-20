<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLSelectAttributes } from 'svelte/elements';

	interface Props extends HTMLSelectAttributes {
		label?: string;
		error?: string;
		hint?: string;
		children: Snippet;
	}

	let {
		label,
		error,
		hint,
		id,
		value = $bindable(''),
		children,
		...rest
	}: Props = $props();

	const selectId = id || `select-${Math.random().toString(36).slice(2, 9)}`;
</script>

<div class="select-group" class:has-error={error}>
	{#if label}
		<label for={selectId}>{label}</label>
	{/if}
	<select
		id={selectId}
		bind:value
		class:error
		{...rest}
	>
		{@render children()}
	</select>
	{#if error}
		<p class="error-message">{error}</p>
	{:else if hint}
		<p class="hint">{hint}</p>
	{/if}
</div>

<style>
	.select-group {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	label {
		font-weight: 500;
		color: var(--geko-dark);
		font-size: var(--text-sm);
	}

	select {
		width: 100%;
		padding: var(--space-3) var(--space-4);
		font-family: var(--font-body);
		font-size: var(--text-base);
		color: var(--geko-dark);
		background-color: var(--geko-white);
		border: 2px solid var(--geko-gray-light);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
	}

	select:focus {
		outline: none;
		border-color: var(--geko-gold);
		box-shadow: 0 0 0 3px rgba(196, 163, 90, 0.2);
	}

	select.error {
		border-color: var(--color-danger);
	}

	.error-message {
		color: var(--color-danger);
		font-size: var(--text-sm);
		margin: 0;
	}

	.hint {
		color: var(--geko-gray);
		font-size: var(--text-sm);
		margin: 0;
	}

	.has-error label {
		color: var(--color-danger);
	}
</style>
