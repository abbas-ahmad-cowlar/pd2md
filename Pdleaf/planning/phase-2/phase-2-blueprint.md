# Phase 2 Blueprint — Editor Enhancements

> **Phase**: 2 of 7
> **Goal**: Transform the basic CodeMirror editor from Phase 1 into a professional-grade LaTeX editing experience. Every enhancement in this phase is a CodeMirror extension — no backend changes required.
> **Estimated Effort**: 1–2 weeks
> **Prerequisite**: Phase 1 is complete. The editor loads, compiles, and previews a PDF.

---

## What Phase 2 Delivers

When Phase 2 is complete, a user should be able to:
1. Get context-aware LaTeX autocomplete as they type (commands, environments, packages)
2. Type `{` and have `}` auto-inserted; type `\begin{itemize}` and get `\end{itemize}` automatically
3. See matching brackets highlighted
4. Fold/unfold LaTeX environments and sections
5. Toggle comments with `Ctrl+/`
6. Use multiple cursors (`Ctrl+D`, `Alt+Click`)
7. Toggle word wrap on/off
8. Switch to Vim or Emacs keybindings
9. Jump to any line with `Ctrl+G`

**Key Insight**: Every feature in Phase 2 is a CodeMirror extension. There are ZERO backend changes. This phase is purely frontend, purely editor-focused. This makes it fast to implement and easy to test.

**What Phase 2 does NOT include**: Auto-compile (Phase 3), file tree (Phase 4), spell check (Phase 5), settings panel (Phase 6).

---

## Architecture Principle: Extension Compartments

CodeMirror 6 has a concept called **Compartments** — dynamic extension slots that can be reconfigured at runtime without recreating the editor. We'll use compartments for features that can be toggled (word wrap, keybinding mode, etc.):

```javascript
import { Compartment } from '@codemirror/state';

const lineWrapCompartment = new Compartment();
const keybindingCompartment = new Compartment();

// In initEditor(), add:
extensions: [
  lineWrapCompartment.of(EditorView.lineWrapping), // default: on
  keybindingCompartment.of([]),                      // default: standard
  // ...
]

// To toggle at runtime:
editorView.dispatch({
  effects: lineWrapCompartment.reconfigure(
    wrapEnabled ? EditorView.lineWrapping : []
  ),
});
```

This pattern is used in Features 2.7 and 2.8. Understanding it upfront is important.

---

## Feature Summary Table

| # | Feature | Effort | CodeMirror Built-in? | New Code? |
|---|---------|--------|---------------------|-----------|
| 2.1 | LaTeX Autocomplete | 4–6 hrs | Extension yes, data no | Custom dictionary + completionSource |
| 2.2 | Auto-Close Brackets & `\begin/\end` | 2–3 hrs | Partially | Custom `\begin/\end` handler |
| 2.3 | Bracket Matching / Highlighting | 15 min | Yes — `bracketMatching()` | None |
| 2.4 | Code Folding | 3–4 hrs | Extension yes, logic no | Custom `foldService` for LaTeX |
| 2.5 | Comment / Uncomment Toggle | 30 min | Yes — `toggleComment` | Config only |
| 2.6 | Multiple Cursors | 0 min | Yes — built into basicSetup | Already done |
| 2.7 | Word Wrap Toggle | 1 hr | Yes — `lineWrapping` | Compartment toggle |
| 2.8 | Vim / Emacs Keybindings | 1–2 hrs | npm packages exist | Compartment toggle |
| 2.9 | Go-to-Line Dialog | 1–2 hrs | Partial | Custom dialog |

**Total estimated effort**: 12–18 hours

---

## Implementation Order

The features should be implemented in this order:

1. **2.3 — Bracket Matching** (already included in Phase 1; verify it works)
2. **2.6 — Multiple Cursors** (already built into CodeMirror; verify it works)
3. **2.5 — Comment Toggle** (tiny config change)
4. **2.2 — Auto-Close Brackets** (mostly built-in + custom `\begin/\end`)
5. **2.7 — Word Wrap Toggle** (Compartment pattern introduction)
6. **2.1 — LaTeX Autocomplete** (biggest feature — needs the dictionary)
7. **2.4 — Code Folding** (custom fold service)
8. **2.9 — Go-to-Line** (small UI dialog)
9. **2.8 — Vim/Emacs** (npm install + Compartment toggle)

Rationale: Start with zero-code wins (2.3, 2.6), then small config (2.5, 2.2), then introduce the Compartment pattern (2.7), then tackle the bigger features (2.1, 2.4), and finish with the UI pieces (2.9, 2.8).

---

## Editor Module Refactoring

Phase 2 requires changes to `src/js/editor.js`:
1. Add new extensions to the `EditorState.create()` call
2. Add Compartments for toggleable features
3. Export new utility functions (`toggleWordWrap()`, `setKeybindingMode()`, `goToLine()`)

**Important**: All Phase 2 features modify the SAME file (`editor.js`). Do NOT create separate files per feature — they're all CodeMirror extensions that go into the same editor initialization.

The exception is the autocomplete dictionary, which should be in its own file: `src/js/latexCompletions.js`.

### File Changes Summary

| File | What Changes |
|------|-------------|
| `src/js/editor.js` | Add extensions, Compartments, export new functions |
| `src/js/latexCompletions.js` | **[NEW]** Autocomplete dictionary and completion source |
| `src/css/style.css` | Add styles for autocomplete dropdown, fold gutters, go-to-line dialog |
| `src/index.html` | Add go-to-line dialog markup (if using a DOM dialog) |

---

## Feature 2.1 — LaTeX Autocomplete

### What We're Building
Context-aware autocomplete for LaTeX commands, environments, and packages. Shows a dropdown as the user types, triggered by `\` or `Ctrl+Space`.

### Sub-Steps
1. **Install the autocomplete extension**: `@codemirror/autocomplete` (likely already installed with `codemirror` meta-package)
2. **Create the autocomplete dictionary** (`latexCompletions.js`) with ~500 entries covering:
   - Document structure: `\documentclass`, `\usepackage`, `\begin`, `\end`
   - Sectioning: `\chapter`, `\section`, `\subsection`, `\subsubsection`, `\paragraph`
   - Text formatting: `\textbf`, `\textit`, `\underline`, `\emph`, `\texttt`
   - Math: `\frac`, `\sqrt`, `\sum`, `\int`, `\lim`, `\alpha`, `\beta`, Greek letters
   - Environments: `itemize`, `enumerate`, `figure`, `table`, `equation`, `align`, `tabular`
   - References: `\ref`, `\label`, `\cite`, `\eqref`, `\pageref`
   - Common packages: `amsmath`, `graphicx`, `hyperref`, `geometry`, `babel`, `fontenc`
3. **Create the completion source function** that:
   - Detects when the cursor is after `\` → offer command completions
   - Detects when inside `\begin{` → offer environment names
   - Detects when inside `\usepackage{` → offer package names
   - Provides snippets with tab stops (e.g., `\frac{$1}{$2}`)
4. **Register the autocompletion extension** in the editor with:
   - `activateOnTyping: true` (show suggestions as you type after `\`)
   - `override: [latexCompletionSource]` (our custom source)
   - Sensible defaults: max 20 suggestions, fuzzy matching

### Do's
- ✅ Organize the dictionary by category (sectioning, formatting, math, etc.)
- ✅ Include `detail` field for each completion (e.g., "Sectioning command", "Greek letter")
- ✅ Include `info` field with a brief description/usage hint
- ✅ Use snippets with `${}` tab stops for commands with arguments
- ✅ Sort by relevance (most common commands first)

### Don'ts
- ❌ Don't try to parse the entire document for custom command definitions — that's too complex for Phase 2
- ❌ Don't add citation key completion (`\cite{key}`) — that requires parsing `.bib` files (Phase 5)
- ❌ Don't add label completion (`\ref{label}`) — that requires scanning for `\label{}` (Phase 5)
- ❌ Don't block the UI thread — the dictionary lookup should be fast (< 5ms)

### Definition of Done
- [ ] Typing `\sec` shows `\section`, `\subsection`, etc. in a dropdown
- [ ] Typing `\begin{` shows environment names
- [ ] Typing `\usepackage{` shows package names
- [ ] `Ctrl+Space` opens the autocomplete dropdown manually
- [ ] Selecting `\frac{}{}` places the cursor in the first `{}`
- [ ] Greek letters like `\alpha`, `\beta` are in the dictionary
- [ ] Dropdown has at most 20 suggestions
- [ ] No lag when typing — completions appear within 50ms

### How to Test
1. Type `\` → dropdown should appear with suggestions
2. Type `\sec` → dropdown should narrow to `\section`, `\subsection`, etc.
3. Select `\section{}` → cursor should be inside the `{}`
4. Type `\begin{` → dropdown should show `itemize`, `enumerate`, `equation`, etc.
5. Type `\alpha` → should show `\alpha` in the dropdown
6. Press `Escape` → dropdown should close
7. `Ctrl+Space` → dropdown should open at any cursor position

---

## Feature 2.2 — Auto-Close Brackets & `\begin/\end` Pairs

### What We're Building
Automatic insertion of matching delimiters and LaTeX environment closers.

### Sub-Steps
1. **Enable `closeBrackets()`** from `@codemirror/autocomplete`:
   - Handles `{→}`, `(→)`, `[→]`, `$→$`
   - Typing the closing character when it already exists skips over it (no double brackets)
   - Backspace on opening bracket removes the closing one too
2. **Custom `\begin/\end` handler**:
   - When the user types `\begin{env}` and presses Enter, auto-insert `\end{env}` on a new line below
   - Place the cursor between `\begin` and `\end` (indented)
   - This requires an `EditorView.inputHandler` or a `keymap` entry for Enter inside `\begin{}`

### Do's
- ✅ Auto-close `{`, `(`, `[`, `$`, `` ` ``
- ✅ Skip-over when typing the closing char (e.g., typing `}` when `}` is already there)
- ✅ Delete pairs on Backspace (e.g., Backspace on `{|}` → empty)
- ✅ Auto-insert `\end{env}` when `\begin{env}` + Enter is typed

### Don'ts
- ❌ Don't auto-close `'` or `"` — LaTeX uses `` ` `` and `'` differently from programming languages
- ❌ Don't auto-close inside comments (lines starting with `%`)
- ❌ Don't be aggressive — if the user pastes code, don't mangle it

### Definition of Done
- [ ] Typing `{` inserts `{}`; cursor is between them
- [ ] Typing `$` inserts `$$`; cursor is between them
- [ ] Typing `}` when cursor is before `}` skips over it
- [ ] Backspace on `{|}` removes both braces
- [ ] Typing `\begin{itemize}` + Enter inserts `\end{itemize}` below
- [ ] Cursor is indented between `\begin` and `\end`

### How to Test
1. Type `{` → should see `{}` with cursor between
2. Type `hello` → see `{hello}`
3. Type `}` → cursor should skip past the existing `}`
4. Backspace → removes the `}`; another backspace → removes the `{`
5. Type `\begin{enumerate}`, press Enter → `\end{enumerate}` appears below
6. Cursor should be on the blank line between begin and end, indented

---

## Feature 2.3 — Bracket Matching / Highlighting

### What We're Building
Visual highlighting of matching bracket pairs when the cursor is on or adjacent to a bracket.

### Sub-Steps
1. **Verify `bracketMatching()` is already active** — it was included in Feature 1.2's extension list
2. **Test it works** with `{}`, `()`, `[]`
3. **Add CSS** for the bracket match highlight if needed:
   ```css
   .cm-matchingBracket {
     background-color: rgba(124, 111, 247, 0.3); /* accent-primary at 30% */
     border-bottom: 1px solid var(--accent-primary);
   }
   .cm-nonmatchingBracket {
     background-color: rgba(248, 113, 113, 0.3); /* error red at 30% */
   }
   ```

### Definition of Done
- [ ] Cursor on `{` → matching `}` is highlighted
- [ ] Cursor on `}` → matching `{` is highlighted
- [ ] Mismatched brackets show red highlight
- [ ] Works for `()`, `[]`, `{}`

### How to Test
1. Type `{hello}` → click on `{` → `}` should highlight
2. Type `{hello` (no closing brace) → click on `{` → red highlight (no match)

---

## Feature 2.4 — Code Folding

### What We're Building
Fold/unfold LaTeX environments (`\begin{...}...\end{...}`) and sections (`\section{...}` through the next section) by clicking a gutter arrow or pressing `Ctrl+Shift+[`.

### Sub-Steps
1. **Install fold extensions**: `foldGutter()`, `foldKeymap` from `@codemirror/language`
2. **Write a custom `foldService`** that finds fold ranges:
   - `\begin{env}` → fold from end of `\begin{env}` line to `\end{env}` line (exclusive)
   - `\section{...}` → fold from end of section line to the line before the next `\section` (or EOF)
   - Same for `\subsection`, `\subsubsection`, `\chapter`, `\paragraph`
3. **Add the fold gutter** to the editor (small arrow icons in the gutter)
4. **Style the fold gutter** arrows to match the dark theme

### Do's
- ✅ Match `\begin{env}` with the corresponding `\end{env}` (handle nesting)
- ✅ Fold sections from their heading to the next same-or-higher-level heading
- ✅ Show fold gutter icons (▶ for foldable, ▼ for folded)
- ✅ Support keyboard: `Ctrl+Shift+[` to fold, `Ctrl+Shift+]` to unfold

### Don'ts
- ❌ Don't fold single-line environments (e.g., `\begin{center}...\end{center}` on one line)
- ❌ Don't fold comments — just LaTeX structures
- ❌ Don't nest folds more than 3 levels deep (confusing)

### Definition of Done
- [ ] Fold gutter appears with arrow icons
- [ ] Clicking the arrow on a `\begin{itemize}` line folds the environment
- [ ] Folded region shows a `...` indicator
- [ ] Clicking again unfolds it
- [ ] `\section{}` can fold everything until the next `\section{}`
- [ ] `Ctrl+Shift+[` folds at cursor, `Ctrl+Shift+]` unfolds

### How to Test
1. Type a multi-line `\begin{itemize}...\end{itemize}` → fold gutter icon should appear
2. Click the icon → content between begin/end should collapse to `...`
3. Click again → content reappears
4. `Ctrl+Shift+[` → folds the block at cursor
5. `Ctrl+Shift+]` → unfolds

---

## Feature 2.5 — Comment / Uncomment Toggle

### What We're Building
`Ctrl+/` toggles a `%` comment prefix on the selected line(s).

### Sub-Steps
1. **Configure the comment system** for LaTeX:
   ```javascript
   import { commentKeymap } from '@codemirror/commands';
   // In the language config or as a separate extension:
   // LaTeX's line comment character is '%'
   ```
2. **Add `commentKeymap`** to the keymap array
3. **If CodeMirror doesn't auto-detect `%`** for the LaTeX language, configure it manually:
   ```javascript
   import { LanguageDescription } from '@codemirror/language';
   // The stex StreamLanguage may need commentTokens: { line: '%' }
   ```

### Definition of Done
- [ ] Select one line → `Ctrl+/` → line gets `% ` prefix
- [ ] `Ctrl+/` again → `% ` is removed
- [ ] Select multiple lines → `Ctrl+/` → all lines get `%` prefix
- [ ] Works with both single-line and multi-line selections

### How to Test
1. Click on a line → `Ctrl+/` → see `%` appear at the start
2. `Ctrl+/` again → `%` disappears
3. Select 3 lines → `Ctrl+/` → all 3 get `%`
4. `Ctrl+/` again → all 3 lose `%`

---

## Feature 2.6 — Multiple Cursors / Multi-Select

### What We're Building
Standard multi-cursor editing that's already built into CodeMirror 6.

### Sub-Steps
1. **Verify it works** — this is already included in the extensions from Feature 1.2
2. **Test these specific behaviors**:
   - `Ctrl+D` — select the next occurrence of the current selection
   - `Alt+Click` — place an additional cursor
   - `Ctrl+Alt+↑/↓` — add cursor above/below

### Definition of Done
- [ ] `Ctrl+D` selects next occurrence
- [ ] Multiple `Ctrl+D` presses select additional occurrences
- [ ] `Alt+Click` places a second cursor
- [ ] Typing with multiple cursors edits at all positions simultaneously

### How to Test
1. Select the word `section` → `Ctrl+D` → next `section` is selected too
2. Type → both selections change simultaneously
3. `Alt+Click` on two different lines → two cursors appear → type → text appears at both

---

## Feature 2.7 — Word Wrap Toggle

### What We're Building
A toggle control (keyboard shortcut or toolbar button) to enable/disable soft line wrapping.

### Sub-Steps
1. **Create a Compartment** for line wrapping (see Architecture section above)
2. **Add a toggle function** to `editor.js`:
   ```javascript
   export function toggleWordWrap() { ... }
   ```
3. **Register a keyboard shortcut**: `Alt+Z` (same as VS Code)
4. **Optional**: Add a toolbar button or status bar indicator showing wrap state

### Definition of Done
- [ ] `Alt+Z` toggles word wrap on/off
- [ ] When off, long lines extend horizontally with a scrollbar
- [ ] When on, long lines wrap at the panel boundary
- [ ] Default state: on (set in Phase 1)

### How to Test
1. Type a very long line (200+ characters)
2. Verify it wraps by default
3. Press `Alt+Z` → line should extend past the panel with horizontal scroll
4. Press `Alt+Z` again → line wraps again

---

## Feature 2.8 — Vim / Emacs Keybinding Modes

### What We're Building
Optional keybinding modes for power users who prefer Vim or Emacs bindings.

### Sub-Steps
1. **Install packages**:
   ```bash
   npm install @replit/codemirror-vim
   npm install @replit/codemirror-emacs
   ```
2. **Create a Compartment** for keybinding mode
3. **Add a toggle function**:
   ```javascript
   export function setKeybindingMode(mode) { ... } // 'default' | 'vim' | 'emacs'
   ```
4. **No UI for now** — will be controlled from the Settings panel (Phase 6)
5. **For testing**: expose the function globally or add a temporary keyboard shortcut

### Definition of Done
- [ ] `setKeybindingMode('vim')` enables Vim keybindings
- [ ] `setKeybindingMode('emacs')` enables Emacs keybindings
- [ ] `setKeybindingMode('default')` restores standard keybindings
- [ ] Vim mode shows a mode indicator (Normal/Insert) — if the package provides one
- [ ] Switching modes doesn't lose editor content

### How to Test
1. Call `setKeybindingMode('vim')` from console
2. Press `i` → should enter insert mode → type text
3. Press `Escape` → should enter normal mode
4. Press `dd` → should delete a line
5. Call `setKeybindingMode('default')` → normal editing resumes

---

## Feature 2.9 — Go-to-Line Dialog

### What We're Building
A small dialog (opened with `Ctrl+G`) where the user types a line number and the editor jumps to it.

### Sub-Steps
1. **Create the dialog HTML** (either a DOM modal or use CodeMirror's panel API)
2. **Create the dialog CSS** (match the dark theme)
3. **Register `Ctrl+G`** to open the dialog
4. **On submit**: parse the number, dispatch cursor to that line, close dialog
5. **On Escape or outside click**: close dialog without action

### Dialog UI
```
┌──────────────────────────────────┐
│  Go to Line: [____42____] [Go]  │
└──────────────────────────────────┘
```
- Small overlay near the top of the editor
- Auto-focused input
- Enter submits, Escape closes
- Shows "Line X of Y" hint

### Definition of Done
- [ ] `Ctrl+G` opens a small dialog
- [ ] Typing a number and pressing Enter jumps to that line
- [ ] Line is highlighted and scrolled into view
- [ ] Pressing Escape closes the dialog
- [ ] Invalid input (non-number, out of range) is handled gracefully

### How to Test
1. `Ctrl+G` → dialog appears with input focused
2. Type `15` → Enter → editor scrolls to line 15, cursor is there
3. `Ctrl+G` → type `99999` → Enter → jumps to last line (clamped)
4. `Ctrl+G` → Escape → dialog closes, nothing changes

---

## Phase 2 Integration Test Plan

> After all 9 features are implemented, run this end-to-end test.

### Full Workflow
1. Open Pdleaf → editor loads with `main.tex`
2. Type `\sec` → autocomplete shows `\section`, `\subsection`
3. Select `\section{}` → cursor is inside `{}`
4. Type `New Section` → press Enter twice
5. Type `\begin{itemize}` → press Enter → `\end{itemize}` auto-inserts
6. Type `\item First` → press Enter → type `\item Second`
7. Click on `{` in `\begin{itemize}` → matching `}` in `\end{` highlights
8. Click the fold gutter icon on `\begin{itemize}` → environment folds
9. Select both `\item` lines → `Ctrl+/` → both get `%` prefix
10. `Ctrl+/` → uncommented again
11. `Ctrl+D` on `item` → selects both → type `task` → both change to `\task`
12. `Ctrl+Z` to undo
13. Type a very long line → `Alt+Z` → wraps toggle
14. `Ctrl+G` → type `1` → Enter → jumps to top of file
15. `Ctrl+S` → compiles → PDF updates

### Edge Cases
1. Autocomplete with empty document → should work
2. Fold an already-folded region → should unfold
3. Comment a line that's already commented → should uncomment
4. Multi-cursor with autocomplete → each cursor gets the completion
5. Vim mode + all Phase 2 features → should coexist

---

> **Phase 2 is complete when all integration tests pass without errors.**
>
> Next: Proceed to Phase 3 (Compilation & Preview Polish) as defined in the roadmap.
