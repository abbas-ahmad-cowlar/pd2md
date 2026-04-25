/**
 * PD2MD — Frontend Application Logic
 *
 * Handles:
 *   - Drag-and-drop file upload
 *   - API communication (upload, poll status, download)
 *   - Progress tracking with pipeline step visualization
 *   - Result display and markdown preview
 */

// ─── State ────────────────────────────────────────────────────
const state = {
    jobId: null,
    pollTimer: null,
    currentSection: 'upload',
};

// ─── DOM References ───────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dropzone = $('#dropzone');
const fileInput = $('#file-input');
const uploadSection = $('#upload-section');
const processingSection = $('#processing-section');
const resultSection = $('#result-section');
const errorSection = $('#error-section');

// ─── Section Management ──────────────────────────────────────
function showSection(name) {
    state.currentSection = name;
    uploadSection.classList.toggle('hidden', name !== 'upload');
    processingSection.classList.toggle('hidden', name !== 'processing');
    resultSection.classList.toggle('hidden', name !== 'result');
    errorSection.classList.toggle('hidden', name !== 'error');
}

// ─── Drag-and-Drop ─────────────────────────────────────────
dropzone.addEventListener('click', () => fileInput.click());

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
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// ─── File Handling ──────────────────────────────────────────
async function handleFile(file) {
    // Validate
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showError('Please select a PDF file.');
        return;
    }

    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > 50) {
        showError(`File too large (${sizeMB.toFixed(1)} MB). Maximum: 50 MB.`);
        return;
    }

    // Show processing
    showSection('processing');
    $('#file-name').textContent = file.name;
    $('#file-size').textContent = `${sizeMB.toFixed(1)} MB`;
    updateProgress(0, 'Uploading...');
    resetSteps();

    // Upload
    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Upload failed');
        }

        const data = await resp.json();
        state.jobId = data.job_id;

        // Start polling
        startPolling();

    } catch (err) {
        showError(err.message);
    }
}

// ─── Progress Polling ───────────────────────────────────────
function startPolling() {
    stopPolling();
    state.pollTimer = setInterval(pollStatus, 500);
}

function stopPolling() {
    if (state.pollTimer) {
        clearInterval(state.pollTimer);
        state.pollTimer = null;
    }
}

async function pollStatus() {
    if (!state.jobId) return;

    try {
        const resp = await fetch(`/api/jobs/${state.jobId}/status`);
        if (!resp.ok) throw new Error('Status check failed');

        const data = await resp.json();

        updateProgress(data.progress, data.current_step);
        updatePipelineSteps(data.progress);

        if (data.status === 'complete') {
            stopPolling();
            await showResult(data);
        } else if (data.status === 'error') {
            stopPolling();
            showError(data.error || 'Conversion failed');
        }

    } catch (err) {
        // Network error — keep trying
        console.error('Poll error:', err);
    }
}

// ─── UI Updates ─────────────────────────────────────────────
function updateProgress(pct, step) {
    $('#progress-bar').style.width = `${pct}%`;
    $('#progress-pct').textContent = `${Math.round(pct)}%`;
    $('#progress-step').textContent = step;
}

function resetSteps() {
    $$('.step').forEach(el => {
        el.classList.remove('active', 'done');
    });
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
async function showResult(data) {
    // Update stats
    if (data.result_stats) {
        $('#stat-pages').textContent = data.result_stats.pages || 0;
        $('#stat-blocks').textContent = data.result_stats.blocks || 0;
        $('#stat-images').textContent = data.result_stats.images || 0;
        $('#stat-tables').textContent = data.result_stats.tables || 0;
    }

    // Load preview
    try {
        const resp = await fetch(`/api/jobs/${state.jobId}/preview`);
        if (resp.ok) {
            const preview = await resp.json();
            $('#preview-content').textContent = preview.content;
        }
    } catch (err) {
        $('#preview-content').textContent = '(Preview not available)';
    }

    showSection('result');
}

function showError(message) {
    $('#error-message').textContent = message;
    showSection('error');
    stopPolling();
}

// ─── Download Handlers ──────────────────────────────────────
$('#btn-download-md').addEventListener('click', () => {
    if (state.jobId) {
        window.location.href = `/api/jobs/${state.jobId}/download/markdown`;
    }
});

$('#btn-download-zip').addEventListener('click', () => {
    if (state.jobId) {
        window.location.href = `/api/jobs/${state.jobId}/download/zip`;
    }
});

$('#btn-copy').addEventListener('click', async () => {
    const content = $('#preview-content').textContent;
    try {
        await navigator.clipboard.writeText(content);
        const btn = $('#btn-copy');
        const origHTML = btn.innerHTML;
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!';
        btn.style.color = '#22c55e';
        setTimeout(() => {
            btn.innerHTML = origHTML;
            btn.style.color = '';
        }, 2000);
    } catch (err) {
        console.error('Copy failed:', err);
    }
});

// ─── New Conversion ─────────────────────────────────────────
$('#btn-new').addEventListener('click', () => {
    state.jobId = null;
    fileInput.value = '';
    showSection('upload');
});

$('#btn-retry').addEventListener('click', () => {
    state.jobId = null;
    fileInput.value = '';
    showSection('upload');
});
