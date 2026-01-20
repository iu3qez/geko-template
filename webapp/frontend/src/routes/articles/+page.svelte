<script lang="ts">
	import { onMount } from 'svelte';
	import { Plus, Search, Trash2, Edit, Sparkles, BookOpen } from 'lucide-svelte';
	import { Button, Card, Badge, Loading, EmptyState, Modal, Input } from '$lib/components/ui';
	import { articles } from '$lib/api';
	import type { Article } from '$lib/api';

	let articlesList = $state<Article[]>([]);
	let filteredArticles = $state<Article[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchQuery = $state('');

	let deleteModal = $state(false);
	let articleToDelete = $state<Article | null>(null);
	let deleting = $state(false);

	let generatingSummary = $state<number | null>(null);

	onMount(async () => {
		await loadArticles();
	});

	async function loadArticles() {
		loading = true;
		error = null;
		try {
			articlesList = await articles.list();
			filteredArticles = articlesList;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore nel caricamento';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			filteredArticles = articlesList.filter(a =>
				a.titolo.toLowerCase().includes(query) ||
				a.autore.toLowerCase().includes(query) ||
				a.contenuto_md.toLowerCase().includes(query)
			);
		} else {
			filteredArticles = articlesList;
		}
	});

	function confirmDelete(article: Article) {
		articleToDelete = article;
		deleteModal = true;
	}

	async function handleDelete() {
		if (!articleToDelete) return;

		deleting = true;
		try {
			await articles.delete(articleToDelete.id);
			articlesList = articlesList.filter(a => a.id !== articleToDelete!.id);
			filteredArticles = filteredArticles.filter(a => a.id !== articleToDelete!.id);
			deleteModal = false;
			articleToDelete = null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante la cancellazione';
		} finally {
			deleting = false;
		}
	}

	async function generateSummary(article: Article) {
		generatingSummary = article.id;
		try {
			const updated = await articles.generateSummary(article.id);
			// Update in list
			const idx = articlesList.findIndex(a => a.id === article.id);
			if (idx !== -1) {
				articlesList[idx] = updated;
			}
			const fidx = filteredArticles.findIndex(a => a.id === article.id);
			if (fidx !== -1) {
				filteredArticles[fidx] = updated;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore generazione sommario';
		} finally {
			generatingSummary = null;
		}
	}
</script>

<svelte:head>
	<title>Articoli - GEKO Radio Magazine</title>
</svelte:head>

<div class="articles-page">
	<header class="page-header">
		<div>
			<h1>Articoli</h1>
			<p>Tutti gli articoli della rivista</p>
		</div>
		<Button href="/articles/new">
			<Plus size={18} />
			Nuovo Articolo
		</Button>
	</header>

	<div class="search-bar">
		<Search size={18} />
		<input
			type="search"
			placeholder="Cerca articoli..."
			bind:value={searchQuery}
		/>
	</div>

	{#if loading}
		<Loading text="Caricamento articoli..." />
	{:else if error}
		<div class="error-message">
			<p>{error}</p>
			<Button onclick={loadArticles}>Riprova</Button>
		</div>
	{:else if articlesList.length === 0}
		<EmptyState
			title="Nessun articolo"
			description="Non ci sono ancora articoli. Crea il primo!"
		>
			{#snippet action()}
				<Button href="/articles/new">
					<Plus size={18} />
					Crea Articolo
				</Button>
			{/snippet}
		</EmptyState>
	{:else if filteredArticles.length === 0}
		<EmptyState
			title="Nessun risultato"
			description="Nessun articolo corrisponde alla ricerca."
		>
			{#snippet action()}
				<Button variant="ghost" onclick={() => searchQuery = ''}>
					Cancella ricerca
				</Button>
			{/snippet}
		</EmptyState>
	{:else}
		<div class="articles-grid">
			{#each filteredArticles as article}
				<Card>
					{#snippet header()}
						<div class="article-header">
							<h3 class="article-title">{article.titolo}</h3>
							{#if article.sommario_llm}
								<span class="has-summary" title="Ha sommario AI">
									<Sparkles size={16} />
								</span>
							{/if}
						</div>
					{/snippet}

					<div class="article-content">
						{#if article.sottotitolo}
							<p class="article-subtitle">{article.sottotitolo}</p>
						{/if}

						{#if article.autore}
							<p class="article-author">
								di <strong>{article.autore}</strong>
								{#if article.nome_autore}
									({article.nome_autore})
								{/if}
							</p>
						{/if}

						{#if article.magazines.length > 0}
							<div class="article-magazines">
								{#each article.magazines as mag}
									<Badge variant={mag.stato === 'pubblicato' ? 'success' : 'gold'}>
										<BookOpen size={12} />
										#{mag.numero}
									</Badge>
								{/each}
							</div>
						{/if}

						{#if article.sommario_llm}
							<p class="article-summary">{article.sommario_llm}</p>
						{/if}
					</div>

					{#snippet footer()}
						<div class="article-actions">
							<Button href="/articles/{article.id}" variant="outline" size="sm">
								<Edit size={14} />
								Modifica
							</Button>
							<Button
								variant="ghost"
								size="sm"
								onclick={() => generateSummary(article)}
								loading={generatingSummary === article.id}
								disabled={!article.contenuto_md}
							>
								<Sparkles size={14} />
								{article.sommario_llm ? 'Rigenera' : 'Sommario AI'}
							</Button>
							<Button
								variant="ghost"
								size="sm"
								onclick={() => confirmDelete(article)}
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
		Sei sicuro di voler eliminare l'articolo <strong>{articleToDelete?.titolo}</strong>?
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
	.articles-page {
		animation: fadeIn var(--transition-base);
	}

	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: var(--space-6);
	}

	.page-header h1 {
		margin-bottom: var(--space-2);
	}

	.page-header p {
		color: var(--geko-gray);
		margin: 0;
	}

	.search-bar {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-3) var(--space-4);
		background: var(--geko-white);
		border: 2px solid var(--geko-gray-light);
		border-radius: var(--radius-md);
		margin-bottom: var(--space-6);
		color: var(--geko-gray);
	}

	.search-bar:focus-within {
		border-color: var(--geko-gold);
		box-shadow: 0 0 0 3px rgba(196, 163, 90, 0.2);
	}

	.search-bar input {
		flex: 1;
		border: none;
		background: none;
		font-size: var(--text-base);
		color: var(--geko-dark);
		outline: none;
	}

	.articles-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
		gap: var(--space-6);
	}

	.article-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-2);
	}

	.article-title {
		font-size: var(--text-lg);
		margin: 0;
		line-height: 1.4;
	}

	.has-summary {
		color: var(--geko-magenta);
		flex-shrink: 0;
	}

	.article-content {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.article-subtitle {
		color: var(--geko-gray);
		font-size: var(--text-sm);
		margin: 0;
	}

	.article-author {
		font-size: var(--text-sm);
		margin: 0;
	}

	.article-magazines {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}

	.article-magazines :global(.badge) {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
	}

	.article-summary {
		font-size: var(--text-sm);
		color: var(--geko-gray);
		font-style: italic;
		margin: 0;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.article-actions {
		display: flex;
		gap: var(--space-2);
		flex-wrap: wrap;
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
