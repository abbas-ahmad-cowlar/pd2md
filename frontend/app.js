/**
 * PD2MD — Frontend Application v3
 *
 * Handles:
 *   - Single and batch file upload with drag-and-drop
 *   - API communication (upload, poll, download)
 *   - Per-file progress tracking in batch mode
 *   - Result display with raw/rendered markdown preview
 *   - Dark mode toggle with localStorage persistence
 *   - Toast notifications
 */

// ─── State ────────────────────────────────────────────────────
const state = {
    // Single mode
    jobId: null,
    pollTimer: null,
    markdownContent: '',
    // Batch mode
    batchId: null,
    batchJobs: [],
    currentSection: 'upload',
};

// ─── DOM References ───────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dropzone = $('#dropzone');
const fileInput = $('#file-input');
const uploadSection = $('#upload-section');
const processingSection = $('#processing-section');
const batchSection = $('#batch-section');
const resultSection = $('#result-section');
const errorSection = $('#error-section');

// ─── Theme Management ────────────────────────────────────────
function initTheme() {
    const saved = localStorage.getItem('pd2md-theme');
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        updateThemeIcons('dark');
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    if (next === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('pd2md-theme', next);
    updateThemeIcons(next);
}

function updateThemeIcons(theme) {
    const sun = $('#theme-icon-sun');
    const moon = $('#theme-icon-moon');
    if (theme === 'dark') {
        sun.classList.add('hidden');
        moon.classList.remove('hidden');
    } else {
        sun.classList.remove('hidden');
        moon.classList.add('hidden');
    }
}

$('#theme-toggle').addEventListener('click', toggleTheme);
initTheme();

// ─── Section Management ──────────────────────────────────────
function showSection(name) {
    state.currentSection = name;
    uploadSection.classList.toggle('hidden', name !== 'upload');
    processingSection.classList.toggle('hidden', name !== 'processing');
    batchSection.classList.toggle('hidden', name !== 'batch');
    resultSection.classList.toggle('hidden', name !== 'result');
    errorSection.classList.toggle('hidden', name !== 'error');

    const titles = {
        upload: 'PD2MD — PDF to Markdown',
        processing: 'Converting... | PD2MD',
        batch: 'Converting batch... | PD2MD',
        result: 'Done! | PD2MD',
        error: 'Error | PD2MD',
    };
    document.title = titles[name] || 'PD2MD';
}

// ─── Drag-and-Drop ─────────────────────────────────────────
dropzone.addEventListener('click', () => fileInput.click());
$('#browse-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFiles(files);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFiles(e.target.files);
});

// ─── File Handling (router) ─────────────────────────────────
function handleFiles(fileList) {
    // Filter PDFs
    const pdfs = [];
    for (const f of fileList) {
        if (f.name.toLowerCase().endsWith('.pdf')) pdfs.push(f);
    }
    if (pdfs.length === 0) {
        showError('Please select PDF files.');
        return;
    }
    if (pdfs.length === 1) {
        handleSingleFile(pdfs[0]);
    } else {
        handleBatchFiles(pdfs);
    }
}

// ─── Single File Flow ───────────────────────────────────────
async function handleSingleFile(file) {
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > 50) {
        showError(`File too large (${sizeMB.toFixed(1)} MB). Maximum: 50 MB.`);
        return;
    }

    showSection('processing');
    $('#file-name').textContent = file.name;
    $('#file-size').textContent = `${sizeMB.toFixed(1)} MB`;
    updateProgress(0, 'Uploading...');
    resetSteps();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/upload', { method: 'POST', body: formData });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Upload failed');
        }
        const data = await resp.json();
        state.jobId = data.job_id;
        startSinglePolling();
    } catch (err) {
        showError(err.message);
    }
}

function startSinglePolling() {
    stopPolling();
    state.pollTimer = setInterval(pollSingleStatus, 500);
}

async function pollSingleStatus() {
    if (!state.jobId) return;
    try {
        const resp = await fetch(`/api/jobs/${state.jobId}/status`);
        if (!resp.ok) throw new Error('Status check failed');
        const data = await resp.json();

        updateProgress(data.progress, data.current_step);
        updatePipelineSteps(data.progress);

        if (data.status === 'complete') {
            stopPolling();
            await showSingleResult(data);
        } else if (data.status === 'error') {
            stopPolling();
            showError(data.error || 'Conversion failed');
        }
    } catch (err) {
        console.error('Poll error:', err);
    }
}

// ─── Batch File Flow ────────────────────────────────────────
async function handleBatchFiles(files) {
    showSection('batch');
    $('#batch-count').textContent = files.length;
    $('#batch-subtitle').textContent = `Uploading ${files.length} files...`;
    $('#batch-progress-bar').style.width = '0%';
    $('#file-queue').innerHTML = '';

    const formData = new FormData();
    for (const f of files) {
        formData.append('files', f);
    }

    try {
        const resp = await fetch('/api/upload-batch', { method: 'POST', body: formData });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Batch upload failed');
        }
        const data = await resp.json();
        state.batchId = data.batch_id;
        state.batchJobs = data.jobs;

        // Build initial queue UI
        const queue = $('#file-queue');
        queue.innerHTML = '';
        for (const job of data.jobs) {
            const item = document.createElement('div');
            item.className = 'queue-item';
            item.id = `queue-${job.job_id}`;
            item.innerHTML = `
                <span class="queue-item-icon">📄</span>
                <span class="queue-item-name">${job.filename}</span>
                <span class="queue-item-status">Queued</span>
            `;
            queue.appendChild(item);
        }

        startBatchPolling();
    } catch (err) {
        showError(err.message);
    }
}

function startBatchPolling() {
    stopPolling();
    state.pollTimer = setInterval(pollBatchStatus, 700);
}

async function pollBatchStatus() {
    if (!state.batchId) return;
    try {
        const resp = await fetch(`/api/batches/${state.batchId}/status`);
        if (!resp.ok) throw new Error('Batch status check failed');
        const data = await resp.json();

        // Update overall progress
        $('#batch-progress-bar').style.width = `${data.overall_progress}%`;
        $('#batch-subtitle').textContent = `${data.completed} of ${data.total} complete` +
            (data.failed > 0 ? ` · ${data.failed} failed` : '');

        // Update each queue item
        for (const job of data.jobs) {
            const item = $(`#queue-${job.id}`);
            if (!item) continue;

            item.className = 'queue-item';
            const statusEl = item.querySelector('.queue-item-status');
            const iconEl = item.querySelector('.queue-item-icon');

            if (job.status === 'complete') {
                item.classList.add('done');
                statusEl.textContent = '✓ Done';
                iconEl.textContent = '✅';
            } else if (job.status === 'error') {
                item.classList.add('error');
                statusEl.textContent = '✗ Failed';
                iconEl.textContent = '❌';
            } else if (job.status === 'processing') {
                item.classList.add('active');
                statusEl.textContent = `${Math.round(job.progress)}%`;
                iconEl.textContent = '⏳';
            } else {
                statusEl.textContent = 'Queued';
                iconEl.textContent = '📄';
            }
        }

        // All done?
        if (data.all_done) {
            stopPolling();
            showBatchResult(data);
        }
    } catch (err) {
        console.error('Batch poll error:', err);
    }
}

function showBatchResult(data) {
    // Populate stats with totals
    let totalPages = 0, totalBlocks = 0, totalImages = 0, totalTables = 0;
    for (const job of data.jobs) {
        if (job.result_stats) {
            totalPages += job.result_stats.pages || 0;
            totalBlocks += job.result_stats.blocks || 0;
            totalImages += job.result_stats.images || 0;
            totalTables += job.result_stats.tables || 0;
        }
    }
    $('#stat-pages').textContent = totalPages;
    $('#stat-blocks').textContent = totalBlocks;
    $('#stat-images').textContent = totalImages;
    $('#stat-tables').textContent = totalTables;

    // Show first successful file's preview
    const firstComplete = data.jobs.find(j => j.status === 'complete');
    if (firstComplete) {
        loadPreview(firstComplete.id);
    }

    showSection('result');
}

// ─── Shared Helpers ─────────────────────────────────────────
function stopPolling() {
    if (state.pollTimer) {
        clearInterval(state.pollTimer);
        state.pollTimer = null;
    }
}

function updateProgress(pct, step) {
    $('#progress-bar').style.width = `${pct}%`;
    $('#progress-pct').textContent = `${Math.round(pct)}%`;
    $('#progress-step').textContent = step;
}

function resetSteps() {
    $$('.step').forEach(el => el.classList.remove('active', 'done'));
}

function updatePipelineSteps(progress) {
    const steps = [
        { id: 'step-extract', threshold: 5 },
        { id: 'step-assemble', threshold: 20 },
        { id: 'step-layout', threshold: 40 },
        { id: 'step-semantics', threshold: 55 },
        { id: 'step-tables', threshold: 70 },
        { id: 'step-emit', threshold: 90 },
    ];
    for (let i = 0; i < steps.length; i++) {
        const el = $(`#${steps[i].id}`);
        const nextThreshold = i + 1 < steps.length ? steps[i + 1].threshold : 100;
        if (progress >= nextThreshold) {
            el.classList.add('done');
            el.classList.remove('active');
        } else if (progress >= steps[i].threshold) {
            el.classList.add('active');
            el.classList.remove('done');
        } else {
            el.classList.remove('active', 'done');
        }
    }
}

// ─── Result Display ─────────────────────────────────────────
async function showSingleResult(data) {
    if (data.result_stats) {
        $('#stat-pages').textContent = data.result_stats.pages || 0;
        $('#stat-blocks').textContent = data.result_stats.blocks || 0;
        $('#stat-images').textContent = data.result_stats.images || 0;
        $('#stat-tables').textContent = data.result_stats.tables || 0;
    }
    await loadPreview(state.jobId);
    showSection('result');
}

async function loadPreview(jobId) {
    try {
        const resp = await fetch(`/api/jobs/${jobId}/preview`);
        if (resp.ok) {
            const preview = await resp.json();
            state.markdownContent = preview.content;
            $('#preview-raw').textContent = preview.content;
            $('#preview-rendered').innerHTML = renderMarkdown(preview.content);
        }
    } catch (err) {
        $('#preview-raw').textContent = '(Preview not available)';
    }
}

function showError(message) {
    $('#error-message').textContent = message;
    showSection('error');
    stopPolling();
}

// ─── Simple Markdown Renderer ───────────────────────────────
function renderMarkdown(md) {
    md = md.replace(/^---[\s\S]*?---\n*/m, '');
    let html = md
        .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
            `<pre><code>${escapeHtml(code.trim())}</code></pre>`)
        .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^---$/gm, '<hr>')
        .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^(?!<[a-z])((?!^\s*$).+)$/gm, '<p>$1</p>');
    html = html.replace(/(<li>.*?<\/li>\n?)+/gs, (match) => `<ul>${match}</ul>`);
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─── Preview Tabs ───────────────────────────────────────────
$$('.preview-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        $$('.preview-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const isRaw = tab.dataset.tab === 'raw';
        $('#preview-raw').classList.toggle('hidden', !isRaw);
        $('#preview-rendered').classList.toggle('hidden', isRaw);
    });
});

// ─── Download Handlers ──────────────────────────────────────
function triggerDownload(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

$('#btn-download-md').addEventListener('click', () => {
    if (state.batchId) {
        triggerDownload(`/api/batches/${state.batchId}/download`, 'pd2md_batch_results.zip');
    } else if (state.jobId) {
        let name = $('#file-name').textContent;
        name = name ? name.replace('.pdf', '.md') : 'document.md';
        triggerDownload(`/api/jobs/${state.jobId}/download/markdown`, name);
    }
});

$('#btn-download-zip').addEventListener('click', () => {
    if (state.batchId) {
        triggerDownload(`/api/batches/${state.batchId}/download`, 'pd2md_batch_results.zip');
    } else if (state.jobId) {
        let name = $('#file-name').textContent;
        name = name ? name.replace('.pdf', '_package.zip') : 'package.zip';
        triggerDownload(`/api/jobs/${state.jobId}/download/zip`, name);
    }
});

// ─── Copy to Clipboard ─────────────────────────────────────
$('#btn-copy').addEventListener('click', async () => {
    if (!state.markdownContent) return;
    try {
        await navigator.clipboard.writeText(state.markdownContent);
        showToast('Copied to clipboard!');
    } catch (err) {
        console.error('Copy failed:', err);
    }
});

// ─── Toast Notifications ────────────────────────────────────
function showToast(message, duration = 2500) {
    const toast = $('#toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
}

// ─── New / Retry ────────────────────────────────────────────
$('#btn-new').addEventListener('click', resetAll);
$('#btn-retry').addEventListener('click', resetAll);

function resetAll() {
    state.jobId = null;
    state.batchId = null;
    state.batchJobs = [];
    state.markdownContent = '';
    fileInput.value = '';
    showSection('upload');
}
