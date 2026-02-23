<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { BookOpen, FileText, Image, Settings, Home, Menu, X } from 'lucide-svelte';

	let { children } = $props();

	let mobileMenuOpen = $state(false);

	const navItems = [
		{ href: '/', label: 'Home', icon: Home },
		{ href: '/magazines', label: 'Numeri', icon: BookOpen },
		{ href: '/articles', label: 'Articoli', icon: FileText },
		{ href: '/media', label: 'Media', icon: Image },
		{ href: '/config', label: 'Config', icon: Settings }
	];

	function isActive(href: string): boolean {
		if (href === '/') {
			return $page.url.pathname === '/';
		}
		return $page.url.pathname.startsWith(href);
	}

	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
	}

	function closeMobileMenu() {
		mobileMenuOpen = false;
	}
</script>

<div class="app-layout">
	<header class="header">
		<div class="header-content">
			<a href="/" class="logo">
				<span class="logo-text">GEKO</span>
				<span class="logo-subtitle">Radio Magazine</span>
			</a>

			<nav class="nav-desktop">
				{#each navItems as item}
					<a
						href={item.href}
						class="nav-link"
						class:active={isActive(item.href)}
					>
						<item.icon size={18} />
						<span>{item.label}</span>
					</a>
				{/each}
			</nav>

			<button class="mobile-menu-btn" onclick={toggleMobileMenu} aria-label="Menu">
				{#if mobileMenuOpen}
					<X size={24} />
				{:else}
					<Menu size={24} />
				{/if}
			</button>
		</div>
	</header>

	{#if mobileMenuOpen}
		<nav class="nav-mobile">
			{#each navItems as item}
				<a
					href={item.href}
					class="nav-link-mobile"
					class:active={isActive(item.href)}
					onclick={closeMobileMenu}
				>
					<item.icon size={20} />
					<span>{item.label}</span>
				</a>
			{/each}
		</nav>
	{/if}

	<main class="main-content">
		{@render children()}
	</main>

	<footer class="footer">
		<div class="footer-content">
			<p>GEKO Radio Magazine - Mountain QRP Club</p>
			<p class="footer-links">
				<a href="https://www.mountainqrp.it" target="_blank" rel="noopener">mountainqrp.it</a>
			</p>
		</div>
	</footer>
</div>

<style>
	.app-layout {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	.header {
		position: sticky;
		top: 0;
		z-index: 100;
		background-color: var(--geko-dark);
		color: var(--geko-white);
		height: var(--header-height);
		box-shadow: var(--shadow-md);
	}

	.header-content {
		max-width: var(--max-width);
		margin: 0 auto;
		padding: 0 var(--space-4);
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.logo {
		display: flex;
		flex-direction: column;
		text-decoration: none;
		color: var(--geko-white);
	}

	.logo:hover {
		text-decoration: none;
	}

	.logo-text {
		font-family: var(--font-display);
		font-size: var(--text-xl);
		font-weight: 700;
		color: var(--geko-gold);
		letter-spacing: 0.1em;
	}

	.logo-subtitle {
		font-size: var(--text-xs);
		color: var(--geko-gray-light);
		letter-spacing: 0.05em;
	}

	.nav-desktop {
		display: flex;
		gap: var(--space-2);
	}

	.nav-link {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-4);
		color: var(--geko-gray-light);
		text-decoration: none;
		font-family: var(--font-display);
		font-size: var(--text-sm);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
	}

	.nav-link:hover {
		color: var(--geko-white);
		background-color: rgba(255, 255, 255, 0.1);
		text-decoration: none;
	}

	.nav-link.active {
		color: var(--geko-gold);
		background-color: rgba(196, 163, 90, 0.15);
	}

	.mobile-menu-btn {
		display: none;
		background: none;
		border: none;
		color: var(--geko-white);
		cursor: pointer;
		padding: var(--space-2);
	}

	.nav-mobile {
		display: none;
		background-color: var(--geko-dark-light);
		padding: var(--space-4);
	}

	.nav-link-mobile {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-3) var(--space-4);
		color: var(--geko-gray-light);
		text-decoration: none;
		font-family: var(--font-display);
		font-size: var(--text-base);
		border-radius: var(--radius-md);
	}

	.nav-link-mobile:hover,
	.nav-link-mobile.active {
		color: var(--geko-gold);
		background-color: rgba(196, 163, 90, 0.15);
		text-decoration: none;
	}

	@media (max-width: 768px) {
		.nav-desktop {
			display: none;
		}

		.mobile-menu-btn {
			display: block;
		}

		.nav-mobile {
			display: flex;
			flex-direction: column;
			gap: var(--space-2);
		}
	}

	.main-content {
		flex: 1;
		padding: var(--space-6) var(--space-4);
		max-width: var(--max-width);
		margin: 0 auto;
		width: 100%;
	}

	.footer {
		background-color: var(--geko-dark);
		color: var(--geko-gray-light);
		padding: var(--space-6) var(--space-4);
		margin-top: auto;
	}

	.footer-content {
		max-width: var(--max-width);
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: var(--text-sm);
	}

	.footer-links a {
		color: var(--geko-gold);
	}

	@media (max-width: 768px) {
		.footer-content {
			flex-direction: column;
			gap: var(--space-2);
			text-align: center;
		}
	}
</style>
