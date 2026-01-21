<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		ArrowLeft, Save, Trash2, Sparkles, BookOpen, Eye, Edit as EditIcon
	} from 'lucide-svelte';
	import { Button, Input, Textarea, Card, Badge, Loading, Modal } from '$lib/components/ui';
	import { articles, magazines as magazinesApi } from '$lib/api';
	import type { Article, Magazine } from '$lib/api';
	import { marked } from 'marked';

	// Configure marked for safe HTML
	marked.setOptions({
		breaks: true,
		gfm: true
	});

	const articleId = $derived(parseInt($page.params.id));

	let article = $state<Article | null>(null);
	let allMagazines = $state<Magazine[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Edit state
	let editData = $state({
		titolo: '',
		sottotitolo: '',
		autore: '',
		nome_autore: '',
		contenuto_md: ''
	});
	let saving = $state(false);
	let hasChanges = $state(false);

	// AI summary
	let generatingSummary = $state(false);
	let editingSummary = $state(false);
	let editedSummary = $state('');
	let savingSummary = $state(false);

	// Assign modal
	let assignModal = $state(false);
	let selectedMagazines = $state<number[]>([]);
	let assigning = $state(false);

	// Delete modal
	let deleteModal = $state(false);
	let deleting = $state(false);

	// Preview mode
	let previewMode = $state(false);

	onMount(async () => {
		await loadArticle();
	});

	async function loadArticle() {
		loading = true;
		error = null;
		try {
			const [art, mags] = await Promise.all([
				articles.get(articleId),
				magazinesApi.list()
			]);
			article = art;
			allMagazines = mags;
			editData = {
				titolo: art.titolo,
				sottotitolo: art.sottotitolo,
				autore: art.autore,
				nome_autore: art.nome_autore,
				contenuto_md: art.contenuto_md
			};
			selectedMagazines = art.magazines.map(m => m.id);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore nel caricamento';
		} finally {
			loading = false;
		}
	}

	function checkChanges() {
		if (!article) return;
		hasChanges =
			editData.titolo !== article.titolo ||
			editData.sottotitolo !== article.sottotitolo ||
			editData.autore !== article.autore ||
			editData.nome_autore !== article.nome_autore ||
			editData.contenuto_md !== article.contenuto_md;
	}

	async function handleSave() {
		if (!article) return;

		saving = true;
		error = null;
		try {
			article = await articles.update(article.id, editData);
			hasChanges = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante il salvataggio';
		} finally {
			saving = false;
		}
	}

	async function handleGenerateSummary() {
		if (!article) return;

		generatingSummary = true;
		try {
			article = await articles.generateSummary(article.id);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore generazione sommario';
		} finally {
			generatingSummary = false;
		}
	}

	function startEditingSummary() {
		editedSummary = article?.sommario_llm || '';
		editingSummary = true;
	}

	async function saveSummary() {
		if (!article) return;

		savingSummary = true;
		try {
			article = await articles.update(article.id, { sommario_llm: editedSummary });
			editingSummary = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore salvataggio sommario';
		} finally {
			savingSummary = false;
		}
	}

	function openAssignModal() {
		selectedMagazines = article?.magazines.map(m => m.id) || [];
		assignModal = true;
	}

	async function handleAssign() {
		if (!article) return;

		assigning = true;
		try {
			article = await articles.assign(article.id, selectedMagazines);
			assignModal = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore assegnazione';
		} finally {
			assigning = false;
		}
	}

	async function handleDelete() {
		if (!article) return;

		deleting = true;
		try {
			await articles.delete(article.id);
			goto('/articles');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante la cancellazione';
		} finally {
			deleting = false;
		}
	}

	function toggleMagazine(magId: number) {
		if (selectedMagazines.includes(magId)) {
			selectedMagazines = selectedMagazines.filter(id => id !== magId);
		} else {
			selectedMagazines = [...selectedMagazines, magId];
		}
	}
</script>

<svelte:head>
	<title>{article ? article.titolo : 'Modifica Articolo'} - GEKO Radio Magazine</title>
</svelte:head>

<div class="article-edit-page">
	<header class="page-header">
		<Button href="/articles" variant="ghost" size="sm">
			<ArrowLeft size={18} />
			Torna agli articoli
		</Button>
	</header>

	{#if loading}
		<Loading text="Caricamento..." />
	{:else if error}
		<div class="error-message">
			<p>{error}</p>
			<Button onclick={loadArticle}>Riprova</Button>
		</div>
	{:else if article}
		<div class="edit-header">
			<div class="title-row">
				<h1>Modifica Articolo</h1>
				{#if hasChanges}
					<Badge variant="warning">Non salvato</Badge>
				{/if}
			</div>
			<div class="header-actions">
				<Button variant="ghost" onclick={() => previewMode = !previewMode}>
					{#if previewMode}
						<EditIcon size={18} />
						Modifica
					{:else}
						<Eye size={18} />
						Preview
					{/if}
				</Button>
				<Button
					variant="outline"
					onclick={handleGenerateSummary}
					loading={generatingSummary}
					disabled={!editData.contenuto_md}
				>
					<Sparkles size={18} />
					{article.sommario_llm ? 'Rigenera Sommario' : 'Genera Sommario AI'}
				</Button>
				<Button onclick={handleSave} loading={saving} disabled={!hasChanges}>
					<Save size={18} />
					Salva
				</Button>
			</div>
		</div>

		<div class="content-layout">
			<div class="main-content">
				{#if previewMode}
					<Card>
						<div class="preview-content">
							<h2>{editData.titolo}</h2>
							{#if editData.sottotitolo}
								<p class="preview-subtitle">{editData.sottotitolo}</p>
							{/if}
							{#if editData.autore}
								<p class="preview-author">
									di <strong>{editData.autore}</strong>
									{#if editData.nome_autore}
										({editData.nome_autore})
									{/if}
								</p>
							{/if}
							<div class="preview-body markdown-content">
								{@html marked(editData.contenuto_md || '')}
							</div>
						</div>
					</Card>
				{:else}
					<Card>
						<form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
							<div class="form-section">
								<Input
									label="Titolo *"
									bind:value={editData.titolo}
									oninput={checkChanges}
									required
								/>

								<Input
									label="Sottotitolo"
									bind:value={editData.sottotitolo}
									oninput={checkChanges}
								/>
							</div>

							<div class="form-grid">
								<Input
									label="Autore (Nominativo)"
									placeholder="es. IK2XYZ"
									bind:value={editData.autore}
									oninput={checkChanges}
								/>

								<Input
									label="Nome Autore"
									placeholder="es. Marco Rossi"
									bind:value={editData.nome_autore}
									oninput={checkChanges}
								/>
							</div>

							<div class="form-section">
								<Textarea
									label="Contenuto (Markdown)"
									bind:value={editData.contenuto_md}
									oninput={checkChanges}
									rows={25}
								/>
							</div>
						</form>
					</Card>
				{/if}
			</div>

			<aside class="sidebar">
				<Card>
					{#snippet header()}
						<div class="sidebar-header">
							<h3>Numeri</h3>
							<Button variant="ghost" size="sm" onclick={openAssignModal}>
								<BookOpen size={14} />
								Assegna
							</Button>
						</div>
					{/snippet}

					{#if article.magazines.length === 0}
						<p class="no-magazines">Non assegnato a nessun numero</p>
					{:else}
						<ul class="magazines-list">
							{#each article.magazines as mag}
								<li>
									<a href="/magazines/{mag.id}">
										<Badge variant={mag.stato === 'pubblicato' ? 'success' : 'gold'}>
											GEKO #{mag.numero}
										</Badge>
									</a>
								</li>
							{/each}
						</ul>
					{/if}
				</Card>

					<Card>
					{#snippet header()}
						<div class="card-header-row">
							<h3>Sommario AI</h3>
							{#if article.sommario_llm && !editingSummary}
								<Button variant="ghost" size="sm" onclick={startEditingSummary}>
									<EditIcon size={14} />
									Modifica
								</Button>
							{/if}
						</div>
					{/snippet}
					{#if editingSummary}
						<Textarea
							bind:value={editedSummary}
							rows={4}
							placeholder="Inserisci il sommario..."
						/>
						<div class="summary-actions">
							<Button size="sm" onclick={saveSummary} loading={savingSummary}>
								Salva
							</Button>
							<Button variant="ghost" size="sm" onclick={() => editingSummary = false}>
								Annulla
							</Button>
						</div>
					{:else if article.sommario_llm}
						<p class="ai-summary">{article.sommario_llm}</p>
					{:else}
						<p class="no-summary">Nessun sommario generato</p>
					{/if}
				</Card>

				<Card>
					{#snippet header()}
						<h3>Azioni</h3>
					{/snippet}
					<Button variant="danger" onclick={() => deleteModal = true}>
						<Trash2 size={18} />
						Elimina Articolo
					</Button>
				</Card>
			</aside>
		</div>
	{/if}
</div>

<Modal bind:open={assignModal} title="Assegna a Numeri" size="md">
	{#if allMagazines.length === 0}
		<p>Non ci sono numeri disponibili.</p>
	{:else}
		<p class="assign-hint">Seleziona i numeri a cui assegnare questo articolo:</p>
		<ul class="magazine-checkboxes">
			{#each allMagazines as mag}
				<li>
					<label>
						<input
							type="checkbox"
							checked={selectedMagazines.includes(mag.id)}
							onchange={() => toggleMagazine(mag.id)}
						/>
						<span>
							GEKO #{mag.numero} - {mag.mese} {mag.anno}
							{#if mag.stato === 'pubblicato'}
								<Badge variant="success">Pubblicato</Badge>
							{/if}
						</span>
					</label>
				</li>
			{/each}
		</ul>
	{/if}

	{#snippet footer()}
		<Button variant="ghost" onclick={() => assignModal = false}>
			Annulla
		</Button>
		<Button onclick={handleAssign} loading={assigning}>
			Salva
		</Button>
	{/snippet}
</Modal>

<Modal bind:open={deleteModal} title="Conferma Eliminazione" size="sm">
	<p>
		Sei sicuro di voler eliminare l'articolo <strong>{article?.titolo}</strong>?
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
	.article-edit-page {
		animation: fadeIn var(--transition-base);
	}

	.page-header {
		margin-bottom: var(--space-4);
	}

	.edit-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--space-6);
		flex-wrap: wrap;
		gap: var(--space-4);
	}

	.title-row {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.title-row h1 {
		margin: 0;
	}

	.header-actions {
		display: flex;
		gap: var(--space-3);
		flex-wrap: wrap;
	}

	.content-layout {
		display: grid;
		grid-template-columns: 1fr 300px;
		gap: var(--space-6);
	}

	.form-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
		margin-bottom: var(--space-4);
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--space-4);
		margin-bottom: var(--space-4);
	}

	.sidebar {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.sidebar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.sidebar-header h3 {
		font-size: var(--text-base);
		margin: 0;
	}

	.no-magazines {
		color: var(--geko-gray);
		font-size: var(--text-sm);
		font-style: italic;
	}

	.magazines-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}

	.magazines-list li {
		margin: 0;
	}

	.ai-summary {
		font-size: var(--text-sm);
		font-style: italic;
		color: var(--geko-gray);
		margin: 0;
	}

	.no-summary {
		font-size: var(--text-sm);
		color: var(--geko-gray-light);
		margin: 0;
	}

	.summary-actions {
		display: flex;
		gap: var(--space-2);
		margin-top: var(--space-3);
	}

	.card-header-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.card-header-row h3 {
		margin: 0;
	}

	.preview-content h2 {
		color: var(--geko-gold);
		margin-bottom: var(--space-3);
	}

	.preview-subtitle {
		font-size: var(--text-lg);
		color: var(--geko-magenta);
		margin-bottom: var(--space-2);
	}

	.preview-author {
		color: var(--geko-gray);
		margin-bottom: var(--space-6);
	}

	.preview-body {
		line-height: 1.8;
	}

	.preview-body :global(p) {
		margin-bottom: var(--space-3);
	}

	/* Markdown rendered content styles */
	.markdown-content :global(h1),
	.markdown-content :global(h2),
	.markdown-content :global(h3),
	.markdown-content :global(h4) {
		color: var(--geko-gold);
		margin-top: var(--space-6);
		margin-bottom: var(--space-3);
	}

	.markdown-content :global(h1) { font-size: var(--text-2xl); }
	.markdown-content :global(h2) { font-size: var(--text-xl); }
	.markdown-content :global(h3) { font-size: var(--text-lg); }

	.markdown-content :global(ul),
	.markdown-content :global(ol) {
		margin-left: var(--space-6);
		margin-bottom: var(--space-4);
	}

	.markdown-content :global(li) {
		margin-bottom: var(--space-2);
	}

	.markdown-content :global(blockquote) {
		border-left: 4px solid var(--geko-gold);
		padding-left: var(--space-4);
		margin: var(--space-4) 0;
		font-style: italic;
		color: var(--geko-gray);
	}

	.markdown-content :global(code) {
		background: var(--geko-dark);
		color: var(--geko-gold);
		padding: 0.2em 0.4em;
		border-radius: 4px;
		font-size: 0.9em;
	}

	.markdown-content :global(pre) {
		background: var(--geko-dark);
		padding: var(--space-4);
		border-radius: var(--radius-md);
		overflow-x: auto;
		margin-bottom: var(--space-4);
	}

	.markdown-content :global(pre code) {
		background: none;
		padding: 0;
	}

	.markdown-content :global(strong) {
		color: var(--geko-magenta);
	}

	.markdown-content :global(a) {
		color: var(--geko-magenta);
		text-decoration: underline;
	}

	.markdown-content :global(img) {
		max-width: 100%;
		height: auto;
		border-radius: var(--radius-md);
		margin: var(--space-4) 0;
	}

	.markdown-content :global(table) {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: var(--space-4);
	}

	.markdown-content :global(th),
	.markdown-content :global(td) {
		border: 1px solid var(--geko-gray);
		padding: var(--space-2) var(--space-3);
		text-align: left;
	}

	.markdown-content :global(th) {
		background: var(--geko-gold);
		color: white;
	}

	.assign-hint {
		margin-bottom: var(--space-4);
	}

	.magazine-checkboxes {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.magazine-checkboxes li {
		margin-bottom: var(--space-3);
	}

	.magazine-checkboxes label {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		cursor: pointer;
	}

	.magazine-checkboxes input[type="checkbox"] {
		width: 18px;
		height: 18px;
		cursor: pointer;
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

	@media (max-width: 900px) {
		.content-layout {
			grid-template-columns: 1fr;
		}

		.sidebar {
			order: -1;
			flex-direction: row;
			flex-wrap: wrap;
		}

		.sidebar > :global(*) {
			flex: 1;
			min-width: 200px;
		}
	}

	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}

		.header-actions {
			width: 100%;
			justify-content: flex-end;
		}
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
