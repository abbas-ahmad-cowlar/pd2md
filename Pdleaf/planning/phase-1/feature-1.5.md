# Feature 1.5 — PDF Viewer (pdf.js)

> **Phase**: 1 | **Feature**: 5 of 6
> **Goal**: Embed Mozilla's pdf.js in the right preview panel to render the compiled PDF. The viewer should render all pages in a scrollable container, scale pages to fit the panel width, and automatically reload when a new compilation succeeds.
> **Estimated Effort**: 3–5 hours
> **Dependencies**: Feature 1.1 (preview panel exists), Feature 1.4 (dispatches `compile-success` events with `pdfUrl`).

---

## Overview

This feature brings the preview pane to life. We are:
1. Installing and configuring pdf.js
2. Creating the PDF viewer module with load/clear/render logic
3. Handling the pdf.js Web Worker setup
4. Listening for compilation events and reloading the PDF
5. Implementing page scaling to fit the panel width
6. Handling placeholder states (before first compile, during loading, on error)

**What this feature does NOT include**: Zoom controls (Phase 3), SyncTeX click-to-jump (Phase 3), text selection layer (Phase 7), page thumbnails (Phase 7), detach to separate tab (Phase 3).

---

## Step 1: Install and Configure pdf.js

### What to Do
Install the `pdfjs-dist` npm package and configure the Web Worker.

### Sub-Steps

#### 1.5.1 — Install pdf.js
```bash
npm install pdfjs-dist
```

#### 1.5.2 — Understand the Web Worker requirement
pdf.js offloads PDF parsing to a Web Worker for performance. The worker file (`pdf.worker.js`) must be accessible to the browser.

**Three options for setting up the worker:**

**Option A — CDN (simplest, requires internet)**:
```javascript
import * as pdfjsLib from 'pdfjs-dist';
pdfjsLib.GlobalWorkerOptions.workerSrc = 
  `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
```

**Option B — Copy worker to public directory (recommended for local-first)**:
```javascript
// In your build config or manually:
// Copy node_modules/pdfjs-dist/build/pdf.worker.mjs to src/assets/pdf.worker.mjs
import * as pdfjsLib from 'pdfjs-dist';
pdfjsLib.GlobalWorkerOptions.workerSrc = '/assets/pdf.worker.mjs';
```

**Option C — Vite import (most modern)**:
```javascript
import * as pdfjsLib from 'pdfjs-dist';
import workerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url';
pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;
```

> **Recommendation**: Use Option C if Vite supports it. Fall back to Option B if not. Option A requires internet (breaks local-first principle).

### Definition of Done
- [ ] `pdfjs-dist` is installed
- [ ] Worker is configured and loads without errors
- [ ] `pdfjsLib.getDocument(url)` can be called without worker errors

### How to Test
```javascript
// Quick test in browser console:
import * as pdfjsLib from 'pdfjs-dist';
console.log('pdf.js version:', pdfjsLib.version);
// Should print a version number without errors
```

---

## Step 2: Create the PDF Viewer Module

### What to Do
Build `src/js/pdfViewer.js` — the module that renders PDFs in the preview panel.

### Sub-Steps

#### 1.5.3 — Module structure

```javascript
// src/js/pdfViewer.js
import * as pdfjsLib from 'pdfjs-dist';

// Configure worker (use whichever approach works — see Step 1)
import workerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url';
pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;

// Module state
let currentPdf = null;       // The loaded PDF document
let container = null;        // The #pdf-container element
const renderedPages = [];    // Array of canvas elements

/**
 * Initialize the PDF viewer.
 * @param {HTMLElement} containerElement - The #pdf-container DOM element
 */
export function initPdfViewer(containerElement) {
  container = containerElement;
  showPlaceholder('No PDF yet — click Compile');
}

/**
 * Load and render a PDF from a URL.
 * @param {string} url - URL of the PDF file
 */
export async function loadPDF(url) {
  if (!container) {
    console.error('PDF viewer not initialized');
    return;
  }

  showPlaceholder('Loading PDF...');

  try {
    // Add timestamp to bust cache
    const cacheBustedUrl = `${url}?t=${Date.now()}`;

    // Load the PDF document
    const loadingTask = pdfjsLib.getDocument(cacheBustedUrl);
    currentPdf = await loadingTask.promise;

    console.log(`PDF loaded: ${currentPdf.numPages} pages`);

    // Clear the container
    clearContainer();

    // Render all pages
    for (let pageNum = 1; pageNum <= currentPdf.numPages; pageNum++) {
      await renderPage(pageNum);
    }

  } catch (err) {
    console.error('Failed to load PDF:', err);
    showPlaceholder('Failed to load PDF. Try recompiling.');
  }
}

/**
 * Render a single page of the PDF.
 * @param {number} pageNum - 1-indexed page number
 */
async function renderPage(pageNum) {
  const page = await currentPdf.getPage(pageNum);

  // Calculate scale to fit container width
  const containerWidth = container.clientWidth - 40; // 20px padding each side
  const unscaledViewport = page.getViewport({ scale: 1 });
  const scale = containerWidth / unscaledViewport.width;
  const viewport = page.getViewport({ scale });

  // Create canvas for this page
  const canvas = document.createElement('canvas');
  canvas.className = 'pdf-page';
  canvas.width = viewport.width * window.devicePixelRatio;
  canvas.height = viewport.height * window.devicePixelRatio;
  canvas.style.width = `${viewport.width}px`;
  canvas.style.height = `${viewport.height}px`;

  const context = canvas.getContext('2d');
  context.scale(window.devicePixelRatio, window.devicePixelRatio);

  // Render the page
  await page.render({
    canvasContext: context,
    viewport,
  }).promise;

  container.appendChild(canvas);
  renderedPages.push(canvas);
}

/**
 * Clear all rendered pages.
 */
function clearContainer() {
  renderedPages.forEach(canvas => canvas.remove());
  renderedPages.length = 0;
  container.innerHTML = '';
}

/**
 * Show a placeholder message.
 * @param {string} message
 */
function showPlaceholder(message) {
  clearContainer();
  const p = document.createElement('p');
  p.className = 'placeholder-text';
  p.textContent = message;
  container.appendChild(p);
}
```

### Key Design Decisions

#### Why canvas-per-page (not one big canvas)?
- Each page is its own `<canvas>` element
- This allows natural scrolling — the browser handles scroll position
- Individual pages can be re-rendered on resize without affecting others
- Future: can add page numbers between canvases, click handlers per page (SyncTeX)

#### Why `devicePixelRatio` scaling?
- On high-DPI displays (Retina, 4K), a canvas rendered at 1x looks blurry
- We create the canvas at `2x` (or `3x` on high-DPI) physical pixels, then scale it down with CSS
- This produces crisp text on all displays

#### Why cache-busting with `?t=Date.now()`?
- The browser aggressively caches PDFs
- Even with `Cache-Control: no-cache` headers, some browsers still cache
- Adding a timestamp query parameter guarantees a fresh fetch every time

### Do's
- ✅ Scale pages to fit container width (not height — we want vertical scrolling)
- ✅ Use `devicePixelRatio` for crisp rendering on high-DPI screens
- ✅ Cache-bust the PDF URL with a timestamp
- ✅ Show "Loading PDF..." while rendering
- ✅ Handle errors gracefully (show error placeholder, don't crash)

### Don'ts
- ❌ Don't render all pages in a single canvas — use one canvas per page
- ❌ Don't add text selection layer — that's Phase 7
- ❌ Don't add zoom controls — that's Phase 3
- ❌ Don't try to render 500 pages all at once — for Phase 1, render all; optimize later if needed
- ❌ Don't add click handlers to the PDF (SyncTeX inverse sync is Phase 3)

### Definition of Done
- [ ] `loadPDF(url)` renders the PDF in the container
- [ ] All pages are rendered as individual canvases
- [ ] Pages are scaled to fit the container width
- [ ] Scrolling through pages works naturally
- [ ] "No PDF yet" placeholder shows before first compile
- [ ] "Loading PDF..." shows while rendering
- [ ] Cache-busted URL ensures fresh PDF on every load

---

## Step 3: Listen for Compilation Events

### What to Do
Connect the PDF viewer to the compiler module by listening for `compile-success` events.

### Sub-Steps

#### 1.5.4 — Event listener setup

Add to `src/js/pdfViewer.js`:

```javascript
/**
 * Start listening for compile events.
 * Call this after initPdfViewer().
 */
export function listenForCompileEvents() {
  document.addEventListener('compile-success', (e) => {
    const { pdfUrl } = e.detail;
    if (pdfUrl) {
      console.log('Compile success — loading PDF:', pdfUrl);
      loadPDF(pdfUrl);
    }
  });

  document.addEventListener('compile-error', () => {
    // Don't clear the existing PDF on error — keep showing the last successful render
    // Just log it. The compile button already shows the error state.
    console.log('Compile failed — keeping previous PDF');
  });
}
```

### Key Design Decisions
- **Don't clear PDF on error**: If the user makes a typo and compilation fails, they should still see their last successful PDF. Overleaf does the same.
- **Decoupled via events**: The PDF viewer doesn't import the compiler module. It just listens for DOM events. This makes the modules independent and testable.

### Definition of Done
- [ ] On `compile-success`, the PDF viewer loads the new PDF
- [ ] On `compile-error`, the existing PDF stays visible (not cleared)
- [ ] Console logs confirm event receipt

### How to Test
1. Click "Compile" → PDF should appear
2. Make a LaTeX error → Compile → old PDF should still be visible
3. Fix the error → Compile → new PDF should replace the old one

---

## Step 4: Add CSS for PDF Pages

### What to Do
Add styles for the rendered PDF page canvases.

### Sub-Steps

#### 1.5.5 — CSS rules

Add to `src/css/style.css`:
```css
/* PDF page canvases */
.pdf-page {
  display: block;
  margin: 10px auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  background: white;
  /* Don't add border-radius — PDFs should look like real paper */
}

/* PDF container scrolling */
#pdf-container {
  padding: 10px 0;
  background: var(--bg-primary);
}

/* Loading placeholder centered */
#pdf-container .placeholder-text {
  width: 100%;
  padding-top: 40%;
}
```

### Key Points
- **White background on canvas**: PDFs are typically white. The canvas should be white even though the app is dark-themed.
- **Box shadow**: Gives a "floating paper" effect that looks premium.
- **Centered with margin auto**: Pages are centered horizontally in the panel.
- **No border-radius**: Paper pages are rectangular. Don't round the corners.

### Definition of Done
- [ ] PDF pages appear as white rectangles with shadows on a dark background
- [ ] Pages are centered in the panel
- [ ] The "paper on dark desk" aesthetic looks professional

---

## Step 5: Handle Panel Resize

### What to Do
When the preview panel width changes (because the user drags the divider — Feature 1.6), the PDF pages should re-render at the new width.

### Sub-Steps

#### 1.5.6 — ResizeObserver

Add to `src/js/pdfViewer.js`:

```javascript
let resizeTimeout = null;

/**
 * Set up a ResizeObserver to re-render pages when the container resizes.
 */
export function setupResizeHandler() {
  if (!container) return;

  const observer = new ResizeObserver(() => {
    // Debounce: wait 300ms after resize stops before re-rendering
    if (resizeTimeout) clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      if (currentPdf) {
        console.log('Panel resized — re-rendering PDF');
        reRenderAllPages();
      }
    }, 300);
  });

  observer.observe(container.parentElement); // Observe the #preview-panel, not the container
}

/**
 * Re-render all pages at the current container width.
 */
async function reRenderAllPages() {
  if (!currentPdf) return;

  clearContainer();
  for (let pageNum = 1; pageNum <= currentPdf.numPages; pageNum++) {
    await renderPage(pageNum);
  }
}
```

### Key Points
- **Debounced at 300ms**: Re-rendering on every pixel of divider drag would be too expensive. Wait until dragging stops.
- **Observe parent element**: We observe `#preview-panel` (the section), not `#pdf-container` (which might change size as we add/remove canvases, creating an infinite loop).
- **Re-renders using existing PDF object**: We don't re-fetch the PDF from the server. The `currentPdf` object is already in memory. We just re-render at the new scale.

### Definition of Done
- [ ] Dragging the divider causes PDF pages to re-render at the new width
- [ ] Re-rendering is debounced (doesn't fire during drag, only after)
- [ ] No "infinite loop" of resize → render → resize

---

## Step 6: Wire Everything in `app.js`

### What to Do
Update `app.js` to initialize the PDF viewer.

### Sub-Steps

#### 1.5.7 — Update `app.js`

```javascript
// src/js/app.js (updated)
import { initEditor } from './editor.js';
import { initCompiler } from './compiler.js';
import { initPdfViewer, listenForCompileEvents, setupResizeHandler } from './pdfViewer.js';

const PROJECT_PATH = 'sample';
const MAIN_FILE = 'main.tex';

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Pdleaf v0.1.0 — Starting...');

  // 1. Initialize editor
  const editorContainer = document.getElementById('editor-container');
  let content = '';
  try {
    const response = await fetch(`/api/file?path=${PROJECT_PATH}/${MAIN_FILE}`);
    content = response.ok ? await response.text() : '% Could not load file.\n';
  } catch {
    content = '% Server unavailable.\n';
  }
  initEditor(editorContainer, content);

  // 2. Initialize compiler
  initCompiler();

  // 3. Initialize PDF viewer
  const pdfContainer = document.getElementById('pdf-container');
  initPdfViewer(pdfContainer);
  listenForCompileEvents();
  setupResizeHandler();

  console.log('Pdleaf: Ready ✅');
});
```

### Definition of Done
- [ ] PDF viewer initializes with "No PDF yet" placeholder
- [ ] Compile → PDF appears
- [ ] Resize → PDF re-renders

---

## Edge Cases

### 7.1 — Multi-page documents
A 10-page document should render all 10 pages as scrollable canvases. Test by adding enough content to generate multiple pages.

### 7.2 — Landscape pages
Some documents have landscape pages. The scaling should still fit width. The height will just be shorter.

### 7.3 — Very large PDFs
A 100+ page PDF may take a few seconds to render. The "Loading PDF..." placeholder should show during this time. For Phase 1, we render all pages. Lazy rendering can be optimized later.

### 7.4 — Missing PDF
If the server returns 404 (PDF doesn't exist yet), show the error placeholder. Don't crash.

### 7.5 — Broken PDF
If the PDF file is corrupted, `pdfjsLib.getDocument()` will reject. The catch block shows the error placeholder.

---

## Final Acceptance Checklist — Feature 1.5 Complete

| # | Check | Status |
|---|-------|--------|
| 1 | `pdfjs-dist` installed and worker configured | ☐ |
| 2 | `src/js/pdfViewer.js` exists with `initPdfViewer()`, `loadPDF()` | ☐ |
| 3 | "No PDF yet — click Compile" shows before first compile | ☐ |
| 4 | After compile, PDF renders in the preview panel | ☐ |
| 5 | All pages render (test with a multi-page document) | ☐ |
| 6 | Pages scale to fit the panel width | ☐ |
| 7 | Pages appear as white paper with shadow on dark background | ☐ |
| 8 | Scrolling through pages works smoothly | ☐ |
| 9 | Re-compiling replaces the old PDF with the new one | ☐ |
| 10 | Compilation error keeps the old PDF visible (doesn't clear) | ☐ |
| 11 | Resizing the panel re-renders pages at the new width | ☐ |
| 12 | No worker errors in the console | ☐ |
| 13 | High-DPI rendering is crisp (check on Retina/4K if available) | ☐ |
| 14 | No JavaScript errors in the console | ☐ |

> **When all 14 checks pass, Feature 1.5 is DONE. Proceed to Feature 1.6 (Split-Panel Layout).**
