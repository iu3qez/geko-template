<script lang="ts">
	import { onMount } from 'svelte';
	import { Save, RefreshCw } from 'lucide-svelte';
	import { Button, Input, Card, Loading, Toast } from '$lib/components/ui';
	import { config } from '$lib/api';
	import type { ConfigItem } from '$lib/api';

	let configItems = $state<Record<string, ConfigItem>>({});
	let editValues = $state<Record<string, string>>({});
	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let successMessage = $state<string | null>(null);

	const configOrder = [
		'ultimo_numero',
		'titolo_rivista',
		'sottotitolo_rivista',
		'sito_web',
		'email_redazione',
		'claude_model'
	];

	onMount(async () => {
		await loadConfig();
	});

	async function loadConfig() {
		loading = true;
		error = null;
		try {
			configItems = await config.getAll();
			// Initialize edit values
			editValues = {};
			for (const [key, item] of Object.entries(configItems)) {
				editValues[key] = item.value;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore nel caricamento';
		} finally {
			loading = false;
		}
	}

	async function handleSave() {
		saving = true;
		error = null;
		successMessage = null;

		try {
			await config.update(editValues);
			await loadConfig();
			successMessage = 'Configurazione salvata con successo';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante il salvataggio';
		} finally {
			saving = false;
		}
	}

	function resetValues() {
		for (const [key, item] of Object.entries(configItems)) {
			editValues[key] = item.value;
		}
	}

	const hasChanges = $derived(() => {
		for (const [key, item] of Object.entries(configItems)) {
			if (editValues[key] !== item.value) return true;
		}
		return false;
	});

	const sortedConfigKeys = $derived(
		Object.keys(configItems).sort((a, b) => {
			const aIdx = configOrder.indexOf(a);
			const bIdx = configOrder.indexOf(b);
			if (aIdx === -1 && bIdx === -1) return a.localeCompare(b);
			if (aIdx === -1) return 1;
			if (bIdx === -1) return -1;
			return aIdx - bIdx;
		})
	);
</script>

<svelte:head>
	<title>Configurazione - GEKO Radio Magazine</title>
</svelte:head>

<div class="config-page">
	<header class="page-header">
		<div>
			<h1>Configurazione</h1>
			<p>Impostazioni globali dell'applicazione</p>
		</div>
		<div class="header-actions">
			<Button variant="ghost" onclick={resetValues} disabled={!hasChanges()}>
				<RefreshCw size={18} />
				Annulla modifiche
			</Button>
			<Button onclick={handleSave} loading={saving} disabled={!hasChanges()}>
				<Save size={18} />
				Salva
			</Button>
		</div>
	</header>

	{#if successMessage}
		<Toast type="success" message={successMessage} onclose={() => successMessage = null} />
	{/if}

	{#if error}
		<div class="error-message">
			<p>{error}</p>
			<Button onclick={() => error = null} variant="ghost" size="sm">Chiudi</Button>
		</div>
	{/if}

	{#if loading}
		<Loading text="Caricamento configurazione..." />
	{:else}
		<Card>
			<form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
				<div class="config-grid">
					{#each sortedConfigKeys as key}
						{@const item = configItems[key]}
						<div class="config-item">
							<Input
								label={formatLabel(key)}
								hint={item.description}
								bind:value={editValues[key]}
							/>
							{#if item.updated_at}
								<span class="last-updated">
									Ultimo aggiornamento: {new Date(item.updated_at).toLocaleDateString('it-IT')}
								</span>
							{/if}
						</div>
					{/each}
				</div>
			</form>
		</Card>

		<Card>
			{#snippet header()}
				<h2>Informazioni</h2>
			{/snippet}

			<dl class="info-list">
				<div>
					<dt>Versione App</dt>
					<dd>1.0.0</dd>
				</div>
				<div>
					<dt>Database</dt>
					<dd>SQLite</dd>
				</div>
				<div>
					<dt>Template</dt>
					<dd>Typst</dd>
				</div>
			</dl>
		</Card>
	{/if}
</div>

<script context="module" lang="ts">
	function formatLabel(key: string): string {
		return key
			.split('_')
			.map(word => word.charAt(0).toUpperCase() + word.slice(1))
			.join(' ');
	}
</script>

<style>
	.config-page {
		max-width: 800px;
		margin: 0 auto;
		animation: fadeIn var(--transition-base);
	}

	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: var(--space-6);
		flex-wrap: wrap;
		gap: var(--space-4);
	}

	.page-header h1 {
		margin-bottom: var(--space-2);
	}

	.page-header p {
		color: var(--geko-gray);
		margin: 0;
	}

	.header-actions {
		display: flex;
		gap: var(--space-3);
	}

	.config-grid {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.config-item {
		position: relative;
	}

	.last-updated {
		display: block;
		font-size: var(--text-xs);
		color: var(--geko-gray-light);
		margin-top: var(--space-1);
	}

	.info-list {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-6);
	}

	.info-list dt {
		font-size: var(--text-sm);
		color: var(--geko-gray);
		margin-bottom: var(--space-1);
	}

	.info-list dd {
		margin: 0;
		font-family: var(--font-display);
		font-weight: 500;
	}

	.info-list h2 {
		font-size: var(--text-lg);
		margin: 0;
	}

	.error-message {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: var(--color-danger-light);
		color: var(--color-danger);
		padding: var(--space-3) var(--space-4);
		border-radius: var(--radius-md);
		margin-bottom: var(--space-4);
	}

	.error-message p {
		margin: 0;
	}

	:global(.config-page .card) {
		margin-bottom: var(--space-6);
	}

	@media (max-width: 640px) {
		.header-actions {
			width: 100%;
			justify-content: flex-end;
		}

		.info-list {
			grid-template-columns: 1fr;
		}
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
