<script lang="ts">
	import type { Snippet } from 'svelte';
	import { X } from 'lucide-svelte';

	interface Props {
		open: boolean;
		title?: string;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		onclose?: () => void;
		children: Snippet;
		footer?: Snippet;
	}

	let {
		open = $bindable(false),
		title,
		size = 'md',
		onclose,
		children,
		footer
	}: Props = $props();

	function handleClose() {
		open = false;
		onclose?.();
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			handleClose();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			handleClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="modal-backdrop" onclick={handleBackdropClick}>
		<div class="modal modal-{size}" role="dialog" aria-modal="true" aria-labelledby="modal-title">
			<header class="modal-header">
				{#if title}
					<h2 id="modal-title">{title}</h2>
				{/if}
				<button class="close-btn" onclick={handleClose} aria-label="Chiudi">
					<X size={20} />
				</button>
			</header>

			<div class="modal-body">
				{@render children()}
			</div>

			{#if footer}
				<footer class="modal-footer">
					{@render footer()}
				</footer>
			{/if}
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-4);
		background-color: rgba(0, 0, 0, 0.5);
		animation: fadeIn var(--transition-fast);
	}

	.modal {
		background-color: var(--geko-white);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-xl);
		max-height: calc(100vh - var(--space-8));
		display: flex;
		flex-direction: column;
		animation: slideUp var(--transition-base);
	}

	.modal-sm { width: 100%; max-width: 400px; }
	.modal-md { width: 100%; max-width: 560px; }
	.modal-lg { width: 100%; max-width: 720px; }
	.modal-xl { width: 100%; max-width: 960px; }

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-4) var(--space-6);
		border-bottom: 1px solid var(--geko-gray-light);
	}

	.modal-header h2 {
		font-size: var(--text-xl);
		margin: 0;
	}

	.close-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-2);
		background: none;
		border: none;
		color: var(--geko-gray);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.close-btn:hover {
		background-color: var(--geko-light);
		color: var(--geko-dark);
	}

	.modal-body {
		padding: var(--space-6);
		overflow-y: auto;
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
		padding: var(--space-4) var(--space-6);
		border-top: 1px solid var(--geko-gray-light);
		background-color: var(--geko-light);
		border-radius: 0 0 var(--radius-lg) var(--radius-lg);
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	@keyframes slideUp {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
