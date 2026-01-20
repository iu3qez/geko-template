<script lang="ts">
	import { goto } from '$app/navigation';
	import { ArrowLeft } from 'lucide-svelte';
	import { Button, Input, Textarea, Card } from '$lib/components/ui';
	import { articles } from '$lib/api';

	let titolo = $state('');
	let sottotitolo = $state('');
	let autore = $state('');
	let nome_autore = $state('');
	let contenuto_md = $state('');
	let saving = $state(false);
	let error = $state<string | null>(null);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = null;

		if (!titolo.trim()) {
			error = 'Il titolo è obbligatorio';
			return;
		}

		saving = true;
		try {
			const article = await articles.create({
				titolo: titolo.trim(),
				sottotitolo,
				autore,
				nome_autore,
				contenuto_md
			});
			goto(`/articles/${article.id}`);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore durante il salvataggio';
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Nuovo Articolo - GEKO Radio Magazine</title>
</svelte:head>

<div class="new-article-page">
	<header class="page-header">
		<Button href="/articles" variant="ghost" size="sm">
			<ArrowLeft size={18} />
			Torna agli articoli
		</Button>
		<h1>Nuovo Articolo</h1>
	</header>

	<Card>
		<form onsubmit={handleSubmit}>
			{#if error}
				<div class="error-message">
					{error}
				</div>
			{/if}

			<div class="form-section">
				<Input
					label="Titolo *"
					placeholder="Titolo dell'articolo"
					bind:value={titolo}
					required
				/>

				<Input
					label="Sottotitolo"
					placeholder="Sottotitolo opzionale"
					bind:value={sottotitolo}
				/>
			</div>

			<div class="form-grid">
				<Input
					label="Autore (Nominativo)"
					placeholder="es. IK2XYZ"
					bind:value={autore}
				/>

				<Input
					label="Nome Autore"
					placeholder="es. Marco Rossi"
					bind:value={nome_autore}
				/>
			</div>

			<div class="form-section">
				<Textarea
					label="Contenuto (Markdown)"
					placeholder="Scrivi il contenuto dell'articolo in formato Markdown..."
					bind:value={contenuto_md}
					rows={20}
				/>
				<p class="hint">
					Puoi usare la sintassi Markdown per formattare il testo.
					Dopo aver salvato potrai modificare l'articolo con l'editor avanzato.
				</p>
			</div>

			<div class="form-actions">
				<Button href="/articles" variant="ghost">
					Annulla
				</Button>
				<Button type="submit" loading={saving}>
					Crea Articolo
				</Button>
			</div>
		</form>
	</Card>
</div>

<style>
	.new-article-page {
		max-width: 900px;
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

	.form-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--space-4);
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
		padding-top: var(--space-4);
		border-top: 1px solid var(--geko-gray-light);
	}

	.hint {
		font-size: var(--text-sm);
		color: var(--geko-gray);
		margin: 0;
	}

	.error-message {
		background: var(--color-danger-light);
		color: var(--color-danger);
		padding: var(--space-4);
		border-radius: var(--radius-md);
	}

	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
