# Pdleaf — Development Roadmap

> **Project**: Pdleaf — A local-first, free, personal LaTeX editor with live preview
> **Scope**: Single-user / student use. No collaboration. Code editor only (no visual/WYSIWYG). No journal submission.
> **Date**: 2026-04-26

---

## Guiding Principles

1. **Code-first**: We are building for people who write raw LaTeX. No visual editor.
2. **Local-first**: Everything runs on your machine. No cloud dependency. Can optionally run as a web server.
3. **Incremental**: Each phase produces a usable tool. Phase 1 alone should be a functional LaTeX editor.
4. **Free forever**: All tools and libraries used are open-source.
5. **No collaboration**: This is a personal tool. One user, one machine, one project at a time.

---

## Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | Vanilla HTML/CSS/JS or lightweight framework | Keeps it simple, fast, no build-step drama |
| Code Editor | CodeMirror 6 | Same engine Overleaf uses. Best LaTeX support. |
| PDF Viewer | pdf.js (Mozilla) | Industry-standard, open-source PDF renderer |
| Backend | Node.js (Express/Fastify) or Python (FastAPI) | Thin server to manage files + trigger compilation |
| LaTeX Engine | TeX Live (pdfLaTeX, XeLaTeX, LuaLaTeX) | Full distribution, all packages included |
| Compilation | latexmk | Handles multi-pass compilation automatically |
| Version/Checkpoints | Git (programmatic via simple-git or similar) | Each "Save" = a git commit. Browse/restore history. |
| Layout | split.js or CSS flexbox with draggable divider | Resizable editor/preview panels |

---

## Phase 1 — Foundation & Core Editor
> **Goal**: A bare-minimum functional LaTeX editor. Open a `.tex` file, edit it, compile it, see the PDF.
> **Estimated Effort**: 1–2 weeks

### 1.1 Project Scaffolding & Web App Shell
Set up the project structure: HTML entry point, CSS reset, JS entry, backend server (Express or FastAPI). Configure dev server (Vite or live-server). Create the basic three-panel layout skeleton (file tree sidebar, editor pane, PDF preview pane).
- **How**: `npm init`, install dependencies, create `index.html`, `style.css`, `app.js`, `server.js`.

### 1.2 CodeMirror 6 Integration (Basic)
Embed CodeMirror 6 in the editor pane with LaTeX syntax highlighting, line numbers, and basic editing (typing, selection, copy/paste). No autocomplete or folding yet — just a working code editor.
- **How**: `npm install @codemirror/...` packages. Initialize with `latex` language mode + `lineNumbers()` + `basicSetup`.

### 1.3 TeX Live Compilation Backend
Create an API endpoint that takes the project path, runs `pdflatex` (or `latexmk`) on the main `.tex` file, and returns success/failure + path to the output PDF. Handle compilation errors gracefully.
- **How**: `child_process.exec('latexmk -pdf -interaction=nonstopmode main.tex')` on the backend.

### 1.4 Manual Compile Button
A "Compile" button in the toolbar that sends a request to the backend, triggers compilation, and refreshes the PDF preview upon success.
- **How**: Frontend button → `fetch('/api/compile')` → backend runs `latexmk` → returns PDF path → frontend reloads PDF.

### 1.5 PDF Viewer (pdf.js)
Embed Mozilla's pdf.js in the preview pane to render the compiled PDF. Basic rendering with scroll, no zoom controls yet.
- **How**: Include `pdfjs-dist` npm package. Render pages into a `<canvas>` element in the preview pane.

### 1.6 Split-Panel Layout (Editor + Preview)
A two-panel layout with a draggable vertical divider. Editor on the left, PDF preview on the right. Resizable by dragging.
- **How**: Use `split.js` or a CSS flexbox layout with a draggable handle.

---

## Phase 2 — Editor Enhancements
> **Goal**: Make the code editor feel professional. Autocomplete, folding, bracket matching, and quality-of-life features.
> **Estimated Effort**: 1–2 weeks

### 2.1 LaTeX Autocomplete
Context-aware autocomplete for LaTeX commands (`\begin{`, `\usepackage{`, `\section{`), environment names, and common options. Triggered as you type or with `Ctrl+Space`.
- **How**: Build a CodeMirror `autocompletion` extension with a custom LaTeX command dictionary (~500 entries).

### 2.2 Auto-Close Brackets & Delimiters
Typing `{` auto-inserts `}`. Same for `(`, `[`, `$`. Typing `\begin{env}` auto-inserts `\end{env}`.
- **How**: CodeMirror's `closeBrackets()` extension + custom handler for `\begin`/`\end` pairs.

### 2.3 Bracket Matching / Highlighting
Highlight the matching bracket when cursor is on `{`, `}`, `(`, `)`, `[`, `]`.
- **How**: CodeMirror's `bracketMatching()` extension. Zero custom code.

### 2.4 Code Folding
Fold/unfold `\begin{...}...\end{...}` environments and `\section{...}` through next section.
- **How**: Write a custom CodeMirror `foldService` that detects `\begin`/`\end` and sectioning commands.

### 2.5 Comment / Uncomment Toggle
`Ctrl+/` toggles `%` prefix on selected lines.
- **How**: CodeMirror's `toggleComment` command with `lineComment: '%'` config.

### 2.6 Multiple Cursors / Multi-Select
`Ctrl+D` selects next occurrence. `Alt+Click` places additional cursors.
- **How**: Built into CodeMirror 6 `basicSetup`. No custom code needed.

### 2.7 Word Wrap Toggle
Option to toggle soft line wrapping on/off.
- **How**: CodeMirror's `EditorView.lineWrapping` extension, toggled via a settings control.

### 2.8 Vim / Emacs Keybinding Modes
Optional keybinding modes for power users.
- **How**: `@codemirror/lang-vim` and `@codemirror/lang-emacs` packages. Toggle in settings.

### 2.9 Go-to-Line Dialog
`Ctrl+Shift+L` opens a dialog to jump to a specific line number.
- **How**: Small modal dialog that calls `editor.dispatch({ selection: { anchor: linePos } })`.

---

## Phase 3 — Compilation & Preview Polish
> **Goal**: Make the compile → preview cycle fast, smart, and seamless. Add SyncTeX, auto-compile, zoom, and error handling.
> **Estimated Effort**: 2–3 weeks

### 3.1 Auto-Compile with Debounce
Automatically recompile the document a few seconds after the user stops typing. Configurable delay (e.g., 2–5 seconds). Toggle on/off.
- **How**: File watcher or editor `onChange` event → debounce timer → trigger `/api/compile`.

### 3.2 Draft / Fast Compile Mode
Skip image rendering and `hyperref` for faster compilation during active editing. Toggle between Fast and Normal mode.
- **How**: Pass `\PassOptionsToPackage{draft}{graphicx}` prepend or use `latexmk` draft flags.

### 3.3 Stop on First Error
Option to halt compilation on the first error instead of accumulating cascading errors.
- **How**: Pass `-halt-on-error` flag to the TeX engine via `latexmk` config.

### 3.4 Multiple Compile Passes (latexmk)
Automatically run the correct number of compilation passes to resolve cross-references, bibliography, table of contents, and indices.
- **How**: `latexmk -pdf` already handles this. Just use `latexmk` instead of raw `pdflatex`.

### 3.5 Error Log Panel
Parse the `.log` file and display errors (red), warnings (orange), and overfull/underfull boxes (gray) in a structured panel below the editor.
- **How**: Regex-parse the `.log` for `! ...` (errors), `LaTeX Warning:` (warnings). Display in a collapsible panel.

### 3.6 Clickable Error → Line Navigation
Click an error in the log panel → editor scrolls to and highlights the offending line.
- **How**: Extract line numbers from log messages. Wire click handler to `editor.dispatch({ selection })`.

### 3.7 Error Count Badge
Show a badge on the "Logs" button with error/warning counts (e.g., "2 ✗ 3 ⚠").
- **How**: Count parsed items and update a badge element after each compile.

### 3.8 SyncTeX — Forward Sync (Editor → PDF)
Click a button or use `Ctrl+Shift+→` to scroll the PDF to the location corresponding to the cursor's line in the editor.
- **How**: Parse the `.synctex.gz` file (generated by adding `-synctex=1` flag) to map source line → PDF page/coordinates. Scroll `pdf.js` to that position.

### 3.9 SyncTeX — Inverse Sync (PDF → Editor)
Double-click on the PDF → editor jumps to the corresponding source line.
- **How**: On PDF click, compute the page/position, look up in SyncTeX data, dispatch cursor to the mapped line.

### 3.10 PDF Zoom Controls
Zoom in/out with Ctrl+Scroll, pinch gestures, and preset buttons (Fit Page, Fit Width, 50%, 100%, 150%, 200%).
- **How**: `pdf.js` API supports scale changes. Add a zoom toolbar with buttons and a dropdown.

### 3.11 Detach PDF to Separate Tab
Option to open the PDF preview in a new browser tab/window (for multi-monitor setups).
- **How**: `window.open('/pdf/output.pdf')` or serve it at a dedicated URL.

### 3.12 Recompile from Scratch
Button to clear all auxiliary files (`.aux`, `.toc`, `.log`, `.bbl`, etc.) and recompile from zero.
- **How**: Delete glob `*.aux *.toc *.log *.bbl *.blg *.out *.synctex.gz` in the output dir, then recompile.

### 3.13 Compilation Time Display
Show how long the last compilation took (e.g., "Compiled in 3.2s").
- **How**: `performance.now()` or `Date.now()` before/after the compile request.

---

## Phase 4 — File & Project Management
> **Goal**: Handle multiple projects, manage files/folders within a project, and provide a project dashboard.
> **Estimated Effort**: 2–3 weeks

### 4.1 Project Dashboard Page
A landing page listing all projects with title, last-modified date, and tags. Click to open. Supports list/grid view.
- **How**: Scan a root projects directory for project folders. Display metadata (from a `project.json` in each).

### 4.2 Create New Project
Button to create a blank project or from a template. Scaffolds a directory with `main.tex` and basic preamble.
- **How**: Copy a template directory into `/projects/<new-project-name>/`.

### 4.3 File Tree Sidebar
A hierarchical tree view in the left panel showing all files and folders in the current project. Click to open a file in the editor.
- **How**: Recursively read the project directory. Render as a collapsible tree with file-type icons.

### 4.4 Create / Rename / Delete Files & Folders
Right-click context menu on the file tree with New File, New Folder, Rename, Delete actions.
- **How**: Backend endpoints for `mkdir`, `writeFile`, `rename`, `unlink`. Frontend context menu UI.

### 4.5 Upload Files (Drag-and-Drop)
Drag files from desktop into the file tree panel to upload them. Also support a standard file picker button.
- **How**: Handle `dragover`/`drop` events, send files via `FormData` to a `/api/upload` endpoint.

### 4.6 Upload ZIP (Auto-Extract)
Upload a `.zip` file and auto-extract it into the project, preserving directory structure.
- **How**: Backend receives ZIP, uses `adm-zip` or `unzipper` to extract into the project directory.

### 4.7 Download Project as ZIP
One-click download of the entire project source as a `.zip` archive.
- **How**: Backend uses `archiver` to zip the project directory and stream it to the client.

### 4.8 Main Document Selection
A setting to designate which `.tex` file is the compilation entry point (defaults to `main.tex`).
- **How**: Store in `project.json` as `{ "mainFile": "main.tex" }`. Dropdown in project settings.

### 4.9 Project Tagging & Filtering
Assign colored tags (e.g., "Thesis", "Homework", "Report") to projects. Filter dashboard by tag.
- **How**: Store tags in `project.json`. Frontend tag chips with filter logic.

### 4.10 Archive / Trash / Clone Projects
Archive a project (hide from dashboard), trash (soft delete), or clone (duplicate all files).
- **How**: Move to `_archive/` or `_trash/` directories. Clone = copy directory.

### 4.11 Project Rename
Rename a project from the dashboard or within the editor.
- **How**: Rename the project directory + update `project.json`.

---

## Phase 5 — Search, Spell Check, Templates & Bibliography
> **Goal**: Add search capabilities, spell checking, a template library, and citation/bibliography support.
> **Estimated Effort**: 2–3 weeks

### 5.1 Find in Current File
`Ctrl+F` opens a search bar with highlighting, case-sensitivity toggle, regex support, and match navigation.
- **How**: CodeMirror's built-in `search` extension. Zero custom code.

### 5.2 Find and Replace
`Ctrl+H` expands the search bar to include a replace field. Replace one / Replace all.
- **How**: CodeMirror's `search` extension includes replace. No custom code.

### 5.3 Project-Wide Search (Find in All Files)
`Ctrl+Shift+F` opens a sidebar search that scans all text files in the project. Shows results with file name, line number, and context snippet.
- **How**: Backend endpoint that runs `grep -rn` (or equivalent) on the project directory. Frontend renders results as clickable links.

### 5.4 Document Outline / Structure Navigator
A panel showing the document hierarchy (`\chapter`, `\section`, `\subsection`, etc.) as a clickable tree. Auto-updates on each save.
- **How**: Regex-parse the current `.tex` file for `\section{...}`, `\subsection{...}`, etc. Render as a nested list.

### 5.5 Integrated Spell Checker
Wavy red underlines on misspelled words. LaTeX-aware (ignores commands like `\textbf`, `\usepackage`, etc.). Multi-language support.
- **How**: Use `typo.js` (hunspell in JS) or browser's built-in `spellcheck` attribute. Filter out LaTeX commands before checking.

### 5.6 Template Library
A collection of starter templates (IEEE paper, thesis, Beamer presentation, homework, CV, cover letter, lab report). Browse and create new projects from templates.
- **How**: Store template directories in a `templates/` folder. Dashboard shows available templates with preview screenshots.

### 5.7 BibTeX / BibLaTeX Support
Compile with `bibtex` or `biber` automatically when `.bib` files are present. `latexmk` handles this natively.
- **How**: `latexmk` with `-bibtex` flag already does this. Just ensure `biber`/`bibtex` is on PATH.

### 5.8 Citation Key Autocomplete
When typing `\cite{`, show a dropdown of all citation keys from the project's `.bib` files with author/title preview.
- **How**: Parse `.bib` files for `@article{key, ...}` entries on project load. Feed into the autocomplete provider.

### 5.9 Word Count
Menu option or status bar showing word count (via `texcount` or a simple text count).
- **How**: Run `texcount main.tex` on the backend and display the result.

---

## Phase 6 — Checkpoints (Version History) & Settings
> **Goal**: Implement the checkpoint/snapshot system so users can save, browse, and restore previous versions. Also build out the settings panel.
> **Estimated Effort**: 2–3 weeks

### 6.1 Git-Backed Auto-Init
When a new project is created, auto-initialize a Git repository in the project directory. The `.git` folder is hidden from the file tree.
- **How**: `git init` in the project directory on creation. Add `.git` to the file tree ignore list.

### 6.2 Manual Checkpoint (Save Snapshot)
A "Save Checkpoint" button (or `Ctrl+S`) that commits all current changes to the Git repo with an auto-generated message (timestamp + optional user label).
- **How**: `git add -A && git commit -m "Checkpoint: 2026-04-26 14:30:22"` via `simple-git` library.

### 6.3 Checkpoint History Panel
A panel (accessible from the toolbar) showing a chronological list of all checkpoints with timestamp, label (if any), and a summary of changed files.
- **How**: `git log --oneline --all` to get the list. Display in a scrollable sidebar panel.

### 6.4 Restore to Checkpoint
Click "Restore" on any checkpoint in the history panel → reverts the entire project to that state. Current state is auto-checkpointed first (so you don't lose anything).
- **How**: Auto-commit current state → `git checkout <commit-hash> -- .` → refresh editor and file tree.

### 6.5 Diff View Between Checkpoints
Select two checkpoints → see a side-by-side diff of what changed (green = added, red = removed).
- **How**: `git diff <hash1> <hash2>` on the backend. Render with a diff viewer (e.g., `diff2html` library).

### 6.6 Checkpoint Labels
Option to add a descriptive label to a checkpoint (e.g., "Before reformatting", "Submitted v1", "After advisor feedback").
- **How**: Store labels as Git tags or in the commit message. UI to edit labels.

### 6.7 Auto-Save (Periodic)
Auto-save the file to disk every N seconds (configurable). This is NOT a checkpoint — just prevents data loss. Separate from the checkpoint system.
- **How**: Debounced `editor.onChange` → write to disk. No Git commit.

### 6.8 Settings Panel
A comprehensive settings page (accessible from the toolbar) with options for:
- TeX engine selection (pdfLaTeX / XeLaTeX / LuaLaTeX)
- Auto-compile on/off + debounce delay
- Spell check language
- Editor theme (light/dark + color themes)
- Font size, font family, line height
- Keybinding mode (Default / Vim / Emacs)
- Auto-close brackets on/off
- Word wrap on/off
- **How**: Store settings in `localStorage` (browser) or a `settings.json` file. Apply on load.

---

## Phase 7 — Polish, Performance & UX
> **Goal**: Final polish pass. Make everything feel smooth, fast, and premium. Fix edge cases.
> **Estimated Effort**: 1–2 weeks

### 7.1 Keyboard Shortcuts System
Register all keyboard shortcuts consistently. Add a "Keyboard Shortcuts" help dialog (`Ctrl+?` or `F1`) that lists all available shortcuts.
- **How**: Central keybinding registry. Modal dialog with a shortcuts cheat sheet.

### 7.2 TeX Engine Selection per Project
Per-project setting to choose between pdfLaTeX, XeLaTeX, LuaLaTeX. Stored in `project.json`.
- **How**: Dropdown in project settings. Backend reads the engine choice and passes the correct command to `latexmk`.

### 7.3 Multiple Editor Themes
Beyond light/dark: Monokai, Solarized, Dracula, GitHub, One Dark, etc. Selectable from settings.
- **How**: CodeMirror theme packages. Import and switch dynamically.

### 7.4 File Type Icons
Custom icons for `.tex`, `.bib`, `.png`, `.jpg`, `.pdf`, `.sty`, `.cls` in the file tree.
- **How**: Map file extensions to SVG icons. Apply in the tree renderer.

### 7.5 Image Preview on Hover
Hovering over an image file in the file tree shows a thumbnail tooltip.
- **How**: Generate thumbnails on the backend (or use the raw file) and show via CSS tooltip on hover.

### 7.6 Cursor Position in Status Bar
Show `Ln 42, Col 15` in a status bar at the bottom of the editor.
- **How**: CodeMirror cursor position events → update a DOM element.

### 7.7 PDF Page Navigation
Page number display, "Go to page" input, previous/next page buttons.
- **How**: `pdf.js` API provides page count and navigation. Build a small toolbar.

### 7.8 PDF Text Selection & Copy
Allow selecting and copying text from the rendered PDF.
- **How**: `pdf.js` text layer is enabled by default. Just ensure it's not disabled.

### 7.9 Responsive Layout
Ensure the UI works reasonably on tablets and smaller screens.
- **How**: CSS media queries. Collapse sidebar on narrow screens. Stack panels vertically.

### 7.10 Loading States & Progress Indicators
Show spinner during compilation, progress bar for long operations, skeleton loaders for initial page load.
- **How**: CSS spinners, `fetch` progress events, transition animations.

### 7.11 Print PDF
Button to trigger the browser's print dialog for the currently previewed PDF.
- **How**: `window.print()` on the PDF iframe/tab, or use `pdf.js` print functionality.

---

## A Far Far Future Plan 🔮
> **These features are genuinely difficult to build and are NOT needed for a personal-use LaTeX editor. Listed here only for completeness. Do not attempt until everything above is rock-solid.**

### FF.1 Visual / WYSIWYG Editor
A rich-text editing mode where the user sees rendered output instead of LaTeX code. Toggle between Code and Visual.
- **Difficulty**: Extreme. Requires bidirectional LaTeX↔DOM transformation.
- **If ever built**: Use ProseMirror + a custom LaTeX schema. Multi-year effort.

### FF.2 Real-Time Collaborative Editing
Multiple users editing the same document simultaneously (like Google Docs).
- **Difficulty**: Extreme. Requires OT/CRDT, WebSocket infrastructure, conflict resolution.
- **If ever built**: Use Yjs + WebSocket server + CodeMirror Yjs binding.

### FF.3 Track Changes (Accept/Reject)
Track all edits with colored highlights. Accept or reject each change individually.
- **Difficulty**: Very hard. Character-level diff tracking with provenance.
- **If ever built**: Store edit operations as a log. Render inline with accept/reject buttons.

### FF.4 Comments & Annotations
Select text and attach threaded comments in a sidebar.
- **Difficulty**: Hard. Need to handle range invalidation as text is edited.
- **If ever built**: Store comments keyed to text ranges. Use decorations in CodeMirror.

### FF.5 User Presence Indicators
See where other users' cursors are in real-time.
- **Difficulty**: Hard. Requires the real-time sync infrastructure from FF.2.

### FF.6 GUI Table Editor
A point-and-click table editor that generates LaTeX `tabular` code.
- **Difficulty**: Hard. Two-way sync between GUI and LaTeX source.

### FF.7 Rich Text Formatting Toolbar
Bold, italic, list buttons that generate correct LaTeX commands.
- **Difficulty**: Hard. Deep coupling between toolbar actions and LaTeX AST.

### FF.8 Copy-Paste from Word / Google Docs
Paste rich text and auto-convert to LaTeX.
- **Difficulty**: Hard. Robust HTML/RTF → LaTeX parser needed.

### FF.9 Direct Journal Submission
Submit to IEEE, Springer, Elsevier directly from the app.
- **Difficulty**: Hard. Requires individual publisher API integrations. Not worth building.

---

> **Total: 7 phases + Far Future = ~65 features across the entire roadmap.**
>
> Phase 1 alone gives you a working LaTeX editor. Each subsequent phase adds a meaningful layer of capability.
