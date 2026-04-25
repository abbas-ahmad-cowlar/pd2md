# Feature 1.6 — Split-Panel Layout (Resizable Divider)

> **Phase**: 1 | **Feature**: 6 of 6
> **Goal**: Make the editor and preview panels resizable by dragging a vertical divider between them. The user should be able to allocate more space to either the editor or the preview by dragging the divider left or right.
> **Estimated Effort**: 2–3 hours
> **Dependencies**: Feature 1.1 (HTML has `#divider`, `#editor-panel`, `#preview-panel`), Feature 1.5 (PDF viewer re-renders on resize via ResizeObserver).

---

## Overview

This is the final feature of Phase 1. We are:
1. Creating the `splitter.js` module that handles divider drag behavior
2. Implementing mousedown/mousemove/mouseup tracking
3. Applying panel width changes via CSS flexbox
4. Enforcing minimum width constraints
5. Handling edge cases (canvas interaction during drag, touch devices)
6. Optionally persisting the split position in `localStorage`

**What this feature does NOT include**: "Editor Only" / "Preview Only" toggle buttons (Phase 3+), horizontal split mode, sidebar (file tree — Phase 4).

---

## Step 1: Create the Splitter Module

### What to Do
Build `src/js/splitter.js` — the module that implements the draggable divider.

### Sub-Steps

#### 1.6.1 — Module structure

```javascript
// src/js/splitter.js

// Configuration
const MIN_PANEL_WIDTH = 200; // Minimum width in pixels for either panel
const STORAGE_KEY = 'pdleaf-split-position'; // localStorage key

// State
let isDragging = false;
let editorPanel = null;
let previewPanel = null;
let divider = null;
let workspace = null;

/**
 * Initialize the resizable split panel.
 */
export function initSplitter() {
  editorPanel = document.getElementById('editor-panel');
  previewPanel = document.getElementById('preview-panel');
  divider = document.getElementById('divider');
  workspace = document.getElementById('workspace');

  if (!editorPanel || !previewPanel || !divider || !workspace) {
    console.error('Splitter: Missing required DOM elements');
    return;
  }

  // Restore saved position or default to 50/50
  const savedPosition = localStorage.getItem(STORAGE_KEY);
  if (savedPosition) {
    applyPosition(parseFloat(savedPosition));
  } else {
    applyPosition(0.5); // 50% each
  }

  // Attach event listeners
  divider.addEventListener('mousedown', onMouseDown);
  divider.addEventListener('touchstart', onTouchStart, { passive: false });

  console.log('Splitter initialized');
}

/**
 * Apply a split position.
 * @param {number} ratio - Editor width as fraction of total (0.0 to 1.0)
 */
function applyPosition(ratio) {
  // Clamp to ensure minimum widths
  const workspaceWidth = workspace.clientWidth - divider.clientWidth;
  const minRatio = MIN_PANEL_WIDTH / workspaceWidth;
  const maxRatio = 1 - minRatio;
  ratio = Math.max(minRatio, Math.min(maxRatio, ratio));

  editorPanel.style.flex = `0 0 ${ratio * 100}%`;
  previewPanel.style.flex = `0 0 ${(1 - ratio) * 100}%`;
}
```

### Key Design Decisions
- **Flexbox-based resizing**: We don't use absolute pixel widths. Instead, we set `flex: 0 0 X%` on each panel. This plays well with the existing flexbox layout from Feature 1.1.
- **Ratio-based storage**: We store the editor's width as a fraction (0.0 to 1.0) of the total workspace width. This means the split position adapts to different browser window sizes.
- **Minimum width constraints**: Neither panel can be smaller than 200px. This prevents the user from accidentally hiding a panel.

---

## Step 2: Implement Mouse Drag Behavior

### What to Do
Handle `mousedown` on the divider, `mousemove` on the document, and `mouseup` to stop.

### Sub-Steps

#### 1.6.2 — Event handlers

```javascript
// src/js/splitter.js (continued)

function onMouseDown(e) {
  e.preventDefault();
  isDragging = true;

  // Add CSS classes for visual feedback
  document.body.classList.add('is-resizing');
  divider.classList.add('divider-active');

  // Listen on document (not divider) so drag continues even if cursor leaves the divider
  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
}

function onMouseMove(e) {
  if (!isDragging) return;

  // Calculate the new editor width ratio
  const workspaceRect = workspace.getBoundingClientRect();
  const dividerWidth = divider.clientWidth;
  const mouseX = e.clientX - workspaceRect.left;
  const availableWidth = workspaceRect.width - dividerWidth;
  const ratio = mouseX / availableWidth;

  applyPosition(ratio);
}

function onMouseUp() {
  if (!isDragging) return;
  isDragging = false;

  // Remove CSS classes
  document.body.classList.remove('is-resizing');
  divider.classList.remove('divider-active');

  // Remove listeners
  document.removeEventListener('mousemove', onMouseMove);
  document.removeEventListener('mouseup', onMouseUp);

  // Save position
  const workspaceWidth = workspace.clientWidth - divider.clientWidth;
  const editorWidth = editorPanel.clientWidth;
  const ratio = editorWidth / workspaceWidth;
  localStorage.setItem(STORAGE_KEY, ratio.toString());

  console.log(`Split position saved: ${(ratio * 100).toFixed(0)}%`);
}
```

#### 1.6.3 — Touch support (basic)

```javascript
function onTouchStart(e) {
  e.preventDefault();
  const touch = e.touches[0];
  onMouseDown({ preventDefault: () => {}, clientX: touch.clientX });

  const onTouchMove = (e) => {
    const touch = e.touches[0];
    onMouseMove({ clientX: touch.clientX });
  };

  const onTouchEnd = () => {
    onMouseUp();
    document.removeEventListener('touchmove', onTouchMove);
    document.removeEventListener('touchend', onTouchEnd);
  };

  document.addEventListener('touchmove', onTouchMove, { passive: false });
  document.addEventListener('touchend', onTouchEnd);
}
```

### Key Points
- **Listen on `document`**: During drag, the cursor may leave the divider element. By listening on `document`, the drag continues even when the cursor is over the editor or preview panel.
- **`e.preventDefault()`**: Prevents text selection during drag.
- **Save on `mouseup`**: Only save to `localStorage` when dragging stops, not during every `mousemove`.

---

## Step 3: CSS for Drag States

### What to Do
Add CSS that improves the drag experience.

### Sub-Steps

#### 1.6.4 — CSS rules

Add to `src/css/style.css`:
```css
/* During resize: prevent interactions with panels */
body.is-resizing {
  cursor: col-resize !important;
  user-select: none;
}

body.is-resizing * {
  cursor: col-resize !important;
  pointer-events: none;
}

body.is-resizing #divider {
  pointer-events: auto;
}

/* Active divider state */
.divider-active {
  background: var(--accent-primary) !important;
}

/* Divider grip indicator (3 dots) */
.divider::after {
  content: '';
  display: block;
  width: 3px;
  height: 30px;
  margin: auto;
  margin-top: calc(50vh - 15px);
  background: repeating-linear-gradient(
    to bottom,
    var(--text-placeholder) 0px,
    var(--text-placeholder) 3px,
    transparent 3px,
    transparent 7px
  );
  border-radius: 2px;
  opacity: 0.5;
  transition: opacity var(--transition-fast);
}

.divider:hover::after {
  opacity: 1;
}
```

### Key Design Decisions
- **`cursor: col-resize !important` on body during drag**: Ensures the resize cursor stays even when the mouse moves over other elements.
- **`pointer-events: none` on all elements during drag**: Prevents the CodeMirror editor and PDF canvases from capturing mouse events during drag. Without this, the cursor would "stick" to the editor when dragging over it.
- **`pointer-events: auto` on divider**: The divider itself still needs to receive events.
- **`user-select: none`**: Prevents text selection in the editor during drag.
- **Grip indicator**: Three small dots on the divider hint that it's draggable.

### Do's
- ✅ Set `cursor: col-resize` on the body during drag
- ✅ Set `pointer-events: none` on all child elements during drag
- ✅ Re-enable pointer events immediately on mouseup
- ✅ Add a visual grip indicator on the divider

### Don'ts
- ❌ Don't use `position: absolute` for the divider — it's a flex item
- ❌ Don't forget to remove the `is-resizing` class on mouseup
- ❌ Don't animate the panel widths during drag (would feel laggy)

### Definition of Done
- [ ] During drag, the cursor is `col-resize` everywhere
- [ ] Text in the editor is not selectable during drag
- [ ] The divider turns purple when active
- [ ] Three small dots appear on the divider as a grip hint

---

## Step 4: Wire in `app.js`

### What to Do
Import and initialize the splitter module.

### Sub-Steps

#### 1.6.5 — Final `app.js`

```javascript
// src/js/app.js (final Phase 1 version)
import { initEditor } from './editor.js';
import { initCompiler } from './compiler.js';
import { initPdfViewer, listenForCompileEvents, setupResizeHandler } from './pdfViewer.js';
import { initSplitter } from './splitter.js';

const PROJECT_PATH = 'sample';
const MAIN_FILE = 'main.tex';

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Pdleaf v0.1.0 — Starting...');

  // 1. Load file content
  let content = '';
  try {
    const response = await fetch(`/api/file?path=${PROJECT_PATH}/${MAIN_FILE}`);
    content = response.ok ? await response.text() : '% Could not load file.\n';
  } catch {
    content = '% Server unavailable.\n';
  }

  // 2. Initialize editor
  initEditor(document.getElementById('editor-container'), content);

  // 3. Initialize compiler (button + shortcuts)
  initCompiler();

  // 4. Initialize PDF viewer
  initPdfViewer(document.getElementById('pdf-container'));
  listenForCompileEvents();
  setupResizeHandler();

  // 5. Initialize splitter (resizable divider)
  initSplitter();

  console.log('Pdleaf: Ready ✅');
});
```

---

## Step 5: Edge Cases

### 5.1 — Window resize
When the browser window is resized, the panels should maintain their ratio. Since we use `flex: 0 0 X%`, the browser handles this automatically. The PDF viewer's ResizeObserver (Feature 1.5) will re-render pages.

### 5.2 — Double-click divider to reset
Optional enhancement: double-clicking the divider resets to 50/50 split.
```javascript
divider.addEventListener('dblclick', () => {
  applyPosition(0.5);
  localStorage.setItem(STORAGE_KEY, '0.5');
  console.log('Split reset to 50/50');
});
```

### 5.3 — Persisted position on reload
When the page reloads, the saved position from `localStorage` should be restored. This is already handled in `initSplitter()`.

### 5.4 — Extreme ratios
If the user somehow sets a ratio outside [0, 1] (e.g., from corrupted localStorage), the `applyPosition()` function clamps it to valid bounds.

### 5.5 — CodeMirror resize
After the divider is dragged, CodeMirror should automatically reflow to the new editor width. CodeMirror 6 handles this natively — it listens for its container's size changes.

---

## Final Acceptance Checklist — Feature 1.6 Complete

| # | Check | Status |
|---|-------|--------|
| 1 | `src/js/splitter.js` exists with `initSplitter()` | ☐ |
| 2 | Divider is visible between editor and preview panels | ☐ |
| 3 | Hovering over divider shows `col-resize` cursor | ☐ |
| 4 | Hovering over divider shows grip indicator (3 dots) | ☐ |
| 5 | Dragging left shrinks editor, grows preview | ☐ |
| 6 | Dragging right grows editor, shrinks preview | ☐ |
| 7 | Minimum width (200px) is enforced on both panels | ☐ |
| 8 | During drag, cursor stays `col-resize` even over panels | ☐ |
| 9 | During drag, text selection is prevented | ☐ |
| 10 | After drag, PDF re-renders to fit new width | ☐ |
| 11 | After drag, CodeMirror reflows to new width | ☐ |
| 12 | Split position is saved to localStorage | ☐ |
| 13 | Reload restores the saved split position | ☐ |
| 14 | Double-click divider resets to 50/50 (if implemented) | ☐ |
| 15 | No JavaScript errors in the console | ☐ |

> **When all checks pass, Feature 1.6 is DONE.**
>
> 🎉 **PHASE 1 IS COMPLETE!** Run the Phase 1 Integration Test Plan (see `phase-1-blueprint.md`) to verify the full end-to-end workflow.
