<script lang="ts">
	interface Props {
		size?: 'sm' | 'md' | 'lg';
		text?: string;
	}

	let { size = 'md', text }: Props = $props();
</script>

<div class="loading loading-{size}">
	<div class="spinner"></div>
	{#if text}
		<p>{text}</p>
	{/if}
</div>

<style>
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-4);
		padding: var(--space-8);
	}

	.spinner {
		border: 3px solid var(--geko-gray-light);
		border-top-color: var(--geko-gold);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.loading-sm .spinner {
		width: 24px;
		height: 24px;
	}

	.loading-md .spinner {
		width: 40px;
		height: 40px;
	}

	.loading-lg .spinner {
		width: 56px;
		height: 56px;
	}

	p {
		font-size: var(--text-sm);
		color: var(--geko-gray);
		margin: 0;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
