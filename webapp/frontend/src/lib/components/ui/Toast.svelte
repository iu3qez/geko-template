<script lang="ts">
	import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-svelte';

	interface Props {
		type?: 'success' | 'error' | 'warning' | 'info';
		message: string;
		visible?: boolean;
		duration?: number;
		onclose?: () => void;
	}

	let {
		type = 'info',
		message,
		visible = $bindable(true),
		duration = 5000,
		onclose
	}: Props = $props();

	const icons = {
		success: CheckCircle,
		error: XCircle,
		warning: AlertTriangle,
		info: Info
	};

	$effect(() => {
		if (visible && duration > 0) {
			const timer = setTimeout(() => {
				visible = false;
				onclose?.();
			}, duration);
			return () => clearTimeout(timer);
		}
	});

	function handleClose() {
		visible = false;
		onclose?.();
	}
</script>

{#if visible}
	<div class="toast toast-{type}" role="alert">
		<svelte:component this={icons[type]} size={20} />
		<span class="message">{message}</span>
		<button class="close-btn" onclick={handleClose} aria-label="Chiudi">
			<X size={16} />
		</button>
	</div>
{/if}

<style>
	.toast {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-4) var(--space-5);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-lg);
		animation: slideIn var(--transition-base);
	}

	.toast-success {
		background-color: var(--color-success-light);
		color: var(--color-success);
	}

	.toast-error {
		background-color: var(--color-danger-light);
		color: var(--color-danger);
	}

	.toast-warning {
		background-color: var(--color-warning-light);
		color: var(--color-warning);
	}

	.toast-info {
		background-color: var(--color-info-light);
		color: var(--color-info);
	}

	.message {
		flex: 1;
		font-size: var(--text-sm);
	}

	.close-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-1);
		background: none;
		border: none;
		color: inherit;
		opacity: 0.7;
		cursor: pointer;
		border-radius: var(--radius-sm);
		transition: opacity var(--transition-fast);
	}

	.close-btn:hover {
		opacity: 1;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
