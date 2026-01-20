<script lang="ts">
	import { goto } from '$app/navigation';
	import { ArrowLeft } from 'lucide-svelte';
	import { Button, Input, Textarea, Select, Card } from '$lib/components/ui';
	import { magazines } from '$lib/api';

	let numero = $state('');
	let mese = $state('');
	let anno = $state(new Date().getFullYear().toString());
	let editoriale = $state('');
	let editoriale_autore = $state('');
	let saving = $state(false);
	let error = $state<string | null>(null);

	const mesi = [
		'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
		'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
	];

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
				editoriale_autore
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

	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
