<script lang="ts">
	import { goto } from '$app/navigation';
	import { ArrowLeft, Image as ImageIcon } from 'lucide-svelte';
	import { Button, Input, Textarea, Select, Card, Modal, Loading } from '$lib/components/ui';
	import { magazines, images as imagesApi } from '$lib/api';
	import type { Image } from '$lib/api';

	let numero = $state('');
	let mese = $state('');
	let anno = $state(new Date().getFullYear().toString());
	let editoriale = $state('');
	let editoriale_autore = $state('');
	let copertina_id = $state<number | null>(null);
	let saving = $state(false);
	let error = $state<string | null>(null);

	// Cover image selection
	let coverModal = $state(false);
	let availableImages = $state<Image[]>([]);
	let loadingImages = $state(false);

	const mesi = [
		'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
		'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
	];

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
		copertina_id = image?.id ?? null;
		coverModal = false;
	}

	const selectedCoverImage = $derived(
		availableImages.find(img => img.id === copertina_id)
	);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = null;

		if (!numero.trim() || !mese || !anno) {
			error = 'Compila tutti i campi obbligatori';
			return;
		}

		saving = true;
		try {
			const magazine = await magazines.create({
				numero: numero.trim(),
				mese,
				anno,
				editoriale,
				editoriale_autore,
				copertina_id
			});
			goto(`/magazines/${magazine.id}`);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante il salvataggio';
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Nuovo Numero - GEKO Radio Magazine</title>
</svelte:head>

<div class="new-magazine-page">
	<header class="page-header">
		<Button href="/magazines" variant="ghost" size="sm">
			<ArrowLeft size={18} />
			Torna ai numeri
		</Button>
		<h1>Nuovo Numero GEKO</h1>
	</header>

	<Card>
		<form onsubmit={handleSubmit}>
			{#if error}
				<div class="error-message">
					{error}
				</div>
			{/if}

			<div class="form-grid">
				<Input
					label="Numero *"
					placeholder="es. 68"
					bind:value={numero}
					required
				/>

				<Select label="Mese *" bind:value={mese} required>
					<option value="">Seleziona mese</option>
					{#each mesi as m}
						<option value={m}>{m}</option>
					{/each}
				</Select>

				<Input
					label="Anno *"
					type="number"
					placeholder="2024"
					bind:value={anno}
					required
				/>
			</div>

			<div class="form-section">
				<Textarea
					label="Editoriale"
					placeholder="Testo dell'editoriale..."
					bind:value={editoriale}
					rows={6}
				/>

				<Input
					label="Autore Editoriale"
					placeholder="es. IK2XYZ Marco"
					bind:value={editoriale_autore}
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
								<Button type="button" variant="ghost" size="sm" onclick={() => copertina_id = null}>
									Rimuovi
								</Button>
							{/if}
						</div>
					</div>
				</div>
			</div>

			<div class="form-actions">
				<Button href="/magazines" variant="ghost">
					Annulla
				</Button>
				<Button type="submit" loading={saving}>
					Crea Numero
				</Button>
			</div>
		</form>
	</Card>
</div>

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
					class:selected={copertina_id === image.id}
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
	.new-magazine-page {
		max-width: 720px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: var(--space-6);
	}

	.page-header h1 {
		margin-top: var(--space-4);
	}

	form {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-4);
	}

	.form-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
		padding-top: var(--space-4);
		border-top: 1px solid var(--geko-gray-light);
	}

	.error-message {
		background: var(--color-danger-light);
		color: var(--color-danger);
		padding: var(--space-4);
		border-radius: var(--radius-md);
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

	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
