# Feature 2.8 — Vim / Emacs Keybinding Modes

> **Phase**: 2 | **Feature**: 8 of 9
> **Goal**: Allow switching between Default, Vim, and Emacs keybinding modes.
> **Estimated Effort**: 1–2 hours
> **Dependencies**: Feature 2.7 (Compartment pattern established).

---

## Overview

Uses the same Compartment pattern from Feature 2.7 to swap keybinding modes at runtime. No UI for toggling yet — that comes with the Settings panel (Phase 6). For now, expose a function.

---

## Step 1: Install Packages

```bash
npm install @replit/codemirror-vim
npm install @replit/codemirror-emacs
```

> **Research step**: Verify these are the correct, maintained packages for CM6. Check npm for alternatives if these are unmaintained.

---

## Step 2: Create Keybinding Compartment

In `editor.js`:
```javascript
import { Compartment } from '@codemirror/state';

const keybindingCompartment = new Compartment();
let currentKeybindingMode = 'default';

// In EditorState.create extensions:
keybindingCompartment.of([]), // default: no special keybindings
```

---

## Step 3: Export Mode Switching Function

```javascript
export async function setKeybindingMode(mode) {
  if (!editorView) return;
  currentKeybindingMode = mode;

  let extension = [];

  switch (mode) {
    case 'vim': {
      const { vim } = await import('@replit/codemirror-vim');
      extension = vim();
      break;
    }
    case 'emacs': {
      const { emacs } = await import('@replit/codemirror-emacs');
      extension = emacs();
      break;
    }
    case 'default':
    default:
      extension = [];
      break;
  }

  editorView.dispatch({
    effects: keybindingCompartment.reconfigure(extension),
  });

  console.log(`Keybinding mode: ${mode}`);
}

export function getKeybindingMode() {
  return currentKeybindingMode;
}
```

### Key Points
- **Dynamic import (`await import(...)`)**: The vim/emacs packages are only loaded when needed. No extra bundle size for users who don't use them.
- **Compartment reconfigure**: Swaps the extension in-place without recreating the editor.
- **Content preserved**: Switching modes doesn't lose any editor text.

---

## Step 4: Vim Mode Indicator (Optional)

The `@replit/codemirror-vim` package may include a status bar showing `-- NORMAL --` / `-- INSERT --`. If not, add one:

```javascript
// If vim provides a status panel, it will appear automatically.
// If not, listen for vim mode changes and update #file-status:
// document.getElementById('file-status').textContent = 'VIM: NORMAL';
```

---

## Do's & Don'ts

### Do's
- ✅ Use dynamic imports to avoid bloating the default bundle
- ✅ Preserve editor content when switching modes
- ✅ Fall back to default if a package fails to load

### Don'ts
- ❌ Don't add a UI toggle yet — that's Phase 6 Settings panel
- ❌ Don't make vim/emacs the default — always start in default mode
- ❌ Don't break `Ctrl+S` (compile) in vim mode — ensure it still works

---

## Final Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | `setKeybindingMode('vim')` enables vim bindings | ☐ |
| 2 | In vim mode: `i` enters insert, `Escape` exits, `dd` deletes line | ☐ |
| 3 | `setKeybindingMode('emacs')` enables emacs bindings | ☐ |
| 4 | `setKeybindingMode('default')` restores normal editing | ☐ |
| 5 | Switching modes preserves editor content | ☐ |
| 6 | `Ctrl+S` still compiles in all modes | ☐ |
| 7 | Packages are lazy-loaded (not in initial bundle) | ☐ |

> **Done → Proceed to Feature 2.9.**
