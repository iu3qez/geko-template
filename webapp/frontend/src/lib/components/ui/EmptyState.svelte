<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { Component } from 'svelte';
	import { Inbox } from 'lucide-svelte';

	interface Props {
		title: string;
		description?: string;
		icon?: Component;
		action?: Snippet;
	}

	let { title, description, icon = Inbox, action }: Props = $props();
</script>

<div class="empty-state">
	<div class="icon-wrapper">
		<svelte:component this={icon} size={48} />
	</div>
	<h3>{title}</h3>
	{#if description}
		<p>{description}</p>
	{/if}
	{#if action}
		<div class="action">
			{@render action()}
		</div>
	{/if}
</div>

<style>
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		padding: var(--space-12) var(--space-6);
		color: var(--geko-gray);
	}

	.icon-wrapper {
		margin-bottom: var(--space-4);
		opacity: 0.5;
	}

	h3 {
		font-size: var(--text-xl);
		color: var(--geko-dark);
		margin-bottom: var(--space-2);
	}

	p {
		font-size: var(--text-sm);
		max-width: 320px;
		margin-bottom: var(--space-4);
	}

	.action {
		margin-top: var(--space-4);
	}
</style>
