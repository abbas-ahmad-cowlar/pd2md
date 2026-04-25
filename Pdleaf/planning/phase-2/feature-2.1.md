# Feature 2.1 — LaTeX Autocomplete

> **Phase**: 2 | **Feature**: 1 of 9
> **Goal**: Context-aware autocomplete for LaTeX commands, environments, and packages. Dropdown appears as user types after `\` or on `Ctrl+Space`.
> **Estimated Effort**: 4–6 hours
> **Dependencies**: Feature 1.2 (editor module). No backend changes.

---

## Overview

Two files to create/modify:
1. `src/js/latexCompletions.js` — **[NEW]** The autocomplete dictionary (~500 entries)
2. `src/js/editor.js` — Add the autocompletion extension

---

## Step 1: Install Autocomplete Extension

```bash
npm install @codemirror/autocomplete
# Likely already installed with the 'codemirror' meta-package — verify first
```

---

## Step 2: Create the Autocomplete Dictionary

### File: `src/js/latexCompletions.js`

Organize entries by category. Each entry has:
- `label` — the command text (e.g., `\section{}`)
- `type` — category for icon styling (`keyword`, `function`, `variable`, `type`)
- `detail` — short category tag (e.g., "Sectioning", "Math")
- `info` — one-line description
- `apply` — snippet with `${}` tab stops (optional)

### Dictionary Categories

#### Sectioning (~10 entries)
`\part`, `\chapter`, `\section`, `\subsection`, `\subsubsection`, `\paragraph`, `\subparagraph`, `\title`, `\author`, `\date`

#### Document Structure (~15 entries)
`\documentclass{}`, `\usepackage{}`, `\begin{}`, `\end{}`, `\input{}`, `\include{}`, `\maketitle`, `\tableofcontents`, `\listoffigures`, `\listoftables`, `\appendix`, `\bibliography{}`, `\bibliographystyle{}`

#### Text Formatting (~20 entries)
`\textbf{}`, `\textit{}`, `\underline{}`, `\emph{}`, `\texttt{}`, `\textrm{}`, `\textsf{}`, `\textsc{}`, `\textsl{}`, `\tiny`, `\small`, `\normalsize`, `\large`, `\Large`, `\LARGE`, `\huge`, `\Huge`, `\centering`, `\raggedright`, `\raggedleft`

#### Math Commands (~60 entries)
`\frac{}{}`, `\sqrt{}`, `\sum`, `\prod`, `\int`, `\lim`, `\infty`, `\partial`, `\nabla`, `\cdot`, `\times`, `\div`, `\pm`, `\mp`, `\leq`, `\geq`, `\neq`, `\approx`, `\equiv`, `\sim`, `\propto`, `\in`, `\notin`, `\subset`, `\supset`, `\cup`, `\cap`, `\forall`, `\exists`, `\rightarrow`, `\leftarrow`, `\Rightarrow`, `\Leftarrow`, `\leftrightarrow`, `\hat{}`, `\bar{}`, `\vec{}`, `\dot{}`, `\ddot{}`, `\tilde{}`, `\overline{}`, `\underline{}`, `\overbrace{}`, `\underbrace{}`

#### Greek Letters (~48 entries)
`\alpha` through `\omega`, uppercase variants (`\Alpha`, `\Gamma`, `\Delta`, `\Theta`, `\Lambda`, `\Xi`, `\Pi`, `\Sigma`, `\Phi`, `\Psi`, `\Omega`)

#### Environment Names (~25 entries)
For use inside `\begin{}`: `document`, `itemize`, `enumerate`, `description`, `figure`, `table`, `tabular`, `equation`, `equation*`, `align`, `align*`, `gather`, `multline`, `array`, `matrix`, `pmatrix`, `bmatrix`, `cases`, `center`, `flushleft`, `flushright`, `minipage`, `abstract`, `verbatim`, `quote`

#### Common Packages (~30 entries)
For use inside `\usepackage{}`: `amsmath`, `amssymb`, `amsthm`, `graphicx`, `hyperref`, `geometry`, `babel`, `fontenc`, `inputenc`, `xcolor`, `listings`, `tikz`, `pgfplots`, `booktabs`, `multirow`, `caption`, `subcaption`, `float`, `algorithm2e`, `fancyhdr`, `setspace`, `natbib`, `biblatex`, `cleveref`, `siunitx`, `enumitem`, `tcolorbox`, `microtype`

#### References & Labels (~10 entries)
`\label{}`, `\ref{}`, `\eqref{}`, `\pageref{}`, `\cite{}`, `\footnote{}`, `\footnotemark`, `\footnotetext{}`

#### Figures & Tables (~15 entries)
`\includegraphics[]{}`, `\caption{}`, `\centering`, `\hline`, `\cline{}`, `\multicolumn{}{}{}`, `\toprule`, `\midrule`, `\bottomrule`, `\resizebox{}{}{}`, `\scalebox{}{}`

---

## Step 3: Create the Completion Source Function

```javascript
// src/js/latexCompletions.js

import { commands, environments, packages } from './latexDictionary.js'; // or inline

/**
 * CodeMirror completion source for LaTeX.
 */
export function latexCompletionSource(context) {
  // 1. Check if we're inside \begin{ or \usepackage{
  const beforeCursor = context.matchBefore(/\\(begin|usepackage)\{[^}]*/);
  if (beforeCursor) {
    const isBegin = beforeCursor.text.includes('\\begin{');
    const bracePos = beforeCursor.text.lastIndexOf('{') + 1;
    const prefix = beforeCursor.text.slice(bracePos);
    const from = beforeCursor.from + bracePos;

    return {
      from,
      options: (isBegin ? environments : packages)
        .filter(e => e.label.startsWith(prefix)),
      validFor: /^[a-zA-Z*]*/,
    };
  }

  // 2. Check if we're after a backslash
  const word = context.matchBefore(/\\[a-zA-Z]*/);
  if (word) {
    if (word.from === word.to && !context.explicit) return null;
    return {
      from: word.from,
      options: commands,
      validFor: /^\\[a-zA-Z]*/,
    };
  }

  return null;
}
```

---

## Step 4: Register in Editor

Add to `editor.js`:
```javascript
import { autocompletion } from '@codemirror/autocomplete';
import { latexCompletionSource } from './latexCompletions.js';

// In extensions array:
autocompletion({
  override: [latexCompletionSource],
  activateOnTyping: true,
  maxRenderedOptions: 20,
}),
```

---

## Step 5: CSS for Autocomplete Dropdown

```css
/* Autocomplete dropdown styling */
.cm-tooltip-autocomplete {
  background: var(--bg-tertiary) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
}
.cm-tooltip-autocomplete > ul > li {
  color: var(--text-primary) !important;
}
.cm-tooltip-autocomplete > ul > li[aria-selected] {
  background: var(--accent-primary) !important;
  color: white !important;
}
.cm-completionDetail {
  color: var(--text-secondary) !important;
  font-style: italic;
}
```

## Detailed Dictionary Entry Format

Each entry in the dictionary should follow this exact structure. Here are representative examples per category:

### Snippet Syntax
CodeMirror uses `${N}` for tab stops in snippets (via the `snippetCompletion` helper from `@codemirror/autocomplete`):
- `${1}` — first tab stop (cursor goes here after selection)
- `${2}` — second tab stop (Tab key jumps here)
- `${1:placeholder}` — tab stop with default placeholder text

```javascript
import { snippetCompletion } from '@codemirror/autocomplete';

// Example entries:
const commandEntries = [
  // Simple command — no arguments
  { label: '\\maketitle', type: 'keyword', detail: 'Document', info: 'Renders the title block' },

  // Command with one argument — use snippet
  snippetCompletion('\\section{${1:title}}', {
    label: '\\section{}',
    type: 'keyword',
    detail: 'Sectioning',
    info: 'Start a new section',
  }),

  // Command with two arguments
  snippetCompletion('\\frac{${1:numerator}}{${2:denominator}}', {
    label: '\\frac{}{}',
    type: 'function',
    detail: 'Math',
    info: 'Fraction: numerator/denominator',
  }),

  // Command with optional + required argument
  snippetCompletion('\\includegraphics[${1:width=\\textwidth}]{${2:filename}}', {
    label: '\\includegraphics[]{}',
    type: 'function',
    detail: 'Figures',
    info: 'Include an image file',
  }),

  // Environment — just the name (for \begin{} context)
  { label: 'itemize', type: 'type', detail: 'Environment', info: 'Bullet point list' },

  // Package — just the name (for \usepackage{} context)
  { label: 'amsmath', type: 'variable', detail: 'Package', info: 'Enhanced math typesetting' },
];
```

### Type-to-Icon Mapping
CodeMirror assigns icons based on the `type` field:
| `type` value | Icon/Color | Used for |
|---|---|---|
| `keyword` | Blue square | Sectioning, structure commands |
| `function` | Purple circle | Math commands, functions |
| `variable` | Orange diamond | Packages |
| `type` | Green triangle | Environments |
| `text` | Gray | Greek letters, symbols |

---

## Edge Cases & Gotchas

### 6.1 — Autocomplete inside math mode
Inside `$...$` or `\[...\]`, the same completion source runs. This is fine — math commands work everywhere. No special handling needed.

### 6.2 — Autocomplete inside comments
Ideally, autocomplete should NOT trigger inside `% comment` lines. Check if the cursor is in a comment token before returning results:
```javascript
// In latexCompletionSource:
const tree = syntaxTree(context.state);
const node = tree.resolveInner(context.pos, -1);
if (node.type.name === 'comment') return null; // skip autocomplete in comments
```
This requires importing `syntaxTree` from `@codemirror/language`. If the LaTeX language mode doesn't mark comments as `comment` nodes, skip this check for Phase 2.

### 6.3 — Performance with ~500 entries
A 500-entry array with `.filter()` takes < 1ms. No optimization needed. If the dictionary ever grows to 5000+ entries, consider using a prefix trie.

### 6.4 — Snippet tab stops with multi-cursor
If the user has multiple cursors, the snippet should apply at each cursor independently. CodeMirror handles this natively.

### 6.5 — Autocomplete + Vim mode
In Vim normal mode, autocomplete should NOT trigger. In insert mode, it should. The `@replit/codemirror-vim` package handles this by not dispatching input events in normal mode.

---

## How to Test — Detailed Scenarios

### Test 1: Basic command completion
1. Type `\tex` in the editor
2. Dropdown should appear showing `\textbf{}`, `\textit{}`, `\texttt{}`, etc.
3. Use arrow keys to navigate
4. Press Enter or Tab to select
5. Selected command should insert with cursor positioned inside `{}`

### Test 2: Environment completion
1. Type `\begin{`
2. Dropdown should show environment names: `itemize`, `enumerate`, `equation`, etc.
3. Select `itemize` → should complete to `\begin{itemize}`
4. The `\begin/\end` handler (Feature 2.2) will then handle the Enter key

### Test 3: Package completion
1. Type `\usepackage{`
2. Dropdown should show package names: `amsmath`, `graphicx`, `hyperref`, etc.
3. Select one → should insert just the name (e.g., `\usepackage{amsmath}`)

### Test 4: Ctrl+Space explicit trigger
1. Place cursor on an empty line
2. Press `Ctrl+Space` → dropdown should show all commands (starting with top completions)
3. Type a few characters → dropdown should narrow

### Test 5: Escape closes dropdown
1. Trigger autocomplete
2. Press Escape → dropdown closes
3. Cursor stays where it was

### Test 6: Performance
1. Type `\` rapidly, then immediately keep typing more characters
2. Dropdown should appear and update without any perceptible lag
3. No jank or input delay

---

## Final Acceptance Checklist — Feature 2.1 Complete

| # | Check | Status |
|---|-------|--------|
| 1 | `@codemirror/autocomplete` installed and working | ☐ |
| 2 | `latexCompletions.js` exists with ~500 entries | ☐ |
| 3 | Entries organized by category (sectioning, math, etc.) | ☐ |
| 4 | Typing `\sec` shows section-related completions | ☐ |
| 5 | Typing `\begin{` shows environment names only | ☐ |
| 6 | Typing `\usepackage{` shows package names only | ☐ |
| 7 | `Ctrl+Space` opens dropdown anywhere | ☐ |
| 8 | Snippet tab stops work (`\frac{|}{|}` cursor placement) | ☐ |
| 9 | Tab key moves between tab stops in snippets | ☐ |
| 10 | Greek letters (`\alpha`, `\beta`, ...) in dictionary | ☐ |
| 11 | Max 20 suggestions shown at once | ☐ |
| 12 | Dropdown styled to match dark theme | ☐ |
| 13 | Selected item has purple highlight | ☐ |
| 14 | Detail text shows category (e.g., "Sectioning", "Math") | ☐ |
| 15 | No lag when typing — completions appear < 50ms | ☐ |
| 16 | Escape closes the dropdown | ☐ |
| 17 | Autocomplete doesn't trigger in comments (if feasible) | ☐ |

> **When all checks pass, Feature 2.1 is DONE. Proceed to Feature 2.2.**
