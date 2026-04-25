# Feature 2.9 — Go-to-Line Dialog

> **Phase**: 2 | **Feature**: 9 of 9
> **Goal**: Provide a `Ctrl+G` shortcut that opens a lightweight dialog where the user types a line number, and the editor scrolls to and highlights that line. This is a common IDE feature that makes navigating long LaTeX documents much faster.
> **Estimated Effort**: 1–2 hours
> **Dependencies**: Feature 1.2 (editor module with `getEditorView()`).

---

## Overview

This feature has three components:
1. **HTML dialog markup** — a small floating panel that appears near the top of the editor
2. **CSS styling** — dark-themed, matches the rest of the app
3. **JavaScript logic** — open/close behavior, input validation, cursor dispatch

There are two approaches to building this:

**Option A — DOM-based dialog** (recommended):
- Create a `<div>` in `index.html` (or dynamically)
- Show/hide with CSS classes
- Positioned absolutely over the editor
- Full control over styling and behavior

**Option B — CodeMirror panel API**:
- Use `showPanel` from `@codemirror/view` to create an inline panel
- More "CodeMirror native" but less flexibility

We'll use **Option A** for full styling control and consistency with future dialogs (find/replace, settings).

---

## Step 1: Create the Dialog HTML

### What to Do
Add the Go-to-Line dialog markup to `src/index.html`.

### Sub-Steps

#### 2.9.1 — Dialog markup

Add inside `<main id="workspace">`, after the editor panel:

```html
<!-- Go-to-Line Dialog -->
<div id="goto-line-dialog" class="dialog-overlay" style="display: none;">
  <div class="dialog-box dialog-goto-line">
    <label for="goto-line-input" class="dialog-label">Go to Line:</label>
    <input
      type="number"
      id="goto-line-input"
      class="dialog-input"
      min="1"
      placeholder="Line number"
      autocomplete="off"
    />
    <button id="goto-line-submit" class="btn btn-primary btn-sm">Go</button>
    <button id="goto-line-close" class="btn btn-ghost btn-sm">✕</button>
    <span id="goto-line-hint" class="dialog-hint"></span>
  </div>
</div>
```

### Key Design Decisions
- **`type="number"`**: Mobile keyboards show a numpad; desktop users can use arrow keys to increment/decrement.
- **`style="display: none"`**: Hidden by default. Shown via JS.
- **Unique IDs**: Every element has an `id` for easy JS targeting and testing.
- **`autocomplete="off"`**: Don't show browser autocomplete suggestions for line numbers.
- **Hint span**: Shows "Line X of Y" context (e.g., "Line 42 of 156").

---

## Step 2: Style the Dialog

### What to Do
Add CSS for the dialog that matches the dark theme and positions it as a floating panel.

### Sub-Steps

#### 2.9.2 — CSS rules

Add to `src/css/style.css`:

```css
/* ═══════════════════════════════════════════════
   Dialog System (reusable for future dialogs)
   ═══════════════════════════════════════════════ */

/* Overlay — positions the dialog relative to the workspace */
.dialog-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  justify-content: center;
  padding-top: 8px;
  pointer-events: none; /* Allow clicks through the overlay */
}

/* The dialog box itself */
.dialog-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg-toolbar);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  pointer-events: auto; /* Dialog itself is clickable */
  animation: dialog-slide-down 150ms ease-out;
}

@keyframes dialog-slide-down {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Dialog label */
.dialog-label {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}

/* Dialog input */
.dialog-input {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--font-size-md);
  padding: 4px 8px;
  width: 100px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.dialog-input:focus {
  border-color: var(--accent-primary);
}

/* Remove number input spin buttons */
.dialog-input[type="number"]::-webkit-inner-spin-button,
.dialog-input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.dialog-input[type="number"] {
  -moz-appearance: textfield;
}

/* Small buttons for dialogs */
.btn-sm {
  padding: 3px 10px;
  font-size: var(--font-size-sm);
}

/* Ghost button (close X) */
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  padding: 3px 6px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.btn-ghost:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

/* Hint text */
.dialog-hint {
  color: var(--text-placeholder);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}
```

### Key Design Decisions
- **Reusable dialog system**: The `.dialog-overlay`, `.dialog-box`, `.dialog-input` classes are generic. Future dialogs (Find/Replace in Phase 5, Settings in Phase 6) will reuse these exact styles.
- **`pointer-events: none` on overlay**: The overlay covers the workspace but doesn't block clicks. Only the dialog box itself (`pointer-events: auto`) is interactive. This means the user can still click in the editor while the dialog is open.
- **Slide-down animation**: A subtle 150ms animation makes the dialog feel polished.
- **No spin buttons**: The number input's default up/down arrows are removed for a cleaner look.
- **`position: absolute`**: The dialog is inside `#workspace` which has `position: relative` (or needs it added). It floats above the editor panel.

### CSS Prerequisite
Make sure `#workspace` has `position: relative`:
```css
#workspace {
  /* ... existing styles ... */
  position: relative; /* Needed for absolute-positioned dialog */
}
```

---

## Step 3: JavaScript Logic

### What to Do
Create the Go-to-Line dialog controller — open/close behavior, input validation, line jumping.

### Sub-Steps

#### 2.9.3 — Create the dialog module

This can go in a new `src/js/gotoLine.js` file, or inline in `editor.js`. A separate file is cleaner since it manages DOM elements outside the editor.

```javascript
// src/js/gotoLine.js
import { getEditorView } from './editor.js';

let dialog = null;
let input = null;
let hint = null;
let isOpen = false;

/**
 * Initialize the Go-to-Line dialog.
 * Call once after DOM is ready.
 */
export function initGotoLine() {
  dialog = document.getElementById('goto-line-dialog');
  input = document.getElementById('goto-line-input');
  hint = document.getElementById('goto-line-hint');

  const submitBtn = document.getElementById('goto-line-submit');
  const closeBtn = document.getElementById('goto-line-close');

  if (!dialog || !input) {
    console.error('Go-to-Line dialog elements not found');
    return;
  }

  // Submit on button click
  submitBtn.addEventListener('click', handleSubmit);

  // Submit on Enter key
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      closeDialog();
    }
  });

  // Close on X button
  closeBtn.addEventListener('click', closeDialog);

  // Update hint as user types
  input.addEventListener('input', updateHint);

  // Register global shortcut
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
      e.preventDefault();
      if (isOpen) {
        closeDialog();
      } else {
        openDialog();
      }
    }
  });

  console.log('Go-to-Line dialog initialized (Ctrl+G)');
}

/**
 * Open the dialog.
 */
function openDialog() {
  const view = getEditorView();
  if (!view) return;

  // Show total line count in hint
  const totalLines = view.state.doc.lines;
  hint.textContent = `of ${totalLines}`;

  // Pre-fill with current cursor line
  const currentLine = view.state.doc.lineAt(view.state.selection.main.head).number;
  input.value = currentLine;

  // Show dialog
  dialog.style.display = 'flex';
  isOpen = true;

  // Focus and select input text
  requestAnimationFrame(() => {
    input.focus();
    input.select();
  });
}

/**
 * Close the dialog and return focus to the editor.
 */
function closeDialog() {
  dialog.style.display = 'none';
  isOpen = false;
  input.value = '';

  // Return focus to editor
  const view = getEditorView();
  if (view) view.focus();
}

/**
 * Handle line number submission.
 */
function handleSubmit() {
  const view = getEditorView();
  if (!view) return;

  const lineNum = parseInt(input.value, 10);
  if (isNaN(lineNum) || lineNum < 1) {
    input.classList.add('input-error');
    setTimeout(() => input.classList.remove('input-error'), 500);
    return;
  }

  // Clamp to valid range
  const totalLines = view.state.doc.lines;
  const targetLine = Math.min(lineNum, totalLines);

  // Get the line's position
  const line = view.state.doc.line(targetLine);

  // Move cursor to start of line and scroll into view
  view.dispatch({
    selection: { anchor: line.from },
    effects: view.scrollIntoView(line.from, { y: 'center' }),
  });

  // Temporarily highlight the line (via CSS — see below)
  highlightTargetLine(view, line);

  closeDialog();
}

/**
 * Flash-highlight the target line for visual feedback.
 */
function highlightTargetLine(view, line) {
  // Add a temporary CSS class to the line
  // Option: use CodeMirror decorations (more proper)
  // Simple option: use a brief scroll + rely on active line highlighting
  // The active line highlight from Phase 1 already shows which line the cursor is on.
  // For extra emphasis, we could add a brief yellow flash — but that's optional polish.
}

/**
 * Update the hint text as the user types.
 */
function updateHint() {
  const view = getEditorView();
  if (!view) return;

  const totalLines = view.state.doc.lines;
  const lineNum = parseInt(input.value, 10);

  if (isNaN(lineNum) || lineNum < 1) {
    hint.textContent = `of ${totalLines}`;
  } else if (lineNum > totalLines) {
    hint.textContent = `of ${totalLines} (clamped)`;
  } else {
    hint.textContent = `of ${totalLines}`;
  }
}
```

### Key Design Decisions
- **Pre-fills current line**: When the dialog opens, it shows the current cursor line number. This gives context and allows easy relative jumping.
- **`requestAnimationFrame` for focus**: Ensures the dialog is visible in the DOM before focusing the input. Without this, some browsers ignore the `focus()` call.
- **Clamped range**: Typing `99999` in a 156-line document jumps to line 156 instead of throwing an error.
- **Return focus to editor**: After closing, focus goes back to the CodeMirror editor so the user can keep typing immediately.
- **`Ctrl+G` toggles**: If the dialog is already open, `Ctrl+G` closes it. This feels natural.
- **`Escape` closes**: Standard dialog behavior.

#### 2.9.4 — Error CSS for invalid input

Add to `src/css/style.css`:
```css
/* Input error flash */
.dialog-input.input-error {
  border-color: var(--accent-error);
  animation: shake 300ms ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  50% { transform: translateX(4px); }
  75% { transform: translateX(-4px); }
}
```

---

## Step 4: Wire in `app.js`

### What to Do
Import and initialize the Go-to-Line dialog.

#### 2.9.5 — Update `app.js`

```javascript
import { initGotoLine } from './gotoLine.js';

// In the DOMContentLoaded handler, after other initializations:
initGotoLine();
```

### Definition of Done
- [ ] `Ctrl+G` opens the dialog
- [ ] Dialog initializes without errors on page load
- [ ] Closing returns focus to the editor

---

## Edge Cases

### 5.1 — Non-numeric input
The `type="number"` input prevents most non-numeric input. But pasting text or entering `e` (exponential notation) could happen. `parseInt(input.value, 10)` handles this — `NaN` triggers the error flash.

### 5.2 — Line number 0 or negative
Clamped to 1. The `min="1"` attribute prevents typing 0 in most browsers, but we also check in JS.

### 5.3 — Line number beyond document length
Clamped to the last line. No error — just goes to the end.

### 5.4 — Empty document
An empty document has 1 line (CodeMirror counts it). Go-to-line 1 works. Any other number is clamped to 1.

### 5.5 — Dialog open + Ctrl+S
If the dialog is open and the user presses `Ctrl+S` to compile, the compile should still work. The dialog doesn't capture all keyboard events — only Enter, Escape, and Ctrl+G.

### 5.6 — Dialog open + click in editor
The dialog stays open (pointer-events: none on overlay allows editor clicks). The user can click in the editor, then come back to the dialog. Closing explicitly required via Escape, X button, or Ctrl+G.

---

## Do's & Don'ts

### Do's
- ✅ Pre-fill with current line number
- ✅ Select the input text on open (easy to type over)
- ✅ Return focus to editor on close
- ✅ Clamp out-of-range values instead of showing errors
- ✅ Use `requestAnimationFrame` for reliable input focus
- ✅ Make the dialog reusable (CSS classes are generic)

### Don'ts
- ❌ Don't show a full-screen modal overlay — this is a lightweight flyout
- ❌ Don't block editor interaction while the dialog is open
- ❌ Don't leave the dialog open after navigating — close on submit
- ❌ Don't add "go to column" — just line number for Phase 2

---

## Final Acceptance Checklist — Feature 2.9 Complete

| # | Check | Status |
|---|-------|--------|
| 1 | `Ctrl+G` opens the Go-to-Line dialog | ☐ |
| 2 | Dialog appears centered near the top of the workspace | ☐ |
| 3 | Dialog shows "Go to Line:" label with an input field | ☐ |
| 4 | Input is pre-filled with the current cursor line number | ☐ |
| 5 | Input is focused and text is selected on open | ☐ |
| 6 | Hint shows "of N" (total line count) | ☐ |
| 7 | Typing `42` + Enter → cursor jumps to line 42 | ☐ |
| 8 | Line 42 is scrolled into view (centered) | ☐ |
| 9 | Typing `99999` → jumps to last line (clamped) | ☐ |
| 10 | Invalid input → input shakes with red border | ☐ |
| 11 | Pressing Escape closes the dialog | ☐ |
| 12 | Clicking X closes the dialog | ☐ |
| 13 | `Ctrl+G` while open → closes the dialog | ☐ |
| 14 | After close, editor has focus (can type immediately) | ☐ |
| 15 | Dialog slide-down animation plays on open | ☐ |
| 16 | Dialog matches the dark theme | ☐ |

> **When all 16 checks pass, Feature 2.9 is DONE.**
>
> 🎉 **PHASE 2 IS COMPLETE!** Run the Phase 2 Integration Test Plan (see `phase-2-blueprint.md`) to verify all editor enhancements work together.
