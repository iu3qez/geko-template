<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Link from '@tiptap/extension-link';
	import Image from '@tiptap/extension-image';
	import Placeholder from '@tiptap/extension-placeholder';
	import {
		Bold, Italic, Strikethrough, Code, List, ListOrdered,
		Quote, Minus, Link as LinkIcon, Image as ImageIcon,
		Heading1, Heading2, Heading3, Undo, Redo, Pilcrow
	} from 'lucide-svelte';

	interface Props {
		value?: string;
		placeholder?: string;
		onchange?: (content: string) => void;
		label?: string;
	}

	let {
		value = $bindable(''),
		placeholder = 'Scrivi il contenuto...',
		onchange,
		label
	}: Props = $props();

	let element: HTMLDivElement;
	let editor: Editor | null = $state(null);

	onMount(() => {
		editor = new Editor({
			element,
			extensions: [
				StarterKit.configure({
					heading: {
						levels: [1, 2, 3]
					}
				}),
				Link.configure({
					openOnClick: false,
					HTMLAttributes: {
						class: 'editor-link'
					}
				}),
				Image.configure({
					HTMLAttributes: {
						class: 'editor-image'
					}
				}),
				Placeholder.configure({
					placeholder
				})
			],
			content: markdownToHtml(value),
			onUpdate: ({ editor }) => {
				const html = editor.getHTML();
				const md = htmlToMarkdown(html);
				value = md;
				onchange?.(md);
			},
			editorProps: {
				attributes: {
					class: 'prose-editor'
				}
			}
		});
	});

	onDestroy(() => {
		editor?.destroy();
	});

	// Simple markdown to HTML conversion (for initial load)
	function markdownToHtml(md: string): string {
		if (!md) return '';

		return md
			// Headers
			.replace(/^### (.*$)/gim, '<h3>$1</h3>')
			.replace(/^## (.*$)/gim, '<h2>$1</h2>')
			.replace(/^# (.*$)/gim, '<h1>$1</h1>')
			// Bold
			.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
			// Italic
			.replace(/\*(.*?)\*/g, '<em>$1</em>')
			// Strikethrough
			.replace(/~~(.*?)~~/g, '<s>$1</s>')
			// Code
			.replace(/`([^`]+)`/g, '<code>$1</code>')
			// Links
			.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
			// Images
			.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')
			// Blockquotes
			.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
			// Horizontal rule
			.replace(/^---$/gim, '<hr />')
			// Unordered lists
			.replace(/^\* (.*$)/gim, '<li>$1</li>')
			.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
			// Ordered lists
			.replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
			// Paragraphs
			.replace(/\n\n/g, '</p><p>')
			.replace(/^(?!<[hubliocp])/gim, '<p>')
			.replace(/(?<![>])$/gim, '</p>');
	}

	// Simple HTML to Markdown conversion
	function htmlToMarkdown(html: string): string {
		if (!html || html === '<p></p>') return '';

		return html
			// Headers
			.replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
			.replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
			.replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
			// Bold
			.replace(/<strong>(.*?)<\/strong>/gi, '**$1**')
			.replace(/<b>(.*?)<\/b>/gi, '**$1**')
			// Italic
			.replace(/<em>(.*?)<\/em>/gi, '*$1*')
			.replace(/<i>(.*?)<\/i>/gi, '*$1*')
			// Strikethrough
			.replace(/<s>(.*?)<\/s>/gi, '~~$1~~')
			.replace(/<strike>(.*?)<\/strike>/gi, '~~$1~~')
			// Code
			.replace(/<code>(.*?)<\/code>/gi, '`$1`')
			// Links
			.replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')
			// Images
			.replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*\/?>/gi, '![$2]($1)')
			.replace(/<img[^>]*src="([^"]*)"[^>]*\/?>/gi, '![]($1)')
			// Blockquotes
			.replace(/<blockquote>(.*?)<\/blockquote>/gi, '> $1\n\n')
			// Horizontal rule
			.replace(/<hr\s*\/?>/gi, '---\n\n')
			// Lists
			.replace(/<ul>(.*?)<\/ul>/gis, (_, content) => {
				return content.replace(/<li>(.*?)<\/li>/gi, '* $1\n') + '\n';
			})
			.replace(/<ol>(.*?)<\/ol>/gis, (_, content) => {
				let i = 0;
				return content.replace(/<li>(.*?)<\/li>/gi, () => `${++i}. $1\n`) + '\n';
			})
			// Paragraphs and line breaks
			.replace(/<p>(.*?)<\/p>/gi, '$1\n\n')
			.replace(/<br\s*\/?>/gi, '\n')
			// Clean up
			.replace(/&nbsp;/gi, ' ')
			.replace(/&lt;/gi, '<')
			.replace(/&gt;/gi, '>')
			.replace(/&amp;/gi, '&')
			.replace(/\n{3,}/g, '\n\n')
			.trim();
	}

	function toggleBold() {
		editor?.chain().focus().toggleBold().run();
	}

	function toggleItalic() {
		editor?.chain().focus().toggleItalic().run();
	}

	function toggleStrike() {
		editor?.chain().focus().toggleStrike().run();
	}

	function toggleCode() {
		editor?.chain().focus().toggleCode().run();
	}

	function toggleHeading(level: 1 | 2 | 3) {
		editor?.chain().focus().toggleHeading({ level }).run();
	}

	function toggleBulletList() {
		editor?.chain().focus().toggleBulletList().run();
	}

	function toggleOrderedList() {
		editor?.chain().focus().toggleOrderedList().run();
	}

	function toggleBlockquote() {
		editor?.chain().focus().toggleBlockquote().run();
	}

	function setHorizontalRule() {
		editor?.chain().focus().setHorizontalRule().run();
	}

	function setLink() {
		const url = prompt('URL del link:');
		if (url) {
			editor?.chain().focus().setLink({ href: url }).run();
		}
	}

	function addImage() {
		const url = prompt('URL dell\'immagine:');
		if (url) {
			editor?.chain().focus().setImage({ src: url }).run();
		}
	}

	function undo() {
		editor?.chain().focus().undo().run();
	}

	function redo() {
		editor?.chain().focus().redo().run();
	}

	function setParagraph() {
		editor?.chain().focus().setParagraph().run();
	}
</script>

<div class="markdown-editor">
	{#if label}
		<label class="editor-label">{label}</label>
	{/if}

	<div class="toolbar">
		<div class="toolbar-group">
			<button
				type="button"
				onclick={toggleBold}
				class:active={editor?.isActive('bold')}
				title="Grassetto"
			>
				<Bold size={16} />
			</button>
			<button
				type="button"
				onclick={toggleItalic}
				class:active={editor?.isActive('italic')}
				title="Corsivo"
			>
				<Italic size={16} />
			</button>
			<button
				type="button"
				onclick={toggleStrike}
				class:active={editor?.isActive('strike')}
				title="Barrato"
			>
				<Strikethrough size={16} />
			</button>
			<button
				type="button"
				onclick={toggleCode}
				class:active={editor?.isActive('code')}
				title="Codice"
			>
				<Code size={16} />
			</button>
		</div>

		<div class="toolbar-divider"></div>

		<div class="toolbar-group">
			<button
				type="button"
				onclick={setParagraph}
				class:active={editor?.isActive('paragraph')}
				title="Paragrafo"
			>
				<Pilcrow size={16} />
			</button>
			<button
				type="button"
				onclick={() => toggleHeading(1)}
				class:active={editor?.isActive('heading', { level: 1 })}
				title="Titolo 1"
			>
				<Heading1 size={16} />
			</button>
			<button
				type="button"
				onclick={() => toggleHeading(2)}
				class:active={editor?.isActive('heading', { level: 2 })}
				title="Titolo 2"
			>
				<Heading2 size={16} />
			</button>
			<button
				type="button"
				onclick={() => toggleHeading(3)}
				class:active={editor?.isActive('heading', { level: 3 })}
				title="Titolo 3"
			>
				<Heading3 size={16} />
			</button>
		</div>

		<div class="toolbar-divider"></div>

		<div class="toolbar-group">
			<button
				type="button"
				onclick={toggleBulletList}
				class:active={editor?.isActive('bulletList')}
				title="Lista puntata"
			>
				<List size={16} />
			</button>
			<button
				type="button"
				onclick={toggleOrderedList}
				class:active={editor?.isActive('orderedList')}
				title="Lista numerata"
			>
				<ListOrdered size={16} />
			</button>
			<button
				type="button"
				onclick={toggleBlockquote}
				class:active={editor?.isActive('blockquote')}
				title="Citazione"
			>
				<Quote size={16} />
			</button>
			<button type="button" onclick={setHorizontalRule} title="Linea orizzontale">
				<Minus size={16} />
			</button>
		</div>

		<div class="toolbar-divider"></div>

		<div class="toolbar-group">
			<button type="button" onclick={setLink} title="Inserisci link">
				<LinkIcon size={16} />
			</button>
			<button type="button" onclick={addImage} title="Inserisci immagine">
				<ImageIcon size={16} />
			</button>
		</div>

		<div class="toolbar-divider"></div>

		<div class="toolbar-group">
			<button type="button" onclick={undo} title="Annulla">
				<Undo size={16} />
			</button>
			<button type="button" onclick={redo} title="Ripeti">
				<Redo size={16} />
			</button>
		</div>
	</div>

	<div class="editor-container" bind:this={element}></div>
</div>

<style>
	.markdown-editor {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.editor-label {
		font-weight: 500;
		color: var(--geko-dark);
		font-size: var(--text-sm);
	}

	.toolbar {
		display: flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-2) var(--space-3);
		background: var(--geko-light);
		border: 2px solid var(--geko-gray-light);
		border-bottom: none;
		border-radius: var(--radius-md) var(--radius-md) 0 0;
		flex-wrap: wrap;
	}

	.toolbar-group {
		display: flex;
		gap: var(--space-1);
	}

	.toolbar-divider {
		width: 1px;
		height: 24px;
		background: var(--geko-gray-light);
		margin: 0 var(--space-2);
	}

	.toolbar button {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		background: transparent;
		border: none;
		border-radius: var(--radius-sm);
		color: var(--geko-gray);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.toolbar button:hover {
		background: var(--geko-white);
		color: var(--geko-dark);
	}

	.toolbar button.active {
		background: var(--geko-gold);
		color: var(--geko-white);
	}

	.editor-container {
		min-height: 400px;
		background: var(--geko-white);
		border: 2px solid var(--geko-gray-light);
		border-radius: 0 0 var(--radius-md) var(--radius-md);
		overflow: hidden;
	}

	.editor-container :global(.prose-editor) {
		min-height: 400px;
		padding: var(--space-4);
		outline: none;
	}

	.editor-container :global(.prose-editor:focus) {
		box-shadow: inset 0 0 0 2px rgba(196, 163, 90, 0.2);
	}

	/* Prose styles */
	.editor-container :global(.prose-editor h1) {
		font-size: var(--text-3xl);
		font-weight: 700;
		color: var(--geko-gold);
		margin: var(--space-6) 0 var(--space-4);
	}

	.editor-container :global(.prose-editor h2) {
		font-size: var(--text-2xl);
		font-weight: 600;
		color: var(--geko-dark);
		margin: var(--space-5) 0 var(--space-3);
	}

	.editor-container :global(.prose-editor h3) {
		font-size: var(--text-xl);
		font-weight: 600;
		color: var(--geko-dark);
		margin: var(--space-4) 0 var(--space-2);
	}

	.editor-container :global(.prose-editor p) {
		margin: var(--space-3) 0;
		line-height: 1.7;
	}

	.editor-container :global(.prose-editor strong) {
		font-weight: 600;
	}

	.editor-container :global(.prose-editor em) {
		font-style: italic;
	}

	.editor-container :global(.prose-editor code) {
		font-family: var(--font-mono);
		font-size: 0.9em;
		background: var(--geko-light);
		padding: 0.125em 0.375em;
		border-radius: var(--radius-sm);
	}

	.editor-container :global(.prose-editor blockquote) {
		border-left: 4px solid var(--geko-gold);
		padding-left: var(--space-4);
		margin: var(--space-4) 0;
		color: var(--geko-gray);
		font-style: italic;
	}

	.editor-container :global(.prose-editor ul),
	.editor-container :global(.prose-editor ol) {
		padding-left: var(--space-6);
		margin: var(--space-3) 0;
	}

	.editor-container :global(.prose-editor li) {
		margin: var(--space-2) 0;
	}

	.editor-container :global(.prose-editor hr) {
		border: none;
		border-top: 2px solid var(--geko-gray-light);
		margin: var(--space-6) 0;
	}

	.editor-container :global(.prose-editor a),
	.editor-container :global(.editor-link) {
		color: var(--geko-magenta);
		text-decoration: underline;
	}

	.editor-container :global(.editor-image) {
		max-width: 100%;
		height: auto;
		border-radius: var(--radius-md);
		margin: var(--space-4) 0;
	}

	.editor-container :global(.ProseMirror-placeholder) {
		color: var(--geko-gray-light);
		pointer-events: none;
	}

	.editor-container :global(.ProseMirror-placeholder::before) {
		content: attr(data-placeholder);
		float: left;
		height: 0;
	}
</style>
