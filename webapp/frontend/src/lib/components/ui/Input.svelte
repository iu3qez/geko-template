<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props extends HTMLInputAttributes {
		label?: string;
		error?: string;
		hint?: string;
	}

	let {
		label,
		error,
		hint,
		id,
		value = $bindable(''),
		...rest
	}: Props = $props();

	const inputId = id || `input-${Math.random().toString(36).slice(2, 9)}`;
</script>

<div class="input-group" class:has-error={error}>
	{#if label}
		<label for={inputId}>{label}</label>
	{/if}
	<input
		id={inputId}
		bind:value
		class:error
		{...rest}
	/>
	{#if error}
		<p class="error-message">{error}</p>
	{:else if hint}
		<p class="hint">{hint}</p>
	{/if}
</div>

<style>
	.input-group {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	label {
		font-weight: 500;
		color: var(--geko-dark);
		font-size: var(--text-sm);
	}

	input {
		width: 100%;
		padding: var(--space-3) var(--space-4);
		font-family: var(--font-body);
		font-size: var(--text-base);
		color: var(--geko-dark);
		background-color: var(--geko-white);
		border: 2px solid var(--geko-gray-light);
		border-radius: var(--radius-md);
		transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
	}

	input:focus {
		outline: none;
		border-color: var(--geko-gold);
		box-shadow: 0 0 0 3px rgba(196, 163, 90, 0.2);
	}

	input::placeholder {
		color: var(--geko-gray-light);
	}

	input.error {
		border-color: var(--color-danger);
	}

	input.error:focus {
		box-shadow: 0 0 0 3px rgba(197, 48, 48, 0.2);
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
