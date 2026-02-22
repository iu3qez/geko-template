<script lang="ts">
	import { onMount } from 'svelte';
	import { Save, RefreshCw, Plus, Trash2, Upload, Users, FileText } from 'lucide-svelte';
	import { Button, Input, Select, Card, Loading, Toast } from '$lib/components/ui';
	import { config, images } from '$lib/api';
	import type { ConfigItem, Image } from '$lib/api';

	interface TeamMember {
		foto: string;
		nominativo: string;
		nome: string;
		ruolo: string;
		ruolo2?: string;
	}

	let configItems = $state<Record<string, ConfigItem>>({});
	let editValues = $state<Record<string, string>>({});
	let teamMembri = $state<TeamMember[]>([]);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let successMessage = $state<string | null>(null);
	let availableImages = $state<Image[]>([]);
	let uploadingFor = $state<number | null>(null);

	// Config keys for general settings (exclude team/finale)
	const generalConfigOrder = [
		'ultimo_numero',
		'titolo_rivista',
		'sottotitolo_rivista',
		'sito_web',
		'email_redazione',
		'claude_model'
	];

	// Config keys for team/finale (handled separately)
	const teamFinaleKeys = [
		'team_membri',
		'link_iscrizione',
		'link_lista_distribuzione',
		'link_donazione',
		'immagine_frequenze',
		'immagine_donazione'
	];

	onMount(async () => {
		await loadConfig();
		await loadImages();
	});

	async function loadImages() {
		try {
			availableImages = await images.list();
		} catch (e) {
			console.error('Error loading images:', e);
		}
	}

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
			// Parse team members from JSON
			try {
				const teamJson = editValues['team_membri'] || '[]';
				teamMembri = JSON.parse(teamJson);
			} catch {
				teamMembri = [];
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
			// Serialize team members to JSON
			editValues['team_membri'] = JSON.stringify(teamMembri);
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
		// Reset team members
		try {
			const teamJson = configItems['team_membri']?.value || '[]';
			teamMembri = JSON.parse(teamJson);
		} catch {
			teamMembri = [];
		}
	}

	function addTeamMember() {
		teamMembri = [...teamMembri, { foto: '', nominativo: '', nome: '', ruolo: '', ruolo2: '' }];
	}

	function removeTeamMember(index: number) {
		teamMembri = teamMembri.filter((_, i) => i !== index);
	}

	function moveTeamMember(index: number, direction: 'up' | 'down') {
		const newIndex = direction === 'up' ? index - 1 : index + 1;
		if (newIndex < 0 || newIndex >= teamMembri.length) return;
		const newMembri = [...teamMembri];
		[newMembri[index], newMembri[newIndex]] = [newMembri[newIndex], newMembri[index]];
		teamMembri = newMembri;
	}

	async function handleImageUpload(event: Event, memberIndex: number) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		uploadingFor = memberIndex;
		try {
			const uploaded = await images.upload(file);
			teamMembri[memberIndex].foto = uploaded.path;
			await loadImages();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore upload immagine';
		} finally {
			uploadingFor = null;
		}
	}

	async function handleConfigImageUpload(event: Event, configKey: string) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		try {
			const uploaded = await images.upload(file);
			editValues[configKey] = uploaded.path;
			await loadImages();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore upload immagine';
		}
	}

	const hasChanges = $derived(() => {
		// Check general config
		for (const [key, item] of Object.entries(configItems)) {
			if (key === 'team_membri') continue; // Compare separately
			if (editValues[key] !== item.value) return true;
		}
		// Check team members
		const currentTeamJson = JSON.stringify(teamMembri);
		const savedTeamJson = configItems['team_membri']?.value || '[]';
		if (currentTeamJson !== savedTeamJson) return true;
		return false;
	});

	const sortedGeneralConfigKeys = $derived(
		Object.keys(configItems)
			.filter(key => !teamFinaleKeys.includes(key))
			.sort((a, b) => {
				const aIdx = generalConfigOrder.indexOf(a);
				const bIdx = generalConfigOrder.indexOf(b);
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
		<!-- General Config -->
		<Card>
			{#snippet header()}
				<h2>Impostazioni Generali</h2>
			{/snippet}
			<form onsubmit={(e) => { e.preventDefault(); handleSave(); }}>
				<div class="config-grid">
					{#each sortedGeneralConfigKeys as key}
						{@const item = configItems[key]}
						<div class="config-item">
							{#if key === 'claude_model'}
								<Select
									label={formatLabel(key)}
									hint={item.description}
									bind:value={editValues[key]}
								>
									<option value="claude-haiku-4-5-20251001">Claude Haiku 4.5 (veloce, economico)</option>
									<option value="claude-sonnet-4-6">Claude Sonnet 4.6 (bilanciato)</option>
									<option value="claude-opus-4-6">Claude Opus 4.6 (più capace)</option>
								</Select>
							{:else}
								<Input
									label={formatLabel(key)}
									hint={item.description}
									bind:value={editValues[key]}
								/>
							{/if}
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

		<!-- Team MQC -->
		<Card>
			{#snippet header()}
				<div class="section-header">
					<h2><Users size={20} /> Team MQC</h2>
					<Button variant="ghost" size="sm" onclick={addTeamMember}>
						<Plus size={16} />
						Aggiungi membro
					</Button>
				</div>
			{/snippet}

			<div class="team-section">
				<div class="config-item">
					<Input
						label="Link Iscrizione"
						hint="Link al modulo di iscrizione al club"
						bind:value={editValues['link_iscrizione']}
					/>
				</div>

				{#if teamMembri.length === 0}
					<p class="empty-message">Nessun membro del team configurato. Clicca "Aggiungi membro" per iniziare.</p>
				{:else}
					<div class="team-grid">
						{#each teamMembri as member, index}
							<div class="team-member-card">
								<div class="member-header">
									<span class="member-number">#{index + 1}</span>
									<div class="member-actions">
										<button type="button" onclick={() => moveTeamMember(index, 'up')} disabled={index === 0} title="Sposta su">
											&uarr;
										</button>
										<button type="button" onclick={() => moveTeamMember(index, 'down')} disabled={index === teamMembri.length - 1} title="Sposta giu">
											&darr;
										</button>
										<button type="button" class="delete" onclick={() => removeTeamMember(index)} title="Rimuovi">
											<Trash2 size={14} />
										</button>
									</div>
								</div>

								<div class="member-foto">
									{#if member.foto}
										<img src={member.foto.startsWith('/') ? member.foto : `/uploads/${member.foto.split('/').pop()}`} alt={member.nominativo} />
									{:else}
										<div class="foto-placeholder">
											<Users size={32} />
										</div>
									{/if}
									<label class="foto-upload">
										<input
											type="file"
											accept="image/*"
											onchange={(e) => handleImageUpload(e, index)}
											disabled={uploadingFor === index}
										/>
										{#if uploadingFor === index}
											Caricamento...
										{:else}
											<Upload size={14} /> Carica foto
										{/if}
									</label>
									{#if availableImages.length > 0}
										<select
											value={member.foto}
											onchange={(e) => { member.foto = (e.target as HTMLSelectElement).value; }}
										>
											<option value="">-- Seleziona immagine --</option>
											{#each availableImages as img}
												<option value={img.path}>{img.original_filename}</option>
											{/each}
										</select>
									{/if}
								</div>

								<div class="member-fields">
									<Input
										label="Nominativo"
										placeholder="es. IK2ABC"
										bind:value={member.nominativo}
									/>
									<Input
										label="Nome"
										placeholder="es. Mario Rossi"
										bind:value={member.nome}
									/>
									<Input
										label="Ruolo"
										placeholder="es. Presidente"
										bind:value={member.ruolo}
									/>
									<Input
										label="Ruolo 2 (opzionale)"
										placeholder="es. Fondatore"
										bind:value={member.ruolo2}
									/>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</Card>

		<!-- Pagina Finale -->
		<Card>
			{#snippet header()}
				<h2><FileText size={20} /> Pagina Finale</h2>
			{/snippet}

			<div class="finale-section">
				<div class="config-grid">
					<div class="config-item">
						<Input
							label="Link Lista Distribuzione"
							hint="Link per iscriversi alla lista di distribuzione"
							bind:value={editValues['link_lista_distribuzione']}
						/>
					</div>
					<div class="config-item">
						<Input
							label="Link Donazione"
							hint="Link per effettuare donazioni"
							bind:value={editValues['link_donazione']}
						/>
					</div>
				</div>

				<div class="images-grid">
					<div class="image-config">
						<label>Immagine Frequenze MQC</label>
						{#if editValues['immagine_frequenze']}
							<img
								src={editValues['immagine_frequenze'].startsWith('/') ? editValues['immagine_frequenze'] : `/uploads/${editValues['immagine_frequenze'].split('/').pop()}`}
								alt="Frequenze MQC"
								class="preview-image"
							/>
						{/if}
						<div class="image-controls">
							<label class="upload-btn">
								<input
									type="file"
									accept="image/*"
									onchange={(e) => handleConfigImageUpload(e, 'immagine_frequenze')}
								/>
								<Upload size={14} /> Carica
							</label>
							<select
								value={editValues['immagine_frequenze'] || ''}
								onchange={(e) => { editValues['immagine_frequenze'] = (e.target as HTMLSelectElement).value; }}
							>
								<option value="">-- Seleziona --</option>
								{#each availableImages as img}
									<option value={img.path}>{img.original_filename}</option>
								{/each}
							</select>
							{#if editValues['immagine_frequenze']}
								<Button variant="ghost" size="sm" onclick={() => editValues['immagine_frequenze'] = ''}>
									<Trash2 size={14} />
								</Button>
							{/if}
						</div>
					</div>

					<div class="image-config">
						<label>Immagine QR Donazione</label>
						{#if editValues['immagine_donazione']}
							<img
								src={editValues['immagine_donazione'].startsWith('/') ? editValues['immagine_donazione'] : `/uploads/${editValues['immagine_donazione'].split('/').pop()}`}
								alt="QR Donazione"
								class="preview-image"
							/>
						{/if}
						<div class="image-controls">
							<label class="upload-btn">
								<input
									type="file"
									accept="image/*"
									onchange={(e) => handleConfigImageUpload(e, 'immagine_donazione')}
								/>
								<Upload size={14} /> Carica
							</label>
							<select
								value={editValues['immagine_donazione'] || ''}
								onchange={(e) => { editValues['immagine_donazione'] = (e.target as HTMLSelectElement).value; }}
							>
								<option value="">-- Seleziona --</option>
								{#each availableImages as img}
									<option value={img.path}>{img.original_filename}</option>
								{/each}
							</select>
							{#if editValues['immagine_donazione']}
								<Button variant="ghost" size="sm" onclick={() => editValues['immagine_donazione'] = ''}>
									<Trash2 size={14} />
								</Button>
							{/if}
						</div>
					</div>
				</div>
			</div>
		</Card>

		<!-- Info -->
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
		max-width: 900px;
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

	.section-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
	}

	.section-header h2 {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin: 0;
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

	/* Team Section */
	.team-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.empty-message {
		color: var(--geko-gray);
		text-align: center;
		padding: var(--space-6);
	}

	.team-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: var(--space-4);
	}

	.team-member-card {
		background: var(--geko-light);
		border-radius: var(--radius-md);
		padding: var(--space-4);
		border: 1px solid var(--geko-border);
	}

	.member-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--space-3);
	}

	.member-number {
		font-weight: 600;
		color: var(--geko-magenta);
	}

	.member-actions {
		display: flex;
		gap: var(--space-1);
	}

	.member-actions button {
		background: none;
		border: 1px solid var(--geko-border);
		border-radius: var(--radius-sm);
		padding: var(--space-1) var(--space-2);
		cursor: pointer;
		font-size: var(--text-sm);
	}

	.member-actions button:hover:not(:disabled) {
		background: var(--geko-white);
	}

	.member-actions button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.member-actions button.delete:hover {
		background: var(--color-danger-light);
		color: var(--color-danger);
		border-color: var(--color-danger);
	}

	.member-foto {
		text-align: center;
		margin-bottom: var(--space-4);
	}

	.member-foto img {
		width: 100px;
		height: 100px;
		object-fit: cover;
		border-radius: var(--radius-md);
		margin-bottom: var(--space-2);
	}

	.foto-placeholder {
		width: 100px;
		height: 100px;
		background: var(--geko-border);
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto var(--space-2);
		color: var(--geko-gray);
	}

	.foto-upload {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		font-size: var(--text-sm);
		color: var(--geko-magenta);
		cursor: pointer;
		margin-bottom: var(--space-2);
	}

	.foto-upload input {
		display: none;
	}

	.foto-upload:hover {
		text-decoration: underline;
	}

	.member-foto select {
		width: 100%;
		padding: var(--space-2);
		border: 1px solid var(--geko-border);
		border-radius: var(--radius-sm);
		font-size: var(--text-sm);
	}

	.member-fields {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	/* Finale Section */
	.finale-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.images-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: var(--space-6);
	}

	.image-config {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.image-config > label {
		font-weight: 500;
		font-size: var(--text-sm);
	}

	.preview-image {
		max-width: 200px;
		max-height: 150px;
		object-fit: contain;
		border-radius: var(--radius-md);
		border: 1px solid var(--geko-border);
	}

	.image-controls {
		display: flex;
		gap: var(--space-2);
		align-items: center;
		flex-wrap: wrap;
	}

	.upload-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-2) var(--space-3);
		background: var(--geko-light);
		border: 1px solid var(--geko-border);
		border-radius: var(--radius-sm);
		font-size: var(--text-sm);
		cursor: pointer;
	}

	.upload-btn:hover {
		background: var(--geko-white);
	}

	.upload-btn input {
		display: none;
	}

	.image-controls select {
		flex: 1;
		min-width: 120px;
		padding: var(--space-2);
		border: 1px solid var(--geko-border);
		border-radius: var(--radius-sm);
		font-size: var(--text-sm);
	}

	/* Info List */
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

		.team-grid {
			grid-template-columns: 1fr;
		}

		.images-grid {
			grid-template-columns: 1fr;
		}
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
