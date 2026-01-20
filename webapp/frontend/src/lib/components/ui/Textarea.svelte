<script lang="ts">
	import type { HTMLTextareaAttributes } from 'svelte/elements';

	interface Props extends HTMLTextareaAttributes {
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

	const textareaId = id || `textarea-${Math.random().toString(36).slice(2, 9)}`;
</script>

<div class="textarea-group" class:has-error={error}>
	{#if label}
		<label for={textareaId}>{label}</label>
	{/if}
	<textarea
		id={textareaId}
		bind:value
		class:error
		{...rest}
	></textarea>
	{#if error}
		<p class="error-message">{error}</p>
	{:else if hint}
		<p class="hint">{hint}</p>
	{/if}
</div>

<style>
	.textarea-group {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	label {
		font-weight: 500;
		color: var(--geko-dark);
		font-size: var(--text-sm);
	}

	textarea {
		width: 100%;
		min-height: 120px;
		padding: var(--space-3) var(--space-4);
		font-family: var(--font-body);
		font-size: var(--text-base);
		color: var(--geko-dark);
		background-color: var(--geko-white);
		border: 2px solid var(--geko-gray-light);
		border-radius: var(--radius-md);
		resize: vertical;
		transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
	}

	textarea:focus {
		outline: none;
		border-color: var(--geko-gold);
		box-shadow: 0 0 0 3px rgba(196, 163, 90, 0.2);
	}

	textarea::placeholder {
		color: var(--geko-gray-light);
	}

	textarea.error {
		border-color: var(--color-danger);
	}

	textarea.error:focus {
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
