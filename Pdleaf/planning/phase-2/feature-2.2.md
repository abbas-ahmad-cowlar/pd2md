# Feature 2.2 — Auto-Close Brackets & `\begin/\end` Pairs

> **Phase**: 2 | **Feature**: 2 of 9
> **Goal**: Auto-insert matching delimiters (`{→}`, `$→$`) and auto-insert `\end{env}` when `\begin{env}` + Enter is typed.
> **Estimated Effort**: 2–3 hours
> **Dependencies**: Feature 1.2 (editor module).

---

## Overview

Two parts:
1. **Built-in bracket closing** — `closeBrackets()` from CodeMirror handles `{}`, `()`, `[]`, `$$`
2. **Custom `\begin/\end` handler** — needs a custom `inputHandler` or Enter-key interceptor

---

## Step 1: Enable `closeBrackets()`

Add to `editor.js`:
```javascript
import { closeBrackets, closeBracketsKeymap } from '@codemirror/autocomplete';

// In extensions:
closeBrackets(),
keymap.of([...closeBracketsKeymap]),
```

### Configure bracket pairs
```javascript
// Override default config if needed:
closeBrackets({
  brackets: ['{', '(', '[', '$'],
  // Don't auto-close single/double quotes — LaTeX handles them differently
}),
```

### Behaviors this enables:
- Type `{` → inserts `{}`, cursor between
- Type `(` → inserts `()`, cursor between
- Type `$` → inserts `$$`, cursor between
- Type `}` when cursor before `}` → skips over
- Backspace on `{|}` → removes both

---

## Step 2: Custom `\begin/\end` Auto-Insertion

When the user types `\begin{env}` and presses Enter, auto-insert `\end{env}` on a new line.

```javascript
// In editor.js — custom Enter handler for \begin{}

import { keymap } from '@codemirror/view';

const beginEndKeymap = keymap.of([{
  key: 'Enter',
  run: (view) => {
    const { state } = view;
    const cursor = state.selection.main.head;
    const line = state.doc.lineAt(cursor);
    const lineText = line.text;

    // Check if the line matches \begin{something}
    const match = lineText.match(/\\begin\{(\w+\*?)\}\s*$/);
    if (match && cursor >= line.from + lineText.lastIndexOf('}')) {
      const envName = match[1];
      const indent = lineText.match(/^(\s*)/)[1]; // preserve indentation
      const insertion = `\n${indent}  \n${indent}\\end{${envName}}`;

      view.dispatch({
        changes: { from: cursor, insert: insertion },
        selection: { anchor: cursor + indent.length + 3 }, // cursor on blank line, indented
      });
      return true; // handled
    }
    return false; // not handled — let default Enter behavior run
  },
}]);

// Add to extensions (BEFORE defaultKeymap so it gets first shot):
// beginEndKeymap,
```

### Key Points
- The handler only fires if the current line ends with `\begin{envname}`
- The cursor must be at or after the closing `}` (not mid-edit)
- Returns `false` if the line doesn't match → normal Enter behavior
- Preserves the original line's indentation + adds 2-space indent for the body

---

## Do's & Don'ts

### Do's
- ✅ Auto-close `{`, `(`, `[`, `$`
- ✅ Support skip-over (typing `}` when it's already there)
- ✅ Handle `\begin{env*}` (starred environments like `align*`)
- ✅ Preserve indentation from the `\begin` line

### Don'ts
- ❌ Don't auto-close `'` or `"` — LaTeX uses backtick pairs (`` `...` ``)
- ❌ Don't auto-insert `\end` on lines that already have `\end` below
- ❌ Don't fire inside comments (`%`)

---

## Final Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | Typing `{` inserts `{}` with cursor between | ☐ |
| 2 | Typing `$` inserts `$$` with cursor between | ☐ |
| 3 | Typing `}` skips over existing `}` | ☐ |
| 4 | Backspace on `{|}` removes both | ☐ |
| 5 | `\begin{itemize}` + Enter → `\end{itemize}` auto-inserts | ☐ |
| 6 | `\begin{align*}` + Enter → `\end{align*}` auto-inserts | ☐ |
| 7 | Cursor is indented between begin/end | ☐ |
| 8 | Normal Enter works on non-`\begin` lines | ☐ |

> **Done → Proceed to Feature 2.3.**
