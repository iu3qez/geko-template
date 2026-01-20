/**
 * API Client for GEKO Magazine
 */

const API_BASE = '/api';

// Types
export interface Article {
	id: number;
	titolo: string;
	sottotitolo: string;
	autore: string;
	nome_autore: string;
	contenuto_md: string;
	contenuto_typ: string;
	sommario_llm: string;
	ordine: number;
	created_at: string;
	updated_at: string;
	magazines: Magazine[];
	images: Image[];
}

export interface Magazine {
	id: number;
	numero: string;
	mese: string;
	anno: string;
	stato: 'bozza' | 'pubblicato';
	editoriale: string;
	editoriale_autore: string;
	copertina_id: number | null;
	copertina: Image | null;
	created_at: string;
	updated_at: string;
	articles: Article[];
	article_count?: number;
}

export interface Image {
	id: number;
	filename: string;
	original_filename: string;
	path: string;
	alt_text: string;
	article_id: number | null;
	uploaded_at: string;
	url: string;
	is_published: boolean;
}

export interface ConfigItem {
	key: string;
	value: string;
	description: string;
	updated_at: string | null;
}

export interface ApiError {
	detail: string;
}

// Helper for fetch with error handling
async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
	const response = await fetch(url, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...options?.headers
		}
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: response.statusText }));
		throw new Error(error.detail || `HTTP ${response.status}`);
	}

	return response.json();
}

// Articles API
export const articles = {
	list: (params?: { magazine_id?: number; search?: string }) => {
		const query = new URLSearchParams();
		if (params?.magazine_id) query.set('magazine_id', String(params.magazine_id));
		if (params?.search) query.set('search', params.search);
		const qs = query.toString();
		return fetchJson<Article[]>(`${API_BASE}/articles${qs ? '?' + qs : ''}`);
	},

	get: (id: number) => fetchJson<Article>(`${API_BASE}/articles/${id}`),

	create: (data: Partial<Article>) =>
		fetchJson<Article>(`${API_BASE}/articles`, {
			method: 'POST',
			body: JSON.stringify(data)
		}),

	update: (id: number, data: Partial<Article>) =>
		fetchJson<Article>(`${API_BASE}/articles/${id}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		}),

	delete: (id: number) =>
		fetchJson<{ status: string }>(`${API_BASE}/articles/${id}`, {
			method: 'DELETE'
		}),

	generateSummary: (id: number) =>
		fetchJson<Article>(`${API_BASE}/articles/${id}/summary`, {
			method: 'POST'
		}),

	assign: (id: number, magazineIds: number[]) =>
		fetchJson<Article>(`${API_BASE}/articles/${id}/assign`, {
			method: 'POST',
			body: JSON.stringify({ magazine_ids: magazineIds })
		})
};

// Magazines API
export const magazines = {
	list: () => fetchJson<Magazine[]>(`${API_BASE}/magazines`),

	get: (id: number) => fetchJson<Magazine>(`${API_BASE}/magazines/${id}`),

	create: (data: Partial<Magazine>) =>
		fetchJson<Magazine>(`${API_BASE}/magazines`, {
			method: 'POST',
			body: JSON.stringify(data)
		}),

	update: (id: number, data: Partial<Magazine>) =>
		fetchJson<Magazine>(`${API_BASE}/magazines/${id}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		}),

	delete: (id: number) =>
		fetchJson<{ status: string }>(`${API_BASE}/magazines/${id}`, {
			method: 'DELETE'
		}),

	build: (id: number) =>
		fetchJson<{ status: string; pdf_url?: string; error?: string }>(`${API_BASE}/magazines/${id}/build`, {
			method: 'POST'
		}),

	getPdfUrl: (id: number) => `${API_BASE}/magazines/${id}/pdf`,

	addArticle: (magazineId: number, articleId: number, ordine?: number) =>
		fetchJson<{ status: string; ordine: number }>(`${API_BASE}/magazines/${magazineId}/articles/${articleId}`, {
			method: 'POST',
			body: JSON.stringify({ ordine })
		}),

	removeArticle: (magazineId: number, articleId: number) =>
		fetchJson<{ status: string }>(`${API_BASE}/magazines/${magazineId}/articles/${articleId}`, {
			method: 'DELETE'
		}),

	reorderArticles: (magazineId: number, articleIds: number[]) =>
		fetchJson<{ status: string }>(`${API_BASE}/magazines/${magazineId}/articles/reorder`, {
			method: 'POST',
			body: JSON.stringify({ article_ids: articleIds })
		})
};

// Images API
export const images = {
	list: (params?: { article_id?: number; magazine_id?: number; published?: boolean }) => {
		const query = new URLSearchParams();
		if (params?.article_id) query.set('article_id', String(params.article_id));
		if (params?.magazine_id) query.set('magazine_id', String(params.magazine_id));
		if (params?.published !== undefined) query.set('published', String(params.published));
		const qs = query.toString();
		return fetchJson<Image[]>(`${API_BASE}/images${qs ? '?' + qs : ''}`);
	},

	get: (id: number) => fetchJson<Image>(`${API_BASE}/images/${id}`),

	upload: async (file: File, articleId?: number): Promise<Image> => {
		const formData = new FormData();
		formData.append('file', file);
		if (articleId) formData.append('article_id', String(articleId));

		const response = await fetch(`${API_BASE}/images`, {
			method: 'POST',
			body: formData
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: response.statusText }));
			throw new Error(error.detail || `HTTP ${response.status}`);
		}

		return response.json();
	},

	uploadMultiple: async (files: File[], articleId?: number): Promise<Image[]> => {
		const formData = new FormData();
		files.forEach(file => formData.append('files', file));
		if (articleId) formData.append('article_id', String(articleId));

		const response = await fetch(`${API_BASE}/images/batch`, {
			method: 'POST',
			body: formData
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: response.statusText }));
			throw new Error(error.detail || `HTTP ${response.status}`);
		}

		return response.json();
	},

	update: (id: number, data: { alt_text?: string; article_id?: number | null }) =>
		fetchJson<Image>(`${API_BASE}/images/${id}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		}),

	delete: (id: number) =>
		fetchJson<{ status: string }>(`${API_BASE}/images/${id}`, {
			method: 'DELETE'
		})
};

// Config API
export const config = {
	getAll: () => fetchJson<Record<string, ConfigItem>>(`${API_BASE}/config`),

	get: (key: string) => fetchJson<ConfigItem>(`${API_BASE}/config/${key}`),

	update: (data: Record<string, string>) =>
		fetchJson<{ status: string }>(`${API_BASE}/config`, {
			method: 'PUT',
			body: JSON.stringify(data)
		})
};

// Export all as default
export default { articles, magazines, images, config };
