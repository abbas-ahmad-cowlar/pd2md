# Feature 3.1 — Auto-Compile with Debounce

> **Phase**: 3 | **Feature**: 1 of 13
> **Goal**: Automatically recompile the document after the user stops typing. Configurable delay. Toggle on/off. This is the single most impactful UX feature in the entire application — it makes Pdleaf feel like a live editor.
> **Estimated Effort**: 2–3 hours
> **Dependencies**: Feature 1.4 (compiler module with `runCompile()`), Feature 1.2 (editor with `getEditorView()`).

---

## Overview

Three components:
1. **CodeMirror update listener** — detects when the document text changes
2. **Debounce timer** — waits N seconds after the last keystroke
3. **Auto-compile module** — manages the toggle state, timer, and triggers compilation

### Architecture Decision: Separate Module vs. Inline
Auto-compile is a separate module (`autoCompile.js`) because:
- It needs its own state (enabled/disabled, timer reference, delay setting)
- It bridges two modules (editor → compiler) without coupling them
- It will gain features later (debounce tuning in Settings, Phase 6)

---

## Step 1: Create the Auto-Compile Module

### File: `src/js/autoCompile.js`

```javascript
// src/js/autoCompile.js
import { getEditorView } from './editor.js';
import { runCompile } from './compiler.js';
import { EditorView } from '@codemirror/view';

// State
let enabled = false;
let debounceDelay = 3000; // ms — default 3 seconds
let debounceTimer = null;
let lastDocLength = 0;   // Track document changes

/**
 * Initialize auto-compile.
 * Attaches an update listener to the editor.
 */
export function initAutoCompile() {
  const view = getEditorView();
  if (!view) {
    console.warn('Auto-compile: editor not ready');
    return;
  }

  // Store initial doc length
  lastDocLength = view.state.doc.length;

  console.log(`Auto-compile initialized (delay: ${debounceDelay}ms, default: OFF)`);
}

/**
 * Create the EditorView extension for auto-compile.
 * This must be added to the editor's extensions during initEditor().
 *
 * @returns {Extension} CodeMirror extension
 */
export function autoCompileExtension() {
  return EditorView.updateListener.of((update) => {
    if (!enabled) return;
    if (!update.docChanged) return; // Only trigger on actual text changes

    // Reset the debounce timer
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      console.log('Auto-compile: triggering...');
      runCompile();
    }, debounceDelay);
  });
}

/**
 * Toggle auto-compile on/off.
 * @returns {boolean} New state
 */
export function toggleAutoCompile() {
  enabled = !enabled;
  updateToggleUI(enabled);

  if (!enabled && debounceTimer) {
    clearTimeout(debounceTimer);
    debounceTimer = null;
  }

  console.log(`Auto-compile: ${enabled ? 'ON' : 'OFF'}`);
  return enabled;
}

/**
 * Set the debounce delay.
 * @param {number} ms - Delay in milliseconds (min 500, max 10000)
 */
export function setDebounceDelay(ms) {
  debounceDelay = Math.max(500, Math.min(10000, ms));
  console.log(`Auto-compile delay: ${debounceDelay}ms`);
}

/**
 * Check if auto-compile is enabled.
 */
export function isAutoCompileEnabled() {
  return enabled;
}

/**
 * Update the toolbar toggle button UI.
 */
function updateToggleUI(isOn) {
  const btn = document.getElementById('btn-auto-compile');
  if (!btn) return;

  if (isOn) {
    btn.classList.add('btn-active');
    btn.title = 'Auto-compile: ON (click to disable)';
  } else {
    btn.classList.remove('btn-active');
    btn.title = 'Auto-compile: OFF (click to enable)';
  }
}
```

### Key Design Decisions

#### Why `EditorView.updateListener` not `onChange`?
- CodeMirror 6 doesn't have a simple `onChange` event. `updateListener` receives all state updates.
- We check `update.docChanged` to filter out cursor movements, selection changes, etc.
- Only actual text changes trigger the timer.

#### Why 3-second default delay?
- Overleaf uses ~2-3 seconds. It's a good balance between responsiveness and not wasting CPU.
- Too short (< 1s) = compiles on every pause, wastes resources
- Too long (> 5s) = feels sluggish, user might manually compile anyway
- The user can tune this in Phase 6 Settings.

#### Why default OFF?
- Auto-compile can be distracting for new users who aren't used to it
- It consumes CPU/disk on every pause in typing
- The user should opt in. In Phase 6 Settings, we can remember their preference.

#### Extension vs. Listener Pattern
The `autoCompileExtension()` returns a CodeMirror extension that must be added during `initEditor()`. This is cleaner than manually attaching event listeners after initialization.

```javascript
// In editor.js — add to extensions:
import { autoCompileExtension } from './autoCompile.js';

// In the extensions array:
autoCompileExtension(),
```

---

## Step 2: Add the Toggle Button to the Toolbar

### HTML
Add to `src/index.html`, in the toolbar section:
```html
<button id="btn-auto-compile" class="btn btn-toolbar" title="Auto-compile: OFF">
  <span class="btn-icon">↻</span>
  <span class="btn-text">Auto</span>
</button>
```

### CSS
```css
/* Active state for toggle buttons */
.btn-active {
  background: var(--accent-primary) !important;
  color: white !important;
}

.btn-active .btn-icon {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

When auto-compile is ON, the button is purple with a spinning icon. When OFF, it's the default toolbar style.

---

## Step 3: Wire in `app.js`

```javascript
import { initAutoCompile, toggleAutoCompile } from './autoCompile.js';

// After editor and compiler init:
initAutoCompile();
document.getElementById('btn-auto-compile').addEventListener('click', toggleAutoCompile);
```

---

## Edge Cases

### 4.1 — Auto-compile while already compiling
The `runCompile()` function from Phase 1 has an `isCompiling` guard. If auto-compile fires while a compilation is in progress, it's silently skipped. This is correct — the user's current compilation takes priority.

### 4.2 — Rapid typing
Each keystroke resets the timer. Only when the user pauses for `debounceDelay` ms does compilation trigger. Typing 100 words straight → no compile until a 3-second pause.

### 4.3 — Auto-compile + Ctrl+S manual compile
If the user presses `Ctrl+S` during the debounce timer, the manual compile runs immediately and the debounce timer is effectively superseded. The `isCompiling` guard prevents double compilation.

### 4.4 — Empty document
If the user deletes everything, the auto-compile will fire and compile an empty document. This will produce a LaTeX error. That's expected behavior.

### 4.5 — Large document (slow compilation)
If compilation takes 10s and the debounce is 3s, the user might type → wait 3s → compile starts → type more → wait 3s → compile queued but blocked by `isCompiling`. The second compile is lost. This is acceptable for Phase 3. Phase 6+ could add a "compile pending" state.

---

## Do's & Don'ts

### Do's
- ✅ Only trigger on `docChanged`, not cursor moves
- ✅ Reset timer on every keystroke (proper debounce)
- ✅ Respect the `isCompiling` guard
- ✅ Show visual feedback (spinning icon when ON)
- ✅ Default to OFF

### Don'ts
- ❌ Don't compile on every keystroke — always debounce
- ❌ Don't show the full "Compiling..." button animation for auto-compiles — use a subtle indicator
- ❌ Don't persist the toggle state yet — that's Phase 6 Settings
- ❌ Don't queue missed compilations — just skip if one is running

---

## Final Acceptance Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | Auto-compile toggle button exists in toolbar | ☐ |
| 2 | Default state: OFF | ☐ |
| 3 | Clicking toggle → ON → button turns purple with spinning icon | ☐ |
| 4 | Type text → wait 3s → compilation fires automatically | ☐ |
| 5 | Rapid typing → only one compile after the pause | ☐ |
| 6 | `Ctrl+S` during debounce → manual compile fires immediately | ☐ |
| 7 | Auto-compile while already compiling → silently skipped | ☐ |
| 8 | Toggle OFF → no more auto-compiles | ☐ |
| 9 | Toggle OFF → pending debounce timer cancelled | ☐ |
| 10 | Console logs "Auto-compile: triggering..." on each auto-compile | ☐ |
| 11 | No duplicate compilations | ☐ |

> **Done → Proceed to Feature 3.2.**
