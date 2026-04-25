# Feature 2.4 — Code Folding

> **Phase**: 2 | **Feature**: 4 of 9
> **Goal**: Fold/unfold LaTeX environments (`\begin/\end`) and sections by clicking gutter arrows or using keyboard shortcuts.
> **Estimated Effort**: 3–4 hours
> **Dependencies**: Feature 1.2 (editor module).

---

## Overview

Two things to build:
1. A **custom `foldService`** that understands LaTeX structure (not JavaScript/JSON structure)
2. **Fold gutter** with styled icons + keyboard shortcuts

---

## Step 1: Install/Import Fold Extensions

```javascript
import { foldGutter, foldKeymap, foldService } from '@codemirror/language';
```

Add to keymap: `...foldKeymap` (provides `Ctrl+Shift+[` fold, `Ctrl+Shift+]` unfold).

---

## Step 2: Write the Custom LaTeX Fold Service

The built-in fold service doesn't understand LaTeX. We need a custom one.

```javascript
// src/js/editor.js — custom fold service

const latexFoldService = foldService.of((state, lineStart, lineEnd) => {
  const line = state.doc.lineAt(lineStart);
  const text = line.text.trimStart();

  // 1. Fold \begin{env} ... \end{env}
  const beginMatch = text.match(/^\\begin\{(\w+\*?)\}/);
  if (beginMatch) {
    const envName = beginMatch[1];
    const endPattern = `\\end{${envName}}`;

    // Search forward for matching \end{env}
    let depth = 1;
    let pos = line.to;
    while (pos < state.doc.length && depth > 0) {
      const nextLine = state.doc.lineAt(pos + 1);
      const trimmed = nextLine.text.trimStart();

      if (trimmed.startsWith(`\\begin{${envName}}`)) depth++;
      if (trimmed.startsWith(endPattern)) depth--;

      if (depth === 0) {
        // Fold from end of \begin line to start of \end line
        return { from: line.to, to: nextLine.from - 1 };
      }
      pos = nextLine.to;
    }
  }

  // 2. Fold \section{} ... (until next same-or-higher-level heading)
  const sectionLevels = {
    '\\chapter': 0, '\\section': 1, '\\subsection': 2,
    '\\subsubsection': 3, '\\paragraph': 4, '\\subparagraph': 5,
  };

  for (const [cmd, level] of Object.entries(sectionLevels)) {
    if (text.startsWith(cmd + '{') || text.startsWith(cmd + '[')) {
      // Find the next heading at same or higher level
      let pos = line.to;
      let foldEnd = state.doc.length; // default: fold to end of document

      while (pos < state.doc.length) {
        const nextLine = state.doc.lineAt(pos + 1);
        const trimmed = nextLine.text.trimStart();

        for (const [otherCmd, otherLevel] of Object.entries(sectionLevels)) {
          if (trimmed.startsWith(otherCmd + '{') || trimmed.startsWith(otherCmd + '[')) {
            if (otherLevel <= level) {
              foldEnd = nextLine.from - 1;
              return { from: line.to, to: foldEnd };
            }
          }
        }
        pos = nextLine.to;
      }

      // Fold to end of document if no next heading found
      if (line.to < state.doc.length) {
        return { from: line.to, to: state.doc.length };
      }
    }
  }

  return null; // No fold region found
});
```

### Key Points
- **Nesting-aware**: Handles nested `\begin{itemize}` inside `\begin{enumerate}`
- **Section hierarchy**: `\subsection` folds until the next `\subsection` or `\section` (not until the next `\subsubsection`)
- **Returns `null`** for lines that aren't foldable

---

## Step 3: Add Fold Gutter

```javascript
// In extensions:
foldGutter({
  markerDOM(open) {
    const marker = document.createElement('span');
    marker.className = open ? 'fold-marker fold-open' : 'fold-marker fold-closed';
    marker.textContent = open ? '▾' : '▸';
    return marker;
  },
}),
latexFoldService,
keymap.of(foldKeymap),
```

---

## Step 4: CSS for Fold Gutter

```css
/* Fold gutter markers */
.fold-marker {
  color: var(--text-placeholder);
  cursor: pointer;
  font-size: 12px;
  padding: 0 2px;
  transition: color var(--transition-fast);
}
.fold-marker:hover {
  color: var(--accent-primary);
}

/* Folded placeholder */
.cm-foldPlaceholder {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 3px;
  padding: 0 4px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 11px;
}
.cm-foldPlaceholder::after {
  content: '…';
}
```

---

## Do's & Don'ts

### Do's
- ✅ Handle nesting (environments inside environments)
- ✅ Respect section hierarchy levels
- ✅ Show `…` placeholder for folded regions
- ✅ Support both gutter click and keyboard (`Ctrl+Shift+[` / `]`)
- ✅ Handle starred variants (`\section*{}` should fold just like `\section{}`)
- ✅ Handle `\begin{env}` where `env` contains `*` (e.g., `align*`, `equation*`)

### Don'ts
- ❌ Don't fold single-line environments (e.g., `\begin{center}...\end{center}` all on one line)
- ❌ Don't fold comments — just LaTeX structures
- ❌ Don't fold the preamble (before `\begin{document}`) by default
- ❌ Don't crash on mismatched `\begin`/`\end` — return `null` gracefully

---

## Edge Cases

### 5.1 — Nested environments
```latex
\begin{enumerate}
  \begin{itemize}     ← this should fold independently
    \item nested
  \end{itemize}
  \item outer
\end{enumerate}       ← outer fold encompasses inner
```
The depth tracking in the fold service handles this: it increments depth on `\begin{enumerate}` and decrements on `\end{enumerate}`, ignoring inner `\begin{itemize}/\end{itemize}` pairs.

### 5.2 — Mismatched begin/end
```latex
\begin{itemize}
\end{enumerate}  ← wrong environment name
```
The fold service searches for `\end{itemize}` specifically. It won't match `\end{enumerate}`, so it returns `null` (no fold region found). This is safe — no crash.

### 5.3 — Section hierarchy
```latex
\section{A}        ← folds until \section{B}
  \subsection{A.1} ← folds until \subsection{A.2}
  content...
  \subsection{A.2} ← folds until \section{B}
  content...
\section{B}        ← folds until \section{C} or EOF
```

### 5.4 — Last section in document
If a `\section{}` has no subsequent section, it folds to the end of the document.

### 5.5 — `\begin{document}...\end{document}`
The `document` environment could technically fold. This is acceptable — the user probably won't fold the entire document, but it should work if they try.

### 5.6 — Performance on large documents
The fold service is called once per visible line, not for the entire document. Performance is proportional to the number of visible lines (~50-100), not the document length. The forward search to find `\end{env}` could be slow for very large documents — but for the typical LaTeX document (< 5000 lines), it's fine.

---

## How to Test — Detailed Scenarios

### Test 1: Environment folding
1. Type:
   ```latex
   \begin{itemize}
     \item First
     \item Second
     \item Third
   \end{itemize}
   ```
2. A fold arrow (▾) should appear in the gutter on the `\begin{itemize}` line
3. Click it → lines 2-4 collapse, showing `…`
4. Click `…` or the arrow again → region expands

### Test 2: Section folding
1. Type:
   ```latex
   \section{Introduction}
   This is the intro.
   \section{Methods}
   This is methods.
   ```
2. Fold arrows should appear on both `\section` lines
3. Fold `\section{Introduction}` → hides "This is the intro." only
4. Fold `\section{Methods}` → hides "This is methods." (to EOF)

### Test 3: Nested folding
1. Type nested environments
2. Fold the inner one → only inner collapses
3. Fold the outer one → everything collapses (including the already-folded inner)
4. Unfold the outer → inner is still folded

### Test 4: Keyboard shortcuts
1. Place cursor on a `\begin{itemize}` line
2. `Ctrl+Shift+[` → folds
3. `Ctrl+Shift+]` → unfolds

---

## Final Acceptance Checklist — Feature 2.4 Complete

| # | Check | Status |
|---|-------|--------|
| 1 | Fold gutter appears with arrow icons on foldable lines | ☐ |
| 2 | Clicking arrow on `\begin{itemize}` folds the environment | ☐ |
| 3 | Folded region shows `…` placeholder | ☐ |
| 4 | Clicking `…` or arrow unfolds | ☐ |
| 5 | `\section{}` folds to next `\section{}` | ☐ |
| 6 | `\subsection{}` folds to next `\subsection{}` or `\section{}` | ☐ |
| 7 | Last section folds to end of document | ☐ |
| 8 | Nested environments fold independently | ☐ |
| 9 | Nested: outer fold encompasses still-folded inner | ☐ |
| 10 | Starred environments (`align*`) fold correctly | ☐ |
| 11 | `Ctrl+Shift+[` folds at cursor | ☐ |
| 12 | `Ctrl+Shift+]` unfolds at cursor | ☐ |
| 13 | Mismatched `\begin/\end` doesn't crash (no fold shown) | ☐ |
| 14 | Single-line environments are NOT foldable | ☐ |
| 15 | Fold gutter icons match dark theme | ☐ |
| 16 | Folded placeholder `…` matches dark theme | ☐ |

> **When all checks pass, Feature 2.4 is DONE. Proceed to Feature 2.7.**
