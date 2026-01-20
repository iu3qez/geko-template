<script lang="ts">
	import { onMount } from 'svelte';
	import { Plus, Calendar, FileText, Download, Trash2 } from 'lucide-svelte';
	import { Button, Card, Badge, Loading, EmptyState, Modal } from '$lib/components/ui';
	import { magazines } from '$lib/api';
	import type { Magazine } from '$lib/api';

	let magazinesList = $state<Magazine[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let deleteModal = $state(false);
	let magazineToDelete = $state<Magazine | null>(null);
	let deleting = $state(false);

	onMount(async () => {
		await loadMagazines();
	});

	async function loadMagazines() {
		loading = true;
		error = null;
		try {
			magazinesList = await magazines.list();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore nel caricamento';
		} finally {
			loading = false;
		}
	}

	function confirmDelete(magazine: Magazine) {
		magazineToDelete = magazine;
		deleteModal = true;
	}

	async function handleDelete() {
		if (!magazineToDelete) return;

		deleting = true;
		try {
			await magazines.delete(magazineToDelete.id);
			magazinesList = magazinesList.filter(m => m.id !== magazineToDelete!.id);
			deleteModal = false;
			magazineToDelete = null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante la cancellazione';
		} finally {
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>Numeri - GEKO Radio Magazine</title>
</svelte:head>

<div class="magazines-page">
	<header class="page-header">
		<div>
			<h1>Numeri GEKO</h1>
			<p>Archivio di tutti i numeri della rivista</p>
		</div>
		<Button href="/magazines/new">
			<Plus size={18} />
			Nuovo Numero
		</Button>
	</header>

	{#if loading}
		<Loading text="Caricamento numeri..." />
	{:else if error}
		<div class="error-message">
			<p>{error}</p>
			<Button onclick={loadMagazines}>Riprova</Button>
		</div>
	{:else if magazinesList.length === 0}
		<EmptyState
			title="Nessun numero"
			description="Non ci sono ancora numeri della rivista. Crea il primo!"
		>
			{#snippet action()}
				<Button href="/magazines/new">
					<Plus size={18} />
					Crea Numero
				</Button>
			{/snippet}
		</EmptyState>
	{:else}
		<div class="magazines-grid">
			{#each magazinesList as magazine}
				<Card>
					{#snippet header()}
						<div class="magazine-header">
							<span class="magazine-number">GEKO #{magazine.numero}</span>
							<Badge variant={magazine.stato === 'pubblicato' ? 'success' : 'warning'}>
								{magazine.stato}
							</Badge>
						</div>
					{/snippet}

					<div class="magazine-content">
						<div class="magazine-info">
							<div class="info-row">
								<Calendar size={16} />
								<span>{magazine.mese} {magazine.anno}</span>
							</div>
							<div class="info-row">
								<FileText size={16} />
								<span>{magazine.article_count} articoli</span>
							</div>
						</div>

						{#if magazine.copertina}
							<div class="magazine-cover">
								<img src={magazine.copertina.url} alt="Copertina GEKO #{magazine.numero}" />
							</div>
						{/if}
					</div>

					{#snippet footer()}
						<div class="magazine-actions">
							<Button href="/magazines/{magazine.id}" variant="outline" size="sm">
								Dettagli
							</Button>
							{#if magazine.stato === 'pubblicato'}
								<Button
									href="/api/magazines/{magazine.id}/pdf"
									variant="secondary"
									size="sm"
								>
									<Download size={14} />
									PDF
								</Button>
							{/if}
							<Button
								variant="ghost"
								size="sm"
								onclick={() => confirmDelete(magazine)}
							>
								<Trash2 size={14} />
							</Button>
						</div>
					{/snippet}
				</Card>
			{/each}
		</div>
	{/if}
</div>

<Modal bind:open={deleteModal} title="Conferma Eliminazione" size="sm">
	<p>
		Sei sicuro di voler eliminare il numero <strong>GEKO #{magazineToDelete?.numero}</strong>?
	</p>
	<p class="warning-text">Questa azione non può essere annullata.</p>

	{#snippet footer()}
		<Button variant="ghost" onclick={() => deleteModal = false}>
			Annulla
		</Button>
		<Button variant="danger" onclick={handleDelete} loading={deleting}>
			Elimina
		</Button>
	{/snippet}
</Modal>

<style>
	.magazines-page {
		animation: fadeIn var(--transition-base);
	}

	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: var(--space-8);
	}

	.page-header h1 {
		margin-bottom: var(--space-2);
	}

	.page-header p {
		color: var(--geko-gray);
		margin: 0;
	}

	.magazines-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: var(--space-6);
	}

	.magazine-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.magazine-number {
		font-family: var(--font-display);
		font-size: var(--text-xl);
		font-weight: 700;
		color: var(--geko-gold);
	}

	.magazine-content {
		display: flex;
		gap: var(--space-4);
	}

	.magazine-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.info-row {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		color: var(--geko-gray);
		font-size: var(--text-sm);
	}

	.magazine-cover {
		width: 80px;
		height: 100px;
		border-radius: var(--radius-md);
		overflow: hidden;
		flex-shrink: 0;
	}

	.magazine-cover img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.magazine-actions {
		display: flex;
		gap: var(--space-2);
	}

	.error-message {
		background: var(--color-danger-light);
		color: var(--color-danger);
		padding: var(--space-6);
		border-radius: var(--radius-md);
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-4);
	}

	.warning-text {
		color: var(--color-danger);
		font-size: var(--text-sm);
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
