<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		ArrowLeft, Save, Trash2, Sparkles, BookOpen, Eye, Edit as EditIcon, ImageIcon, HelpCircle
	} from 'lucide-svelte';
	import { Button, Input, Textarea, Card, Badge, Loading, Modal } from '$lib/components/ui';
	import { articles, magazines as magazinesApi, images as imagesApi } from '$lib/api';
	import type { Article, Magazine, Image } from '$lib/api';
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

	// Image gallery
	let imageGalleryModal = $state(false);
	let galleryImages = $state<Image[]>([]);
	let loadingImages = $state(false);
	let uploadingImage = $state(false);
	let cursorPosition = $state(0);
	const contentTextareaId = 'content-markdown-editor';

	// Syntax guide
	let syntaxGuideOpen = $state(true);

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

	async function openImageGallery() {
		// Save cursor position before opening modal
		const textarea = document.getElementById(contentTextareaId) as HTMLTextAreaElement | null;
		if (textarea) {
			cursorPosition = textarea.selectionStart;
		}
		imageGalleryModal = true;
		loadingImages = true;
		try {
			galleryImages = await imagesApi.list();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore caricamento immagini';
		} finally {
			loadingImages = false;
		}
	}

	function insertImage(image: Image) {
		const markdown = `\n![${image.alt_text || image.original_filename}](${image.url})\n`;
		const text = editData.contenuto_md;

		// Find the end of the current line/paragraph
		let insertPos = cursorPosition;
		const nextNewline = text.indexOf('\n', cursorPosition);
		if (nextNewline !== -1) {
			insertPos = nextNewline;
		} else {
			insertPos = text.length;
		}

		// Insert at position
		editData.contenuto_md = text.slice(0, insertPos) + markdown + text.slice(insertPos);
		checkChanges();
		imageGalleryModal = false;

		// Restore focus and set cursor after inserted text
		setTimeout(() => {
			const textarea = document.getElementById(contentTextareaId) as HTMLTextAreaElement | null;
			if (textarea) {
				textarea.focus();
				const newPos = insertPos + markdown.length;
				textarea.setSelectionRange(newPos, newPos);
			}
		}, 100);
	}

	async function handleImageUpload(event: Event) {
		const input = event.target as HTMLInputElement;
		const files = input.files;
		if (!files || files.length === 0) return;

		uploadingImage = true;
		try {
			const uploaded = await imagesApi.upload(files[0], article?.id);
			galleryImages = [uploaded, ...galleryImages];
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore upload immagine';
		} finally {
			uploadingImage = false;
			input.value = '';
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
									id={contentTextareaId}
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
				<!-- Syntax Guide -->
				<Card>
					{#snippet header()}
						<div class="sidebar-header">
							<h3>Sintassi Markdown</h3>
							<Button variant="ghost" size="sm" onclick={() => syntaxGuideOpen = !syntaxGuideOpen}>
								{syntaxGuideOpen ? 'Nascondi' : 'Mostra'}
							</Button>
						</div>
					{/snippet}
					{#if syntaxGuideOpen}
						<div class="syntax-guide">
							<table class="syntax-table">
								<tbody>
									<tr><td><code># Titolo</code></td><td>Titolo sezione</td></tr>
									<tr><td><code>## Sottotitolo</code></td><td>Sottosezione</td></tr>
									<tr><td><code>**grassetto**</code></td><td><strong>grassetto</strong></td></tr>
									<tr><td><code>*corsivo*</code></td><td><em>corsivo</em></td></tr>
									<tr><td><code>[testo](url)</code></td><td>Link</td></tr>
									<tr><td><code>https://...</code></td><td>Link automatico</td></tr>
									<tr><td><code>![alt](path)</code></td><td>Immagine</td></tr>
									<tr><td><code>![alt](path){'{'}width=50%{'}'}</code></td><td>Immagine con dimensione</td></tr>
									<tr><td><code>- elemento</code></td><td>Lista puntata</td></tr>
									<tr><td><code>1. elemento</code></td><td>Lista numerata</td></tr>
									<tr><td><code>&gt; citazione</code></td><td>Blockquote</td></tr>
								</tbody>
							</table>
							<details class="syntax-details">
								<summary>Tabelle</summary>
								<pre class="syntax-example">| Col1 | Col2 |
|------|------|
| A    | B    |</pre>
							</details>
							<details class="syntax-details">
								<summary>Box evidenza</summary>
								<pre class="syntax-example">!!! note "Titolo"
Contenuto del box
!!!</pre>
							</details>
						</div>
					{/if}
				</Card>

				<!-- Image Gallery -->
				<Card>
					{#snippet header()}
						<div class="sidebar-header">
							<h3>Immagini</h3>
							<Button variant="ghost" size="sm" onclick={openImageGallery}>
								<ImageIcon size={14} />
								Galleria
							</Button>
						</div>
					{/snippet}
					<p class="help-text">Usa la galleria per inserire immagini nel testo.</p>
				</Card>

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

<Modal bind:open={imageGalleryModal} title="Galleria Immagini" size="lg">
	<div class="gallery-upload">
		<label class="upload-btn">
			<input
				type="file"
				accept="image/*"
				onchange={handleImageUpload}
				disabled={uploadingImage}
			/>
			{#if uploadingImage}
				Caricamento...
			{:else}
				Carica nuova immagine
			{/if}
		</label>
	</div>

	{#if loadingImages}
		<Loading text="Caricamento immagini..." />
	{:else if galleryImages.length === 0}
		<p class="no-images">Nessuna immagine disponibile. Carica la prima!</p>
	{:else}
		<div class="image-gallery">
			{#each galleryImages as image}
				<button
					class="gallery-item"
					onclick={() => insertImage(image)}
					title="Clicca per inserire: {image.original_filename}"
				>
					<img src={image.url} alt={image.alt_text || image.original_filename} />
					<span class="image-name">{image.original_filename}</span>
				</button>
			{/each}
		</div>
	{/if}

	{#snippet footer()}
		<Button variant="ghost" onclick={() => imageGalleryModal = false}>
			Chiudi
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

	/* Syntax Guide Styles */
	.syntax-guide {
		font-size: var(--text-sm);
	}

	.syntax-table {
		width: 100%;
		border-collapse: collapse;
	}

	.syntax-table td {
		padding: var(--space-1) var(--space-2);
		border-bottom: 1px solid var(--geko-gray-light);
	}

	.syntax-table td:first-child {
		font-family: monospace;
		white-space: nowrap;
		color: var(--geko-magenta);
	}

	.syntax-table td:last-child {
		color: var(--geko-gray);
		font-size: var(--text-xs);
	}

	.syntax-details {
		margin-top: var(--space-2);
		border-top: 1px solid var(--geko-gray-light);
		padding-top: var(--space-2);
	}

	.syntax-details summary {
		cursor: pointer;
		color: var(--geko-gold);
		font-weight: 500;
		font-size: var(--text-sm);
	}

	.syntax-example {
		background: var(--geko-dark);
		color: var(--geko-light);
		padding: var(--space-2);
		border-radius: var(--radius-sm);
		font-size: var(--text-xs);
		margin-top: var(--space-2);
		overflow-x: auto;
	}

	.help-text {
		font-size: var(--text-sm);
		color: var(--geko-gray);
		margin: 0;
	}

	/* Image Gallery Styles */
	.gallery-upload {
		margin-bottom: var(--space-4);
		text-align: center;
	}

	.upload-btn {
		display: inline-block;
		padding: var(--space-2) var(--space-4);
		background: var(--geko-gold);
		color: white;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: background var(--transition-base);
	}

	.upload-btn:hover {
		background: var(--geko-magenta);
	}

	.upload-btn input {
		display: none;
	}

	.image-gallery {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		gap: var(--space-3);
		max-height: 400px;
		overflow-y: auto;
	}

	.gallery-item {
		background: var(--geko-light);
		border: 2px solid transparent;
		border-radius: var(--radius-md);
		padding: var(--space-2);
		cursor: pointer;
		transition: all var(--transition-base);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-1);
	}

	.gallery-item:hover {
		border-color: var(--geko-gold);
		transform: scale(1.02);
	}

	.gallery-item img {
		width: 100%;
		height: 80px;
		object-fit: cover;
		border-radius: var(--radius-sm);
	}

	.gallery-item .image-name {
		font-size: var(--text-xs);
		color: var(--geko-gray);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 100%;
	}

	.no-images {
		text-align: center;
		color: var(--geko-gray);
		padding: var(--space-6);
	}
</style>
