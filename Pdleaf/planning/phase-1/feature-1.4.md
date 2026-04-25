# Feature 1.4 — Manual Compile Button

> **Phase**: 1 | **Feature**: 4 of 6
> **Goal**: Wire the "Compile" button in the toolbar to save the current editor content, trigger the backend compilation, show loading/success/error states, and notify the PDF viewer to reload. When done, clicking "Compile" or pressing `Ctrl+S` should save, compile, and update the PDF.
> **Estimated Effort**: 2–4 hours
> **Dependencies**: Feature 1.2 (editor with `getContent()` and `saveCurrentFile()`), Feature 1.3 (compile endpoint).

---

## Overview

This feature is the glue between the editor and the compilation backend. We are:
1. Creating the `compiler.js` frontend module
2. Implementing the save → compile → notify pipeline
3. Adding loading/success/error states to the compile button
4. Registering keyboard shortcuts (`Ctrl+S`, `Ctrl+Enter`)
5. Preventing double-compilation with a guard
6. Dispatching events so the PDF viewer (Feature 1.5) can react

**What this feature does NOT include**: Auto-compile on edit (Phase 3), error log panel (Phase 3), compilation settings (Phase 6).

---

## Step 1: Create the Compiler Module

### What to Do
Build `src/js/compiler.js` — the module that handles the entire compile workflow.

### Sub-Steps

#### 1.4.1 — Module structure

```javascript
// src/js/compiler.js
import { saveCurrentFile, getContent } from './editor.js';

// State
let isCompiling = false;

// Configuration — hardcoded for Phase 1
const PROJECT_PATH = 'sample';
const MAIN_FILE = 'main.tex';

/**
 * Run the full compile pipeline: save → compile → notify.
 * @returns {Promise<{success: boolean, pdfUrl: string|null, duration: number}>}
 */
export async function runCompile() {
  if (isCompiling) {
    console.log('Compilation already in progress — skipping');
    return { success: false, pdfUrl: null, duration: 0 };
  }

  isCompiling = true;
  updateUI('compiling');

  try {
    // Step 1: Save the file to disk
    const saved = await saveCurrentFile();
    if (!saved) {
      updateUI('error', 'Save failed');
      isCompiling = false;
      return { success: false, pdfUrl: null, duration: 0 };
    }

    // Step 2: Trigger compilation
    const response = await fetch('/api/compile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        projectPath: PROJECT_PATH,
        mainFile: MAIN_FILE,
      }),
    });

    const result = await response.json();

    if (result.success) {
      updateUI('success', `Compiled in ${result.duration}s`);
      // Notify the PDF viewer to reload
      document.dispatchEvent(new CustomEvent('compile-success', {
        detail: { pdfUrl: result.pdfUrl, duration: result.duration },
      }));
    } else {
      updateUI('error', result.error || 'Compilation failed');
      document.dispatchEvent(new CustomEvent('compile-error', {
        detail: { error: result.error, log: result.log },
      }));
    }

    return {
      success: result.success,
      pdfUrl: result.pdfUrl,
      duration: result.duration,
    };

  } catch (err) {
    console.error('Compile error:', err);
    updateUI('error', 'Network error');
    return { success: false, pdfUrl: null, duration: 0 };
  } finally {
    isCompiling = false;
  }
}
```

### Key Design Decisions
- **`isCompiling` guard**: Module-level boolean prevents overlapping compilations. Even if the user clicks rapidly or hits Ctrl+S multiple times, only one compilation runs.
- **CustomEvent dispatching**: We use `document.dispatchEvent()` to decouple the compiler from the PDF viewer. The PDF viewer listens for `compile-success` — the compiler doesn't need to know about the viewer.
- **Structured return value**: `runCompile()` returns `{ success, pdfUrl, duration }` — useful for testing and chaining.
- **`finally` block**: Always resets `isCompiling`, even if an error occurs.

---

## Step 2: Implement Button UI States

### What to Do
Create the `updateUI()` function that changes the compile button's appearance based on the current state.

### Sub-Steps

#### 1.4.2 — UI state management

```javascript
// src/js/compiler.js (continued)

// Timeout reference for clearing status messages
let statusTimeout = null;

/**
 * Update the compile button and status text.
 * @param {'idle'|'compiling'|'success'|'error'} state
 * @param {string} message - Optional status message
 */
function updateUI(state, message = '') {
  const btn = document.getElementById('btn-compile');
  const btnIcon = btn.querySelector('.btn-icon');
  const btnText = btn.querySelector('.btn-text');
  const status = document.getElementById('compile-status');

  // Clear any pending status timeout
  if (statusTimeout) clearTimeout(statusTimeout);

  switch (state) {
    case 'compiling':
      btn.disabled = true;
      btnIcon.textContent = '⟳';      // Spinning/loading indicator
      btnText.textContent = 'Compiling...';
      btn.classList.remove('btn-success', 'btn-error');
      btn.classList.add('btn-compiling');
      status.textContent = '';
      break;

    case 'success':
      btn.disabled = false;
      btnIcon.textContent = '✓';
      btnText.textContent = 'Compiled';
      btn.classList.remove('btn-compiling', 'btn-error');
      btn.classList.add('btn-success');
      status.textContent = message;

      // Reset to idle after 3 seconds
      statusTimeout = setTimeout(() => updateUI('idle'), 3000);
      break;

    case 'error':
      btn.disabled = false;
      btnIcon.textContent = '✗';
      btnText.textContent = 'Error';
      btn.classList.remove('btn-compiling', 'btn-success');
      btn.classList.add('btn-error');
      status.textContent = message;

      // Reset to idle after 5 seconds
      statusTimeout = setTimeout(() => updateUI('idle'), 5000);
      break;

    case 'idle':
    default:
      btn.disabled = false;
      btnIcon.textContent = '▶';
      btnText.textContent = 'Compile';
      btn.classList.remove('btn-compiling', 'btn-success', 'btn-error');
      status.textContent = '';
      break;
  }
}
```

#### 1.4.3 — CSS for button states

Add to `src/css/style.css`:
```css
/* Compile button states */
.btn-compiling {
  background: var(--accent-warning) !important;
  color: #1a1a2e !important;
  animation: pulse 1s ease-in-out infinite;
}

.btn-success {
  background: var(--accent-success) !important;
  color: #1a1a2e !important;
}

.btn-error {
  background: var(--accent-error) !important;
  color: white !important;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

### UI State Flow
```
[idle] ──click──→ [compiling] ──success──→ [success] ──3s──→ [idle]
                      │                         
                      └──failure──→ [error] ──5s──→ [idle]
```

### Definition of Done
- [ ] Button shows "▶ Compile" in idle state (purple)
- [ ] Button shows "⟳ Compiling..." in compiling state (yellow, pulsing)
- [ ] Button shows "✓ Compiled" in success state (green) with duration in status text
- [ ] Button shows "✗ Error" in error state (red) with error message in status text
- [ ] Button is disabled during compilation (can't click)
- [ ] After 3s (success) or 5s (error), button resets to idle

---

## Step 3: Register Keyboard Shortcuts

### What to Do
Register `Ctrl+S` and `Ctrl+Enter` as keyboard shortcuts that trigger `runCompile()`.

### Sub-Steps

#### 1.4.4 — Keyboard shortcut registration

```javascript
// src/js/compiler.js (continued)

/**
 * Initialize the compiler: attach button click and keyboard shortcuts.
 */
export function initCompiler() {
  // Button click
  const btn = document.getElementById('btn-compile');
  btn.addEventListener('click', () => runCompile());

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl+S — Save and compile
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault(); // Prevent browser's "Save Page" dialog
      runCompile();
    }

    // Ctrl+Enter — Compile
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      runCompile();
    }
  });

  console.log('Compiler initialized: Ctrl+S / Ctrl+Enter to compile');
}
```

### Key Points
- **`e.preventDefault()`**: Essential for `Ctrl+S` — without it, the browser opens the "Save Page" dialog.
- **`e.metaKey`**: Handles `Cmd+S` on macOS (future-proofing).
- **Registered on `document`**: Captures the shortcut regardless of which element has focus (even when the cursor is in the CodeMirror editor).

### Do's
- ✅ Always call `e.preventDefault()` for browser-default shortcuts
- ✅ Support both `Ctrl` (Windows/Linux) and `Meta/Cmd` (macOS)
- ✅ Log that shortcuts are registered (debugging help)

### Don'ts
- ❌ Don't register shortcuts inside CodeMirror's keymap — use `document.addEventListener` for global shortcuts
- ❌ Don't add more shortcuts here — `Ctrl+F` (search), `Ctrl+/` (comment) are Phase 2+

### Definition of Done
- [ ] `Ctrl+S` triggers compilation (doesn't open browser save dialog)
- [ ] `Ctrl+Enter` triggers compilation
- [ ] Both shortcuts work whether the editor or preview panel has focus

### How to Test
1. Click in the editor → type something → press `Ctrl+S`
2. Button should show "Compiling..." then "Compiled in X.Xs"
3. Click in the preview panel → press `Ctrl+Enter` → should also compile
4. Check that the browser's "Save Page As" dialog does NOT appear

---

## Step 4: Wire Everything in `app.js`

### What to Do
Update `app.js` to import and initialize the compiler module.

### Sub-Steps

#### 1.4.5 — Update `app.js`

```javascript
// src/js/app.js (updated)
import { initEditor } from './editor.js';
import { initCompiler } from './compiler.js';

const PROJECT_PATH = 'sample';
const MAIN_FILE = 'main.tex';

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Pdleaf v0.1.0 — Starting...');

  // 1. Initialize editor
  const container = document.getElementById('editor-container');
  let content = '';
  try {
    const response = await fetch(`/api/file?path=${PROJECT_PATH}/${MAIN_FILE}`);
    if (response.ok) {
      content = await response.text();
    } else {
      content = '% Could not load file.\n';
    }
  } catch {
    content = '% Server unavailable.\n';
  }
  initEditor(container, content);

  // 2. Initialize compiler (button + shortcuts)
  initCompiler();

  // 3. PDF viewer will be initialized in Feature 1.5
  // ...

  console.log('Pdleaf: Ready ✅');
});
```

### Definition of Done
- [ ] `app.js` imports and calls `initCompiler()`
- [ ] The compile button works after page load
- [ ] Keyboard shortcuts work after page load

---

## Step 5: Edge Cases & Error Handling

### What to Handle

#### 5.1 — Rapid clicking / double compilation
The `isCompiling` guard prevents this. Test by clicking "Compile" 5 times rapidly.

#### 5.2 — Backend is down
The `fetch()` call will throw a network error. The `catch` block in `runCompile()` handles this and shows "Network error" in the button.

#### 5.3 — Empty editor
If the editor is empty, the file is still saved (empty file) and compilation will fail with a LaTeX error. This is the expected behavior — the error state will show.

#### 5.4 — Very fast compilation
If compilation takes < 100ms, the "Compiling..." state might flash too quickly to see. This is acceptable — the success state will show immediately.

#### 5.5 — Compilation timeout
If the backend times out (60s), it returns `{ success: false, timedOut: true }`. The error state shows "Compilation timed out after 60s".

---

## Final Acceptance Checklist — Feature 1.4 Complete

| # | Check | Status |
|---|-------|--------|
| 1 | `src/js/compiler.js` exists with `runCompile()` and `initCompiler()` | ☐ |
| 2 | Clicking "Compile" saves the file then triggers compilation | ☐ |
| 3 | Button shows "⟳ Compiling..." with yellow pulsing during compilation | ☐ |
| 4 | Button shows "✓ Compiled" with green + duration on success | ☐ |
| 5 | Button shows "✗ Error" with red + error message on failure | ☐ |
| 6 | Button is disabled during compilation (can't double-click) | ☐ |
| 7 | Button resets to "▶ Compile" after 3s (success) or 5s (error) | ☐ |
| 8 | `Ctrl+S` triggers compile (browser save dialog blocked) | ☐ |
| 9 | `Ctrl+Enter` triggers compile | ☐ |
| 10 | `compile-success` event is dispatched with `{ pdfUrl, duration }` | ☐ |
| 11 | `compile-error` event is dispatched with `{ error, log }` | ☐ |
| 12 | Network errors show "Network error" (no crash) | ☐ |
| 13 | 5 rapid clicks only trigger one compilation | ☐ |
| 14 | No JavaScript errors in the console | ☐ |

> **When all 14 checks pass, Feature 1.4 is DONE. Proceed to Feature 1.5 (PDF Viewer).**
