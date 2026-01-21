<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		ArrowLeft, Edit, Download, FileText, Plus, Trash2,
		ChevronUp, ChevronDown, CheckCircle, AlertCircle, Loader, Image as ImageIcon
	} from 'lucide-svelte';
	import { Button, Badge, Card, Loading, Modal, Input, Textarea, Select } from '$lib/components/ui';
	import { magazines, articles as articlesApi, images as imagesApi } from '$lib/api';
	import type { Magazine, Article, Image } from '$lib/api';

	const magazineId = $derived(parseInt($page.params.id));

	let magazine = $state<Magazine | null>(null);
	let allArticles = $state<Article[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Edit mode
	let editing = $state(false);
	let editData = $state({
		numero: '',
		mese: '',
		anno: '',
		stato: 'bozza',
		editoriale: '',
		editoriale_autore: '',
		copertina_id: null as number | null
	});
	let saving = $state(false);

	// Build PDF
	let building = $state(false);
	let buildResult = $state<{ status: string; error?: string } | null>(null);

	// Add article modal
	let addArticleModal = $state(false);
	let selectedArticleId = $state<number | null>(null);
	let addingArticle = $state(false);

	// Delete confirmation
	let deleteModal = $state(false);
	let deleting = $state(false);

	// Cover image selection
	let coverModal = $state(false);
	let availableImages = $state<Image[]>([]);
	let loadingImages = $state(false);

	const mesi = [
		'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
		'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
	];

	onMount(async () => {
		await loadMagazine();
	});

	async function loadMagazine() {
		loading = true;
		error = null;
		try {
			const [mag, arts] = await Promise.all([
				magazines.get(magazineId),
				articlesApi.list()
			]);
			magazine = mag;
			allArticles = arts;
			editData = {
				numero: mag.numero,
				mese: mag.mese,
				anno: mag.anno,
				stato: mag.stato,
				editoriale: mag.editoriale,
				editoriale_autore: mag.editoriale_autore,
				copertina_id: mag.copertina_id
			};
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore nel caricamento';
		} finally {
			loading = false;
		}
	}

	async function handleSave() {
		if (!magazine) return;

		saving = true;
		error = null;
		try {
			magazine = await magazines.update(magazine.id, editData);
			editing = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante il salvataggio';
		} finally {
			saving = false;
		}
	}

	async function handleBuild() {
		if (!magazine) return;

		building = true;
		buildResult = null;
		try {
			const result = await magazines.build(magazine.id);
			buildResult = result;
			if (result.status === 'success') {
				// Refresh to update state
				await loadMagazine();
			}
		} catch (e) {
			buildResult = { status: 'error', error: e instanceof Error ? e.message : 'Errore' };
		} finally {
			building = false;
		}
	}

	async function handleAddArticle() {
		if (!magazine || !selectedArticleId) return;

		addingArticle = true;
		try {
			await magazines.addArticle(magazine.id, selectedArticleId);
			await loadMagazine();
			addArticleModal = false;
			selectedArticleId = null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore';
		} finally {
			addingArticle = false;
		}
	}

	async function handleRemoveArticle(articleId: number) {
		if (!magazine) return;

		try {
			await magazines.removeArticle(magazine.id, articleId);
			await loadMagazine();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore';
		}
	}

	async function handleMoveArticle(index: number, direction: 'up' | 'down') {
		if (!magazine) return;

		const articles = [...magazine.articles];
		const newIndex = direction === 'up' ? index - 1 : index + 1;

		// Swap articles
		[articles[index], articles[newIndex]] = [articles[newIndex], articles[index]];

		// Get new order of IDs
		const articleIds = articles.map(a => a.id);

		console.log('Reordering articles:', { magazineId: magazine.id, articleIds });

		try {
			await magazines.reorderArticles(magazine.id, articleIds);
			await loadMagazine();
		} catch (e) {
			console.error('Reorder error:', e);
			error = e instanceof Error ? e.message : 'Errore nel riordino';
		}
	}

	async function handleDelete() {
		if (!magazine) return;

		deleting = true;
		try {
			await magazines.delete(magazine.id);
			goto('/magazines');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante la cancellazione';
		} finally {
			deleting = false;
		}
	}

	async function openCoverModal() {
		coverModal = true;
		loadingImages = true;
		try {
			availableImages = await imagesApi.list();
		} catch (e) {
			console.error('Error loading images:', e);
		} finally {
			loadingImages = false;
		}
	}

	function selectCover(image: Image | null) {
		editData.copertina_id = image?.id ?? null;
		coverModal = false;
	}

	const selectedCoverImage = $derived(
		availableImages.find(img => img.id === editData.copertina_id) || magazine?.copertina
	);

	const availableArticles = $derived(
		allArticles.filter(a => !magazine?.articles.some(ma => ma.id === a.id))
	);
</script>

<svelte:head>
	<title>{magazine ? `GEKO #${magazine.numero}` : 'Dettaglio Numero'} - GEKO Radio Magazine</title>
</svelte:head>

<div class="magazine-detail">
	<header class="page-header">
		<Button href="/magazines" variant="ghost" size="sm">
			<ArrowLeft size={18} />
			Torna ai numeri
		</Button>
	</header>

	{#if loading}
		<Loading text="Caricamento..." />
	{:else if error}
		<div class="error-message">
			<p>{error}</p>
			<Button onclick={loadMagazine}>Riprova</Button>
		</div>
	{:else if magazine}
		<div class="magazine-header">
			<div class="magazine-title">
				<h1>GEKO #{magazine.numero}</h1>
				<Badge variant={magazine.stato === 'pubblicato' ? 'success' : 'warning'}>
					{magazine.stato}
				</Badge>
			</div>
			<p class="magazine-date">{magazine.mese} {magazine.anno}</p>
		</div>

		<div class="content-grid">
			<section class="magazine-info-section">
				<Card>
					{#snippet header()}
						<div class="card-header-row">
							<h2>Informazioni</h2>
							{#if !editing}
								<Button variant="ghost" size="sm" onclick={() => editing = true}>
									<Edit size={16} />
									Modifica
								</Button>
							{/if}
						</div>
					{/snippet}

					{#if editing}
						<form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
							<div class="form-grid">
								<Input label="Numero" bind:value={editData.numero} required />
								<Select label="Mese" bind:value={editData.mese}>
									{#each mesi as m}
										<option value={m}>{m}</option>
									{/each}
								</Select>
								<Input label="Anno" bind:value={editData.anno} required />
							</div>

							<Select label="Stato" bind:value={editData.stato}>
								<option value="bozza">Bozza</option>
								<option value="pubblicato">Pubblicato</option>
							</Select>

							<Textarea
								label="Editoriale"
								bind:value={editData.editoriale}
								rows={4}
							/>

							<Input
								label="Autore Editoriale"
								bind:value={editData.editoriale_autore}
							/>

							<div class="cover-selector">
								<label class="cover-label">Immagine Prima Pagina</label>
								<div class="cover-preview-container">
									{#if selectedCoverImage}
										<div class="cover-preview">
											<img src={selectedCoverImage.url} alt="Copertina selezionata" />
										</div>
									{:else}
										<div class="cover-placeholder">
											<ImageIcon size={32} />
											<span>Nessuna immagine</span>
										</div>
									{/if}
									<div class="cover-actions">
										<Button type="button" variant="outline" size="sm" onclick={openCoverModal}>
											{selectedCoverImage ? 'Cambia' : 'Seleziona'}
										</Button>
										{#if selectedCoverImage}
											<Button type="button" variant="ghost" size="sm" onclick={() => editData.copertina_id = null}>
												Rimuovi
											</Button>
										{/if}
									</div>
								</div>
							</div>

							<div class="form-actions">
								<Button variant="ghost" onclick={() => editing = false}>
									Annulla
								</Button>
								<Button type="submit" loading={saving}>
									Salva
								</Button>
							</div>
						</form>
					{:else}
						<dl class="info-list">
							<div>
								<dt>Editoriale</dt>
								<dd>{magazine.editoriale || 'Non inserito'}</dd>
							</div>
							{#if magazine.editoriale_autore}
								<div>
									<dt>Autore Editoriale</dt>
									<dd>{magazine.editoriale_autore}</dd>
								</div>
							{/if}
						</dl>
					{/if}
				</Card>

				<Card>
					{#snippet header()}
						<h2>Azioni</h2>
					{/snippet}

					<div class="actions-list">
						<Button onclick={handleBuild} loading={building} disabled={magazine.articles.length === 0}>
							{#if building}
								Generazione in corso...
							{:else}
								Genera PDF
							{/if}
						</Button>

						{#if magazine.stato === 'pubblicato'}
							<Button href="/api/magazines/{magazine.id}/pdf" variant="secondary">
								<Download size={18} />
								Scarica PDF
							</Button>
						{/if}

						<Button variant="danger" onclick={() => deleteModal = true}>
							<Trash2 size={18} />
							Elimina Numero
						</Button>
					</div>

					{#if buildResult}
						<div class="build-result build-{buildResult.status}">
							{#if buildResult.status === 'success'}
								<CheckCircle size={20} />
								<span>PDF generato con successo!</span>
							{:else}
								<AlertCircle size={20} />
								<span>{buildResult.error || 'Errore durante la generazione'}</span>
							{/if}
						</div>
					{/if}
				</Card>
			</section>

			<section class="articles-section">
				<Card>
					{#snippet header()}
						<div class="card-header-row">
							<h2>Articoli ({magazine.articles.length})</h2>
							<Button variant="outline" size="sm" onclick={() => addArticleModal = true}>
								<Plus size={16} />
								Aggiungi
							</Button>
						</div>
					{/snippet}

					{#if magazine.articles.length === 0}
						<p class="no-articles">
							Nessun articolo in questo numero.<br />
							Aggiungi articoli per poter generare il PDF.
						</p>
					{:else}
						<ul class="articles-list">
							{#each magazine.articles as article, idx}
								<li class="article-item">
									<div class="article-reorder">
										<button
											class="reorder-btn"
											onclick={() => handleMoveArticle(idx, 'up')}
											disabled={idx === 0}
											aria-label="Sposta su"
										>
											<ChevronUp size={16} />
										</button>
										<button
											class="reorder-btn"
											onclick={() => handleMoveArticle(idx, 'down')}
											disabled={idx === magazine.articles.length - 1}
											aria-label="Sposta giù"
										>
											<ChevronDown size={16} />
										</button>
									</div>
									<span class="article-order">{idx + 1}</span>
									<a href="/articles/{article.id}" class="article-info">
										<strong>{article.titolo}</strong>
										{#if article.autore}
											<span class="article-author">{article.autore}</span>
										{/if}
									</a>
									<button
										class="remove-btn"
										onclick={() => handleRemoveArticle(article.id)}
										aria-label="Rimuovi articolo"
									>
										<Trash2 size={14} />
									</button>
								</li>
							{/each}
						</ul>
					{/if}
				</Card>
			</section>
		</div>
	{/if}
</div>

<Modal bind:open={addArticleModal} title="Aggiungi Articolo" size="md">
	{#if availableArticles.length === 0}
		<p>Non ci sono articoli disponibili da aggiungere.</p>
		<p>
			<a href="/articles/new">Crea un nuovo articolo</a>
		</p>
	{:else}
		<Select label="Seleziona articolo" bind:value={selectedArticleId}>
			<option value={null}>Seleziona...</option>
			{#each availableArticles as article}
				<option value={article.id}>
					{article.titolo} {article.autore ? `(${article.autore})` : ''}
				</option>
			{/each}
		</Select>
	{/if}

	{#snippet footer()}
		<Button variant="ghost" onclick={() => addArticleModal = false}>
			Annulla
		</Button>
		<Button
			onclick={handleAddArticle}
			loading={addingArticle}
			disabled={!selectedArticleId}
		>
			Aggiungi
		</Button>
	{/snippet}
</Modal>

<Modal bind:open={deleteModal} title="Conferma Eliminazione" size="sm">
	<p>
		Sei sicuro di voler eliminare <strong>GEKO #{magazine?.numero}</strong>?
	</p>
	<p class="warning-text">
		Questa azione non può essere annullata. Gli articoli non verranno eliminati.
	</p>

	{#snippet footer()}
		<Button variant="ghost" onclick={() => deleteModal = false}>
			Annulla
		</Button>
		<Button variant="danger" onclick={handleDelete} loading={deleting}>
			Elimina
		</Button>
	{/snippet}
</Modal>

<Modal bind:open={coverModal} title="Seleziona Immagine Prima Pagina" size="lg">
	{#if loadingImages}
		<Loading text="Caricamento immagini..." />
	{:else if availableImages.length === 0}
		<p>Non ci sono immagini disponibili. <a href="/media">Carica delle immagini</a> prima.</p>
	{:else}
		<div class="image-grid">
			{#each availableImages as image}
				<button
					type="button"
					class="image-option"
					class:selected={editData.copertina_id === image.id}
					onclick={() => selectCover(image)}
				>
					<img src={image.url} alt={image.alt_text || image.original_filename} />
					<span class="image-name">{image.original_filename}</span>
				</button>
			{/each}
		</div>
	{/if}

	{#snippet footer()}
		<Button variant="ghost" onclick={() => coverModal = false}>
			Annulla
		</Button>
	{/snippet}
</Modal>

<style>
	.magazine-detail {
		animation: fadeIn var(--transition-base);
	}

	.page-header {
		margin-bottom: var(--space-4);
	}

	.magazine-header {
		margin-bottom: var(--space-6);
	}

	.magazine-title {
		display: flex;
		align-items: center;
		gap: var(--space-4);
	}

	.magazine-title h1 {
		color: var(--geko-gold);
	}

	.magazine-date {
		color: var(--geko-gray);
		font-size: var(--text-lg);
		margin: var(--space-2) 0 0;
	}

	.content-grid {
		display: grid;
		grid-template-columns: 1fr 1.5fr;
		gap: var(--space-6);
	}

	.card-header-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.card-header-row h2 {
		font-size: var(--text-lg);
		margin: 0;
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-4);
		margin-bottom: var(--space-4);
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
		margin-top: var(--space-4);
		padding-top: var(--space-4);
		border-top: 1px solid var(--geko-gray-light);
	}

	.info-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.info-list dt {
		font-size: var(--text-sm);
		color: var(--geko-gray);
		margin-bottom: var(--space-1);
	}

	.info-list dd {
		margin: 0;
	}

	.actions-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.build-result {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3);
		border-radius: var(--radius-md);
		margin-top: var(--space-4);
		font-size: var(--text-sm);
	}

	.build-success {
		background: var(--color-success-light);
		color: var(--color-success);
	}

	.build-error {
		background: var(--color-danger-light);
		color: var(--color-danger);
	}

	.no-articles {
		text-align: center;
		color: var(--geko-gray);
		padding: var(--space-6);
	}

	.articles-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.article-item {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-3);
		border-bottom: 1px solid var(--geko-gray-light);
	}

	.article-item:last-child {
		border-bottom: none;
	}

	.article-reorder {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.reorder-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 18px;
		padding: 0;
		background: transparent;
		border: 1px solid var(--geko-gray-light);
		border-radius: 3px;
		color: var(--geko-gray);
		cursor: pointer;
		transition: all 0.15s;
	}

	.reorder-btn:hover:not(:disabled) {
		background: var(--geko-gold);
		border-color: var(--geko-gold);
		color: white;
	}

	.reorder-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.article-order {
		font-family: var(--font-display);
		font-size: var(--text-sm);
		color: var(--geko-gray);
		width: 24px;
		text-align: center;
	}

	.article-info {
		flex: 1;
		text-decoration: none;
		color: inherit;
	}

	.article-info:hover {
		text-decoration: none;
	}

	.article-info strong {
		display: block;
		font-size: var(--text-sm);
	}

	.article-info:hover strong {
		color: var(--geko-magenta);
	}

	.article-author {
		font-size: var(--text-xs);
		color: var(--geko-gray);
	}

	.remove-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-2);
		background: none;
		border: none;
		color: var(--geko-gray);
		cursor: pointer;
		border-radius: var(--radius-md);
	}

	.remove-btn:hover {
		background: var(--color-danger-light);
		color: var(--color-danger);
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

	/* Cover selector */
	.cover-selector {
		margin-top: var(--space-4);
	}

	.cover-label {
		display: block;
		font-size: var(--text-sm);
		font-weight: 500;
		color: var(--geko-dark);
		margin-bottom: var(--space-2);
	}

	.cover-preview-container {
		display: flex;
		align-items: flex-start;
		gap: var(--space-4);
	}

	.cover-preview {
		width: 120px;
		height: 160px;
		border-radius: var(--radius-md);
		overflow: hidden;
		border: 2px solid var(--geko-gold);
	}

	.cover-preview img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.cover-placeholder {
		width: 120px;
		height: 160px;
		border-radius: var(--radius-md);
		border: 2px dashed var(--geko-gray-light);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		color: var(--geko-gray);
		font-size: var(--text-sm);
	}

	.cover-actions {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	/* Image grid in modal */
	.image-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		gap: var(--space-3);
		max-height: 400px;
		overflow-y: auto;
	}

	.image-option {
		background: none;
		border: 2px solid transparent;
		border-radius: var(--radius-md);
		padding: var(--space-2);
		cursor: pointer;
		transition: all var(--transition-fast);
		text-align: center;
	}

	.image-option:hover {
		border-color: var(--geko-gray-light);
	}

	.image-option.selected {
		border-color: var(--geko-gold);
		background: rgba(196, 163, 90, 0.1);
	}

	.image-option img {
		width: 100%;
		aspect-ratio: 3/4;
		object-fit: cover;
		border-radius: var(--radius-sm);
	}

	.image-option .image-name {
		display: block;
		font-size: var(--text-xs);
		color: var(--geko-gray);
		margin-top: var(--space-1);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	@media (max-width: 768px) {
		.content-grid {
			grid-template-columns: 1fr;
		}

		.form-grid {
			grid-template-columns: 1fr;
		}
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
