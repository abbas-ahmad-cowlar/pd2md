# Feature 2.7 — Word Wrap Toggle

> **Phase**: 2 | **Feature**: 7 of 9
> **Goal**: Toggle soft line wrapping on/off with `Alt+Z`. Introduces the **Compartment** pattern used again in Feature 2.8.
> **Estimated Effort**: 1 hour
> **Dependencies**: Feature 1.2 (editor module).

---

## Overview

This feature introduces CodeMirror **Compartments** — dynamic extension slots that can be reconfigured at runtime without recreating the editor. This same pattern is used for keybinding modes (Feature 2.8) and will be used extensively in Phase 6 (Settings).

---

## Implementation

### Step 1: Create the Compartment

In `editor.js`:
```javascript
import { Compartment } from '@codemirror/state';

const lineWrapCompartment = new Compartment();
let wordWrapEnabled = true; // track state

// In EditorState.create extensions:
lineWrapCompartment.of(EditorView.lineWrapping), // default: ON
```

### Step 2: Export Toggle Function

```javascript
export function toggleWordWrap() {
  if (!editorView) return;
  wordWrapEnabled = !wordWrapEnabled;
  editorView.dispatch({
    effects: lineWrapCompartment.reconfigure(
      wordWrapEnabled ? EditorView.lineWrapping : []
    ),
  });
  console.log(`Word wrap: ${wordWrapEnabled ? 'ON' : 'OFF'}`);
  return wordWrapEnabled;
}

export function isWordWrapEnabled() {
  return wordWrapEnabled;
}
```

### Step 3: Register Keyboard Shortcut

```javascript
// In keymap:
{ key: 'Alt-z', run: () => { toggleWordWrap(); return true; } },
```

### Step 4: Optional Status Bar Indicator

Update the status bar to show wrap state:
```javascript
// In app.js or a UI helper:
document.getElementById('file-status').textContent = 
  wordWrapEnabled ? 'Wrap: On' : 'Wrap: Off';
```

---

## Final Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | Default state: word wrap ON (lines wrap at panel edge) | ☐ |
| 2 | `Alt+Z` toggles to OFF → long lines extend with horizontal scroll | ☐ |
| 3 | `Alt+Z` again → wrapping restored | ☐ |
| 4 | Editor content is preserved during toggle | ☐ |
| 5 | Console logs the new state | ☐ |

> **Done → Proceed to Feature 2.8.**
