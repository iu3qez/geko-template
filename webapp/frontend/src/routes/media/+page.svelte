<script lang="ts">
	import { onMount } from 'svelte';
	import { Upload, Trash2, Image as ImageIcon, Copy, Check, Filter } from 'lucide-svelte';
	import { Button, Card, Loading, EmptyState, Modal, Input } from '$lib/components/ui';
	import { images } from '$lib/api';
	import type { Image } from '$lib/api';

	let imagesList = $state<Image[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Upload state
	let uploading = $state(false);
	let uploadProgress = $state<string | null>(null);
	let dragOver = $state(false);

	// Filter state
	let filterPublished = $state<boolean | null>(null);

	// Delete modal
	let deleteModal = $state(false);
	let imageToDelete = $state<Image | null>(null);
	let deleting = $state(false);

	// Selected image for details
	let selectedImage = $state<Image | null>(null);
	let editingAltText = $state(false);
	let newAltText = $state('');
	let savingAltText = $state(false);

	// Copy feedback
	let copiedId = $state<number | null>(null);

	onMount(async () => {
		await loadImages();
	});

	async function loadImages() {
		loading = true;
		error = null;
		try {
			const params: { published?: boolean } = {};
			if (filterPublished !== null) {
				params.published = filterPublished;
			}
			imagesList = await images.list(params);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore nel caricamento';
		} finally {
			loading = false;
		}
	}

	async function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		if (input.files?.length) {
			await uploadFiles(Array.from(input.files));
		}
	}

	async function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;

		if (e.dataTransfer?.files.length) {
			await uploadFiles(Array.from(e.dataTransfer.files));
		}
	}

	async function uploadFiles(files: File[]) {
		uploading = true;
		uploadProgress = `Caricamento di ${files.length} file...`;
		error = null;

		try {
			const result = await images.uploadMultiple(files);
			imagesList = [...result.images, ...imagesList];

			if (result.errors?.length > 0) {
				error = `${result.errors.length} file non caricati`;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante il caricamento';
		} finally {
			uploading = false;
			uploadProgress = null;
		}
	}

	function confirmDelete(image: Image) {
		imageToDelete = image;
		deleteModal = true;
	}

	async function handleDelete() {
		if (!imageToDelete) return;

		deleting = true;
		try {
			await images.delete(imageToDelete.id);
			imagesList = imagesList.filter(img => img.id !== imageToDelete!.id);
			if (selectedImage?.id === imageToDelete.id) {
				selectedImage = null;
			}
			deleteModal = false;
			imageToDelete = null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante la cancellazione';
		} finally {
			deleting = false;
		}
	}

	function selectImage(image: Image) {
		selectedImage = image;
		newAltText = image.alt_text;
		editingAltText = false;
	}

	async function saveAltText() {
		if (!selectedImage) return;

		savingAltText = true;
		try {
			const updated = await images.update(selectedImage.id, { alt_text: newAltText });
			// Update in list
			const idx = imagesList.findIndex(img => img.id === selectedImage!.id);
			if (idx !== -1) {
				imagesList[idx] = updated;
			}
			selectedImage = updated;
			editingAltText = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore salvataggio';
		} finally {
			savingAltText = false;
		}
	}

	function copyMarkdown(image: Image) {
		const markdown = `![${image.alt_text || image.original_filename}](${image.url})`;
		navigator.clipboard.writeText(markdown);
		copiedId = image.id;
		setTimeout(() => {
			if (copiedId === image.id) copiedId = null;
		}, 2000);
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	$effect(() => {
		loadImages();
	});
</script>

<svelte:head>
	<title>Media Library - GEKO Radio Magazine</title>
</svelte:head>

<div class="media-page">
	<header class="page-header">
		<div>
			<h1>Media Library</h1>
			<p>Gestione immagini e file multimediali</p>
		</div>
	</header>

	<div
		class="upload-area"
		class:drag-over={dragOver}
		ondrop={handleDrop}
		ondragover={handleDragOver}
		ondragleave={handleDragLeave}
		role="button"
		tabindex="0"
	>
		<Upload size={48} />
		<p>Trascina le immagini qui o</p>
		<label class="upload-btn">
			<input
				type="file"
				accept="image/*"
				multiple
				onchange={handleFileSelect}
				disabled={uploading}
			/>
			Seleziona file
		</label>
		{#if uploadProgress}
			<p class="upload-progress">{uploadProgress}</p>
		{/if}
	</div>

	<div class="filter-bar">
		<span class="filter-label">
			<Filter size={16} />
			Filtra:
		</span>
		<button
			class="filter-btn"
			class:active={filterPublished === null}
			onclick={() => filterPublished = null}
		>
			Tutte
		</button>
		<button
			class="filter-btn"
			class:active={filterPublished === true}
			onclick={() => filterPublished = true}
		>
			Pubblicate
		</button>
		<button
			class="filter-btn"
			class:active={filterPublished === false}
			onclick={() => filterPublished = false}
		>
			Non pubblicate
		</button>
	</div>

	{#if error}
		<div class="error-message">
			<p>{error}</p>
			<Button onclick={() => error = null} variant="ghost" size="sm">Chiudi</Button>
		</div>
	{/if}

	<div class="content-layout">
		<div class="images-section">
			{#if loading}
				<Loading text="Caricamento immagini..." />
			{:else if imagesList.length === 0}
				<EmptyState
					title="Nessuna immagine"
					description="Carica la prima immagine trascinandola nell'area sopra"
					icon={ImageIcon}
				/>
			{:else}
				<div class="images-grid">
					{#each imagesList as image}
						<button
							class="image-card"
							class:selected={selectedImage?.id === image.id}
							onclick={() => selectImage(image)}
						>
							<div class="image-thumbnail">
								<img src={image.url} alt={image.alt_text || image.original_filename} loading="lazy" />
							</div>
							<div class="image-info">
								<span class="image-name">{image.original_filename}</span>
							</div>
							<div class="image-actions">
								<button
									class="action-btn"
									onclick|stopPropagation={() => copyMarkdown(image)}
									title="Copia Markdown"
								>
									{#if copiedId === image.id}
										<Check size={14} />
									{:else}
										<Copy size={14} />
									{/if}
								</button>
								<button
									class="action-btn danger"
									onclick|stopPropagation={() => confirmDelete(image)}
									title="Elimina"
								>
									<Trash2 size={14} />
								</button>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>

		{#if selectedImage}
			<aside class="image-detail">
				<Card>
					{#snippet header()}
						<h3>Dettagli Immagine</h3>
					{/snippet}

					<div class="detail-preview">
						<img src={selectedImage.url} alt={selectedImage.alt_text || selectedImage.original_filename} />
					</div>

					<dl class="detail-info">
						<div>
							<dt>Nome file</dt>
							<dd>{selectedImage.original_filename}</dd>
						</div>
						<div>
							<dt>URL</dt>
							<dd class="url-value">{selectedImage.url}</dd>
						</div>
						<div>
							<dt>Testo alternativo</dt>
							{#if editingAltText}
								<dd>
									<Input
										bind:value={newAltText}
										placeholder="Descrizione immagine"
									/>
									<div class="alt-actions">
										<Button size="sm" onclick={saveAltText} loading={savingAltText}>
											Salva
										</Button>
										<Button size="sm" variant="ghost" onclick={() => editingAltText = false}>
											Annulla
										</Button>
									</div>
								</dd>
							{:else}
								<dd>
									{selectedImage.alt_text || 'Non impostato'}
									<button class="edit-link" onclick={() => editingAltText = true}>
										Modifica
									</button>
								</dd>
							{/if}
						</div>
						<div>
							<dt>Caricata il</dt>
							<dd>{new Date(selectedImage.uploaded_at).toLocaleDateString('it-IT')}</dd>
						</div>
					</dl>

					<div class="detail-actions">
						<Button onclick={() => copyMarkdown(selectedImage!)} variant="outline">
							<Copy size={16} />
							Copia Markdown
						</Button>
						<Button onclick={() => confirmDelete(selectedImage!)} variant="danger">
							<Trash2 size={16} />
							Elimina
						</Button>
					</div>
				</Card>
			</aside>
		{/if}
	</div>
</div>

<Modal bind:open={deleteModal} title="Conferma Eliminazione" size="sm">
	<p>
		Sei sicuro di voler eliminare <strong>{imageToDelete?.original_filename}</strong>?
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
	.media-page {
		animation: fadeIn var(--transition-base);
	}

	.page-header {
		margin-bottom: var(--space-6);
	}

	.page-header h1 {
		margin-bottom: var(--space-2);
	}

	.page-header p {
		color: var(--geko-gray);
		margin: 0;
	}

	.upload-area {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-3);
		padding: var(--space-10);
		background: var(--geko-white);
		border: 2px dashed var(--geko-gray-light);
		border-radius: var(--radius-lg);
		text-align: center;
		color: var(--geko-gray);
		transition: all var(--transition-fast);
		margin-bottom: var(--space-6);
	}

	.upload-area.drag-over {
		border-color: var(--geko-gold);
		background: rgba(196, 163, 90, 0.1);
		color: var(--geko-gold);
	}

	.upload-area p {
		margin: 0;
	}

	.upload-btn {
		display: inline-flex;
		padding: var(--space-3) var(--space-6);
		background: var(--geko-gold);
		color: var(--geko-white);
		border-radius: var(--radius-md);
		font-family: var(--font-display);
		font-weight: 500;
		cursor: pointer;
		transition: background var(--transition-fast);
	}

	.upload-btn:hover {
		background: var(--geko-gold-dark);
	}

	.upload-btn input {
		display: none;
	}

	.upload-progress {
		color: var(--geko-magenta);
		font-size: var(--text-sm);
	}

	.filter-bar {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		margin-bottom: var(--space-6);
	}

	.filter-label {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		color: var(--geko-gray);
		font-size: var(--text-sm);
	}

	.filter-btn {
		padding: var(--space-2) var(--space-4);
		background: var(--geko-white);
		border: 1px solid var(--geko-gray-light);
		border-radius: var(--radius-md);
		font-size: var(--text-sm);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.filter-btn:hover {
		border-color: var(--geko-gold);
	}

	.filter-btn.active {
		background: var(--geko-gold);
		color: var(--geko-white);
		border-color: var(--geko-gold);
	}

	.content-layout {
		display: grid;
		grid-template-columns: 1fr 320px;
		gap: var(--space-6);
	}

	.images-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: var(--space-4);
	}

	.image-card {
		background: var(--geko-white);
		border: 2px solid transparent;
		border-radius: var(--radius-md);
		overflow: hidden;
		cursor: pointer;
		transition: all var(--transition-fast);
		text-align: left;
	}

	.image-card:hover {
		box-shadow: var(--shadow-md);
	}

	.image-card.selected {
		border-color: var(--geko-gold);
	}

	.image-thumbnail {
		aspect-ratio: 1;
		overflow: hidden;
		background: var(--geko-light);
	}

	.image-thumbnail img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.image-info {
		padding: var(--space-2) var(--space-3);
	}

	.image-name {
		font-size: var(--text-xs);
		color: var(--geko-dark);
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.image-actions {
		display: flex;
		gap: var(--space-1);
		padding: var(--space-2) var(--space-3);
		border-top: 1px solid var(--geko-gray-light);
	}

	.action-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-2);
		background: none;
		border: none;
		color: var(--geko-gray);
		border-radius: var(--radius-sm);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.action-btn:hover {
		background: var(--geko-light);
		color: var(--geko-gold);
	}

	.action-btn.danger:hover {
		background: var(--color-danger-light);
		color: var(--color-danger);
	}

	.image-detail h3 {
		font-size: var(--text-base);
		margin: 0;
	}

	.detail-preview {
		margin-bottom: var(--space-4);
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	.detail-preview img {
		width: 100%;
		height: auto;
	}

	.detail-info {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		margin-bottom: var(--space-4);
	}

	.detail-info dt {
		font-size: var(--text-xs);
		color: var(--geko-gray);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.detail-info dd {
		margin: 0;
		font-size: var(--text-sm);
	}

	.url-value {
		word-break: break-all;
		font-family: var(--font-mono);
		font-size: var(--text-xs);
		background: var(--geko-light);
		padding: var(--space-2);
		border-radius: var(--radius-sm);
	}

	.edit-link {
		display: inline;
		background: none;
		border: none;
		color: var(--geko-magenta);
		font-size: var(--text-sm);
		cursor: pointer;
		padding: 0;
		margin-left: var(--space-2);
	}

	.edit-link:hover {
		text-decoration: underline;
	}

	.alt-actions {
		display: flex;
		gap: var(--space-2);
		margin-top: var(--space-2);
	}

	.detail-actions {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
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

	.warning-text {
		color: var(--color-danger);
		font-size: var(--text-sm);
	}

	@media (max-width: 900px) {
		.content-layout {
			grid-template-columns: 1fr;
		}

		.image-detail {
			position: fixed;
			bottom: 0;
			left: 0;
			right: 0;
			z-index: 50;
			max-height: 50vh;
			overflow-y: auto;
			box-shadow: var(--shadow-xl);
		}
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
