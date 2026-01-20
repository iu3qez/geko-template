<script lang="ts">
	import { onMount } from 'svelte';
	import { BookOpen, FileText, Image, Settings, Plus, Download, Sparkles } from 'lucide-svelte';
	import { Card, Loading, Badge } from '$lib/components/ui';
	import { magazines, articles, images } from '$lib/api';
	import type { Magazine, Article, Image as ImageType } from '$lib/api';

	let magazinesList = $state<Magazine[]>([]);
	let articlesList = $state<Article[]>([]);
	let imagesList = $state<ImageType[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			const [mags, arts, imgs] = await Promise.all([
				magazines.list(),
				articles.list(),
				images.list()
			]);
			magazinesList = mags;
			articlesList = arts;
			imagesList = imgs;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Errore nel caricamento';
		} finally {
			loading = false;
		}
	});

	const stats = $derived([
		{ label: 'Numeri', value: magazinesList.length, icon: BookOpen, href: '/magazines' },
		{ label: 'Articoli', value: articlesList.length, icon: FileText, href: '/articles' },
		{ label: 'Immagini', value: imagesList.length, icon: Image, href: '/media' }
	]);

	const latestMagazine = $derived(magazinesList[0]);
	const recentArticles = $derived(articlesList.slice(0, 5));

	const quickActions = [
		{ label: 'Nuovo Articolo', icon: Plus, href: '/articles/new', color: 'gold' },
		{ label: 'Nuovo Numero', icon: BookOpen, href: '/magazines/new', color: 'magenta' },
		{ label: 'Carica Immagini', icon: Image, href: '/media', color: 'gold' },
		{ label: 'Configurazione', icon: Settings, href: '/config', color: 'magenta' }
	];
</script>

<svelte:head>
	<title>GEKO Radio Magazine - Dashboard</title>
</svelte:head>

<div class="home">
	<header class="hero">
		<h1>GEKO Radio Magazine</h1>
		<p>Gestione editoriale per il Mountain QRP Club</p>
	</header>

	{#if loading}
		<Loading text="Caricamento..." />
	{:else if error}
		<div class="error-message">
			<p>{error}</p>
		</div>
	{:else}
		<section class="stats-section">
			<div class="stats-grid">
				{#each stats as stat}
					<a href={stat.href} class="stat-card">
						<div class="stat-icon">
							<stat.icon size={24} />
						</div>
						<div class="stat-content">
							<span class="stat-value">{stat.value}</span>
							<span class="stat-label">{stat.label}</span>
						</div>
					</a>
				{/each}
			</div>
		</section>

		<div class="content-grid">
			<section class="quick-actions">
				<h2>Azioni Rapide</h2>
				<div class="actions-grid">
					{#each quickActions as action}
						<a href={action.href} class="action-card action-{action.color}">
							<action.icon size={24} />
							<span>{action.label}</span>
						</a>
					{/each}
				</div>
			</section>

			<section class="latest-magazine">
				<h2>Ultimo Numero</h2>
				{#if latestMagazine}
					<Card href="/magazines/{latestMagazine.id}">
						<div class="magazine-preview">
							<div class="magazine-number">
								<span class="number">#{latestMagazine.numero}</span>
								<Badge variant={latestMagazine.stato === 'pubblicato' ? 'success' : 'warning'}>
									{latestMagazine.stato}
								</Badge>
							</div>
							<p class="magazine-date">{latestMagazine.mese} {latestMagazine.anno}</p>
							<p class="magazine-articles">{latestMagazine.article_count} articoli</p>
							{#if latestMagazine.stato === 'pubblicato'}
								<a
									href="/api/magazines/{latestMagazine.id}/pdf"
									class="download-btn"
									onclick={(e) => e.stopPropagation()}
								>
									<Download size={16} />
									Scarica PDF
								</a>
							{/if}
						</div>
					</Card>
				{:else}
					<Card>
						<p class="no-content">Nessun numero creato</p>
						<a href="/magazines/new" class="btn btn-primary">Crea il primo numero</a>
					</Card>
				{/if}
			</section>

			<section class="recent-articles">
				<div class="section-header">
					<h2>Articoli Recenti</h2>
					<a href="/articles" class="view-all">Vedi tutti</a>
				</div>
				{#if recentArticles.length > 0}
					<ul class="articles-list">
						{#each recentArticles as article}
							<li>
								<a href="/articles/{article.id}" class="article-item">
									<div class="article-info">
										<strong>{article.titolo}</strong>
										{#if article.autore}
											<span class="article-author">{article.autore}</span>
										{/if}
									</div>
									{#if article.sommario_llm}
										<Sparkles size={14} class="has-summary" />
									{/if}
								</a>
							</li>
						{/each}
					</ul>
				{:else}
					<p class="no-content">Nessun articolo</p>
				{/if}
			</section>
		</div>
	{/if}
</div>

<style>
	.home {
		animation: fadeIn var(--transition-base);
	}

	.hero {
		text-align: center;
		padding: var(--space-8) 0;
		margin-bottom: var(--space-8);
		border-bottom: 2px solid var(--geko-gold);
	}

	.hero h1 {
		font-size: var(--text-4xl);
		color: var(--geko-gold);
		margin-bottom: var(--space-2);
	}

	.hero p {
		color: var(--geko-gray);
		font-size: var(--text-lg);
		margin: 0;
	}

	.stats-section {
		margin-bottom: var(--space-8);
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-4);
	}

	.stat-card {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		padding: var(--space-5);
		background: var(--geko-white);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md);
		text-decoration: none;
		color: inherit;
		transition: all var(--transition-fast);
	}

	.stat-card:hover {
		transform: translateY(-2px);
		box-shadow: var(--shadow-lg);
		text-decoration: none;
	}

	.stat-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 48px;
		height: 48px;
		background: var(--geko-gold);
		color: var(--geko-white);
		border-radius: var(--radius-md);
	}

	.stat-content {
		display: flex;
		flex-direction: column;
	}

	.stat-value {
		font-family: var(--font-display);
		font-size: var(--text-2xl);
		font-weight: 700;
		color: var(--geko-dark);
	}

	.stat-label {
		font-size: var(--text-sm);
		color: var(--geko-gray);
	}

	.content-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--space-6);
	}

	.quick-actions {
		grid-column: 1 / -1;
	}

	.quick-actions h2,
	.latest-magazine h2,
	.recent-articles h2 {
		font-size: var(--text-xl);
		margin-bottom: var(--space-4);
	}

	.actions-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--space-4);
	}

	.action-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-3);
		padding: var(--space-6);
		background: var(--geko-white);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md);
		text-decoration: none;
		font-family: var(--font-display);
		font-weight: 500;
		transition: all var(--transition-fast);
	}

	.action-card:hover {
		transform: translateY(-2px);
		box-shadow: var(--shadow-lg);
		text-decoration: none;
	}

	.action-gold {
		color: var(--geko-gold);
	}

	.action-gold:hover {
		background: var(--geko-gold);
		color: var(--geko-white);
	}

	.action-magenta {
		color: var(--geko-magenta);
	}

	.action-magenta:hover {
		background: var(--geko-magenta);
		color: var(--geko-white);
	}

	.magazine-preview {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.magazine-number {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.magazine-number .number {
		font-family: var(--font-display);
		font-size: var(--text-2xl);
		font-weight: 700;
		color: var(--geko-gold);
	}

	.magazine-date {
		color: var(--geko-gray);
		margin: 0;
	}

	.magazine-articles {
		font-size: var(--text-sm);
		color: var(--geko-gray);
		margin: 0;
	}

	.download-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-4);
		background: var(--geko-magenta);
		color: var(--geko-white);
		border-radius: var(--radius-md);
		font-size: var(--text-sm);
		text-decoration: none;
		width: fit-content;
		margin-top: var(--space-2);
	}

	.download-btn:hover {
		background: var(--geko-magenta-dark);
		text-decoration: none;
	}

	.section-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--space-4);
	}

	.section-header h2 {
		margin: 0;
	}

	.view-all {
		font-size: var(--text-sm);
		color: var(--geko-magenta);
	}

	.articles-list {
		list-style: none;
		padding: 0;
		margin: 0;
		background: var(--geko-white);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md);
		overflow: hidden;
	}

	.articles-list li {
		margin: 0;
	}

	.article-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-4);
		text-decoration: none;
		color: inherit;
		border-bottom: 1px solid var(--geko-gray-light);
		transition: background var(--transition-fast);
	}

	.article-item:hover {
		background: var(--geko-light);
		text-decoration: none;
	}

	.articles-list li:last-child .article-item {
		border-bottom: none;
	}

	.article-info {
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.article-info strong {
		font-size: var(--text-sm);
	}

	.article-author {
		font-size: var(--text-xs);
		color: var(--geko-gray);
	}

	.article-item :global(.has-summary) {
		color: var(--geko-magenta);
	}

	.no-content {
		color: var(--geko-gray);
		font-style: italic;
		padding: var(--space-4);
		text-align: center;
	}

	.error-message {
		background: var(--color-danger-light);
		color: var(--color-danger);
		padding: var(--space-4);
		border-radius: var(--radius-md);
		text-align: center;
	}

	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}

		.content-grid {
			grid-template-columns: 1fr;
		}

		.actions-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
