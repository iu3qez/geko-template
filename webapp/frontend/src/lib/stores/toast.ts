import { writable } from 'svelte/store';

export interface ToastMessage {
	id: string;
	type: 'success' | 'error' | 'warning' | 'info';
	message: string;
	duration?: number;
}

function createToastStore() {
	const { subscribe, update } = writable<ToastMessage[]>([]);

	function add(message: Omit<ToastMessage, 'id'>) {
		const id = Math.random().toString(36).slice(2, 9);
		const toast: ToastMessage = { id, ...message };

		update(toasts => [...toasts, toast]);

		if (message.duration !== 0) {
			setTimeout(() => {
				remove(id);
			}, message.duration || 5000);
		}

		return id;
	}

	function remove(id: string) {
		update(toasts => toasts.filter(t => t.id !== id));
	}

	function success(message: string, duration?: number) {
		return add({ type: 'success', message, duration });
	}

	function error(message: string, duration?: number) {
		return add({ type: 'error', message, duration: duration || 8000 });
	}

	function warning(message: string, duration?: number) {
		return add({ type: 'warning', message, duration });
	}

	function info(message: string, duration?: number) {
		return add({ type: 'info', message, duration });
	}

	return {
		subscribe,
		add,
		remove,
		success,
		error,
		warning,
		info
	};
}

export const toasts = createToastStore();
