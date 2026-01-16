/**
 * GEKO Magazine - Editor Markdown WYSIWYG
 *
 * Integrazione EasyMDE per editing Markdown con:
 * - Toolbar formattazione
 * - Preview live side-by-side
 * - Supporto drag & drop immagini
 * - Scorciatoie tastiera
 *
 * Configurazione:
 *   L'editor può essere abilitato/disabilitato tramite:
 *   - localStorage: 'geko_editor_mode' = 'wysiwyg' | 'plain'
 *   - Toggle nell'interfaccia
 */

// Configurazione default
const EDITOR_CONFIG = {
    // Abilita editor WYSIWYG di default
    defaultMode: 'wysiwyg',  // 'wysiwyg' o 'plain'

    // Endpoint upload immagini
    uploadEndpoint: '/upload/image/editor',

    // Opzioni EasyMDE
    easymde: {
        spellChecker: false,
        autosave: {
            enabled: true,
            uniqueId: 'geko-article-editor',
            delay: 5000,  // Salva ogni 5 secondi
        },
        placeholder: 'Scrivi il tuo articolo in Markdown...\n\n## Sezione\n\nTesto con **grassetto** e *corsivo*.',
        toolbar: [
            'bold', 'italic', 'heading', '|',
            'quote', 'unordered-list', 'ordered-list', '|',
            'link', 'image', 'upload-image', 'table', '|',
            'preview', 'side-by-side', 'fullscreen', '|',
            'guide',
            {
                name: 'box-evidenza',
                action: insertBoxEvidenza,
                className: 'fa fa-lightbulb',
                title: 'Inserisci Box Evidenza',
            }
        ],
        sideBySideFullscreen: false,
        status: ['autosave', 'lines', 'words', 'upload-image'],
        // Upload immagini
        uploadImage: true,
        imageUploadFunction: uploadImageHandler,
        imageMaxSize: 10 * 1024 * 1024, // 10MB
        imageAccept: 'image/png, image/jpeg, image/gif, image/webp',
    }
};

// Istanza editor globale
let editorInstance = null;

/**
 * Handler per upload immagini (drag&drop, paste, bottone)
 *
 * @param {File} file - Il file immagine da caricare
 * @param {Function} onSuccess - Callback successo, riceve URL immagine
 * @param {Function} onError - Callback errore, riceve messaggio
 */
function uploadImageHandler(file, onSuccess, onError) {
    // Validazione client-side
    const maxSize = EDITOR_CONFIG.easymde.imageMaxSize;
    if (file.size > maxSize) {
        onError(`File troppo grande. Massimo: ${maxSize / (1024 * 1024)}MB`);
        return;
    }

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        onError('Formato non supportato. Usa: JPG, PNG, GIF o WebP');
        return;
    }

    // Prepara form data
    const formData = new FormData();
    formData.append('file', file);

    // Aggiungi article_id se presente nel form
    const articleIdInput = document.querySelector('input[name="article_id"]');
    if (articleIdInput && articleIdInput.value) {
        formData.append('article_id', articleIdInput.value);
    }

    // Upload
    fetch(EDITOR_CONFIG.uploadEndpoint, {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.detail || 'Errore upload');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Immagine caricata:', data);
        onSuccess(data.url);
    })
    .catch(error => {
        console.error('Errore upload immagine:', error);
        onError(error.message || 'Errore durante il caricamento');
    });
}

/**
 * Inserisce un box evidenza nel testo
 */
function insertBoxEvidenza(editor) {
    const cm = editor.codemirror;
    const selection = cm.getSelection();
    const text = selection || 'Contenuto del box';

    cm.replaceSelection(`\n!!! nota "Titolo Box"\n${text}\n!!!\n`);
}

/**
 * Inizializza l'editor WYSIWYG su una textarea
 *
 * @param {string} textareaId - ID della textarea da convertire
 * @returns {EasyMDE|null} - Istanza dell'editor o null se in modalità plain
 */
function initEditor(textareaId = 'contenuto_md') {
    const textarea = document.getElementById(textareaId);
    if (!textarea) {
        console.warn('Textarea non trovata:', textareaId);
        return null;
    }

    // Controlla modalità salvata
    const savedMode = localStorage.getItem('geko_editor_mode');
    const mode = savedMode || EDITOR_CONFIG.defaultMode;

    if (mode === 'plain') {
        console.log('Editor in modalità plain (textarea semplice)');
        return null;
    }

    // Distruggi istanza precedente se esiste
    if (editorInstance) {
        editorInstance.toTextArea();
        editorInstance = null;
    }

    // Crea editor EasyMDE
    try {
        editorInstance = new EasyMDE({
            element: textarea,
            ...EDITOR_CONFIG.easymde
        });

        console.log('Editor WYSIWYG inizializzato');
        return editorInstance;
    } catch (error) {
        console.error('Errore inizializzazione editor:', error);
        return null;
    }
}

/**
 * Toggle tra modalità WYSIWYG e plain
 */
function toggleEditorMode() {
    const currentMode = localStorage.getItem('geko_editor_mode') || EDITOR_CONFIG.defaultMode;
    const newMode = currentMode === 'wysiwyg' ? 'plain' : 'wysiwyg';

    localStorage.setItem('geko_editor_mode', newMode);

    // Salva contenuto corrente
    let content = '';
    if (editorInstance) {
        content = editorInstance.value();
        editorInstance.toTextArea();
        editorInstance = null;
    } else {
        const textarea = document.getElementById('contenuto_md');
        content = textarea ? textarea.value : '';
    }

    // Ricarica pagina per applicare cambio
    // (oppure re-inizializza l'editor)
    location.reload();
}

/**
 * Ottieni il contenuto dell'editor
 * Funziona sia con WYSIWYG che plain
 */
function getEditorContent() {
    if (editorInstance) {
        return editorInstance.value();
    }
    const textarea = document.getElementById('contenuto_md');
    return textarea ? textarea.value : '';
}

/**
 * Imposta il contenuto dell'editor
 */
function setEditorContent(content) {
    if (editorInstance) {
        editorInstance.value(content);
    } else {
        const textarea = document.getElementById('contenuto_md');
        if (textarea) textarea.value = content;
    }
}

// Auto-inizializza quando il DOM è pronto
document.addEventListener('DOMContentLoaded', function() {
    // Cerca textarea con data-editor="wysiwyg"
    const editorTextarea = document.querySelector('textarea[data-editor="wysiwyg"]');
    if (editorTextarea) {
        initEditor(editorTextarea.id);
    }
});

// Esporta per uso globale
window.GekoEditor = {
    init: initEditor,
    toggle: toggleEditorMode,
    getContent: getEditorContent,
    setContent: setEditorContent,
    getInstance: () => editorInstance,
    uploadImage: uploadImageHandler,
};
