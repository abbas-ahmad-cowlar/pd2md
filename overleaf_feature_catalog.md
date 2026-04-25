# Overleaf Feature Catalog — Exhaustive A-to-Z Breakdown

> **Purpose**: Document every single feature of Overleaf (the online LaTeX editor), from the most obvious to the smallest quality-of-life detail, and assess feasibility of replicating each feature in a locally-hosted, free, open-source alternative.
>
> **Date**: 2026-04-26

---

## Legend — Feasibility Ratings

| Symbol | Meaning |
|--------|---------|
| ✅ EASY | Can be built/integrated with existing open-source tools in < 1 week |
| 🟡 MODERATE | Requires meaningful engineering effort (1–4 weeks) |
| 🔴 HARD | Requires significant infrastructure, R&D, or is impractical to replicate |
| 🟢 FREE EXISTING | Already exists as a free, open-source tool we can just use |

---

## Table of Contents

1. [Core Platform (No-Install LaTeX)](#1-core-platform)
2. [Code Editor Features](#2-code-editor-features)
3. [Visual / Rich-Text Editor](#3-visual-rich-text-editor)
4. [PDF Preview & Compilation](#4-pdf-preview--compilation)
5. [Search & Navigation](#5-search--navigation)
6. [Layout & UI Customization](#6-layout--ui-customization)
7. [Project Management](#7-project-management)
8. [File & Folder Management](#8-file--folder-management)
9. [Collaboration Features](#9-collaboration-features)
10. [Version Control & History](#10-version-control--history)
11. [Templates & Gallery](#11-templates--gallery)
12. [Bibliography & Citations](#12-bibliography--citations)
13. [External Integrations](#13-external-integrations)
14. [Error Handling & Logs](#14-error-handling--logs)
15. [Editor Settings & Customization](#15-editor-settings--customization)
16. [Keyboard Shortcuts](#16-keyboard-shortcuts)
17. [Learning Resources & Documentation](#17-learning-resources--documentation)
18. [Account & Access Management](#18-account--access-management)
19. [Security & Infrastructure](#19-security--infrastructure)
20. [Miscellaneous / Hidden Gems](#20-miscellaneous--hidden-gems)

---

## 1. Core Platform

These are the foundational features that define what Overleaf *is*.

### 1.1 No Local Installation Required
- **What**: Access a full LaTeX environment via a web browser. No need to install TeX Live, MiKTeX, MacTeX, or any packages locally.
- **Why it matters**: Eliminates the #1 barrier to LaTeX adoption — the painful installation and PATH configuration of local distributions.
- **Local Build Feasibility**: ✅ EASY — Install TeX Live or MiKTeX once on the server/local machine. Docker makes this trivial (`texlive/texlive` image).

### 1.2 Cloud-Based Storage
- **What**: All projects are stored on Overleaf's servers. Accessible from any device with internet.
- **Why it matters**: No risk of losing work due to local disk failures. Work from any machine.
- **Local Build Feasibility**: ✅ EASY — Use local filesystem, or a simple SQLite/MongoDB database for metadata. For "online" mode, just add a server with file storage.

### 1.3 Cross-Platform Access
- **What**: Works on Windows, macOS, Linux, Chromebooks, tablets — any device with a modern browser.
- **Why it matters**: No platform-specific builds or installers.
- **Local Build Feasibility**: ✅ EASY — If we build a web app, this is automatic. Even a local Electron app would be cross-platform.

### 1.4 Multiple TeX Engine Support
- **What**: Choose between pdfLaTeX, XeLaTeX, LuaLaTeX for compilation.
- **Why it matters**: Different engines handle fonts, Unicode, and packages differently. XeLaTeX/LuaLaTeX are essential for non-Latin scripts.
- **Local Build Feasibility**: ✅ EASY — TeX Live ships all engines. Just expose them as a dropdown option.

### 1.5 Automatic Package Management
- **What**: Overleaf's TeX Live installation includes virtually all CTAN packages. No need to manually install packages with `tlmgr`.
- **Why it matters**: `\usepackage{tikz}` just works. No "Package not found" errors.
- **Local Build Feasibility**: ✅ EASY — Install the full TeX Live distribution (~5 GB). Or use `tlmgr` to auto-install on demand.

### 1.6 Instant Project Creation
- **What**: Create a new blank project or from a template in one click.
- **Why it matters**: Zero friction to start writing.
- **Local Build Feasibility**: ✅ EASY — Scaffold a directory with a default `.tex` file and open it.

---

## 2. Code Editor Features

The raw LaTeX code editing experience.

### 2.1 Syntax Highlighting
- **What**: LaTeX commands, environments, comments, math delimiters, and strings are color-coded.
- **Why it matters**: Dramatically improves readability and error detection.
- **Local Build Feasibility**: 🟢 FREE EXISTING — CodeMirror 6 (which Overleaf itself uses), Monaco Editor (VS Code's engine), or Ace Editor all provide LaTeX syntax highlighting out of the box.

### 2.2 LaTeX Autocomplete
- **What**: As you type `\begin{`, `\usepackage{`, `\cite{`, etc., a dropdown suggests completions for commands, environments, labels, and citation keys.
- **Why it matters**: Saves time, reduces typos, helps discover commands.
- **Local Build Feasibility**: 🟡 MODERATE — CodeMirror supports custom autocomplete providers. Building a comprehensive LaTeX command dictionary + context-aware completions (e.g., only suggesting `\item` inside `itemize`) requires effort.

### 2.3 Auto-Close Brackets & Delimiters
- **What**: Typing `{` automatically inserts `}`. Same for `(`, `[`, `$`, and `\begin{env}` → `\end{env}`.
- **Why it matters**: Prevents mismatched delimiters, the #1 LaTeX compilation error.
- **Local Build Feasibility**: ✅ EASY — Built-in feature of CodeMirror and Monaco.

### 2.4 Bracket Matching / Highlighting
- **What**: When cursor is on a bracket, the matching bracket is highlighted.
- **Why it matters**: Navigate complex nested structures.
- **Local Build Feasibility**: ✅ EASY — Built-in to CodeMirror / Monaco.

### 2.5 Line Numbers
- **What**: Line numbers displayed in the gutter on the left side of the editor.
- **Why it matters**: Essential for navigating error messages ("Error on line 247").
- **Local Build Feasibility**: ✅ EASY — Default in all major code editors.

### 2.6 Code Folding
- **What**: Collapse/expand sections, environments (`\begin{...}...\end{...}`), and structural elements (chapters, sections).
- **Why it matters**: Focus on the section you're editing without scrolling past hundreds of lines.
- **Local Build Feasibility**: 🟡 MODERATE — CodeMirror supports folding, but you need a custom fold provider that understands LaTeX structure (`\section`, `\begin`/`\end` pairs).

### 2.7 Multiple Cursors / Multi-Select
- **What**: Place multiple cursors and edit multiple locations simultaneously (Ctrl+D to select next occurrence).
- **Why it matters**: Batch editing of repeated patterns.
- **Local Build Feasibility**: ✅ EASY — Built into CodeMirror 6 and Monaco.

### 2.8 Comment / Uncomment Toggle
- **What**: Select lines and press `Ctrl+/` to toggle `%` comment prefix.
- **Why it matters**: Quick way to disable/enable blocks of code during debugging.
- **Local Build Feasibility**: ✅ EASY — Trivial keybinding + string manipulation.

### 2.9 Indent / Dedent Selection
- **What**: Tab / Shift+Tab to adjust indentation of selected lines.
- **Why it matters**: Keep code clean and readable.
- **Local Build Feasibility**: ✅ EASY — Built into CodeMirror / Monaco.

### 2.10 Word Wrap / Soft Wrap
- **What**: Long lines wrap visually without inserting line breaks.
- **Why it matters**: Prevents horizontal scrolling for long paragraphs.
- **Local Build Feasibility**: ✅ EASY — Editor setting toggle.

### 2.11 Integrated Spell Checker
- **What**: Wavy red underlines on misspelled words, with multi-language support. Language selectable per-project or globally.
- **Why it matters**: Catch typos before compilation.
- **Local Build Feasibility**: 🟡 MODERATE — Browser has built-in spellcheck. For richer support (LaTeX-aware, ignoring commands), integrate `hunspell` or a similar dictionary engine, filtering out LaTeX markup.

### 2.12 Emacs / Vim Keybinding Modes
- **What**: Optional Vim or Emacs keybinding modes for power users.
- **Why it matters**: Users with muscle memory for these editors can stay productive.
- **Local Build Feasibility**: ✅ EASY — CodeMirror has official Vim and Emacs extensions. Monaco has a Vim plugin.

### 2.13 Undo / Redo
- **What**: Standard Ctrl+Z / Ctrl+Shift+Z with deep undo history per editing session.
- **Why it matters**: Fearless editing — revert any mistake instantly.
- **Local Build Feasibility**: ✅ EASY — Built into all code editors.

### 2.14 Copy / Cut / Paste with LaTeX Awareness
- **What**: Standard clipboard operations that preserve LaTeX formatting. Pasting from external sources (Word, Google Docs) into Visual Editor converts to LaTeX.
- **Why it matters**: Seamless content migration.
- **Local Build Feasibility**: 🟡 MODERATE — Basic clipboard is free. Rich-text-to-LaTeX conversion (e.g., pasting HTML tables) requires a parser.

### 2.15 Go-to-Line
- **What**: Ctrl+Shift+L opens a dialog to jump to a specific line number.
- **Why it matters**: Essential when error logs reference specific line numbers.
- **Local Build Feasibility**: ✅ EASY — Standard editor feature.

---

## 3. Visual / Rich-Text Editor

Overleaf's WYSIWYG-like editing mode that hides raw LaTeX from the user.

### 3.1 Toggle Between Code & Visual Editor
- **What**: A switch in the toolbar lets you flip between raw LaTeX code and a rich-text view instantly. No data loss between switches.
- **Why it matters**: Beginners can use the visual editor; experts can drop into code. Both work on the same source.
- **Local Build Feasibility**: 🔴 HARD — This requires building a full LaTeX-to-visual DOM renderer and a reverse DOM-to-LaTeX serializer. This is the single hardest feature to replicate. Overleaf invested years into this.

### 3.2 Inline Math Rendering
- **What**: Math expressions like `$E = mc^2$` render as typeset equations directly in the visual editor, not just in the PDF.
- **Why it matters**: See your math without compiling.
- **Local Build Feasibility**: 🟡 MODERATE — Use KaTeX or MathJax to render `$...$` and `\[...\]` inline. The challenge is integrating this smoothly with the editor so it's editable, not just a preview.

### 3.3 Table Editor (GUI)
- **What**: Insert tables via a point-and-click grid selector. Add/remove rows and columns, merge cells, set borders, adjust column widths — all without writing `\begin{tabular}`.
- **Why it matters**: LaTeX tables are notoriously painful to write by hand.
- **Local Build Feasibility**: 🔴 HARD — Building a GUI table editor that generates clean LaTeX `tabular`/`tabularx` code and stays in sync with the source is extremely complex.

### 3.4 Figure Insertion Dialog
- **What**: Click "Insert Figure" → choose upload from computer, pick from project files, or paste a URL. Configure caption, label, width, and placement (`[h]`, `[t]`, `[b]`, `[p]`) via GUI.
- **Why it matters**: No need to memorize `\includegraphics` syntax.
- **Local Build Feasibility**: 🟡 MODERATE — A modal dialog that generates the `\begin{figure}...\end{figure}` LaTeX snippet and inserts it. Not trivial but doable.

### 3.5 Drag-and-Drop Image Upload
- **What**: Drag an image file from your desktop directly into the editor. It auto-uploads and inserts the `\includegraphics` command.
- **Why it matters**: Eliminates the tedious upload → reference cycle.
- **Local Build Feasibility**: 🟡 MODERATE — Handle the `drop` event, save the file to the project directory, generate the LaTeX include code.

### 3.6 Copy-Paste Image Support
- **What**: Copy an image from your clipboard (e.g., screenshot) and paste it directly into the editor.
- **Why it matters**: Lightning-fast workflow for screenshots and diagrams.
- **Local Build Feasibility**: 🟡 MODERATE — Read clipboard image data, save as a file, insert LaTeX reference.

### 3.7 Rich Text Formatting Toolbar
- **What**: Buttons for Bold, Italic, underline, bullet lists, numbered lists, headings, hyperlinks — all generating correct LaTeX underneath.
- **Why it matters**: Word-processor familiarity for non-LaTeX users.
- **Local Build Feasibility**: 🔴 HARD — Each button needs to generate/modify the correct LaTeX command. Requires a deep mapping between visual formatting and LaTeX markup.

### 3.8 Cross-Reference Insertion
- **What**: In the visual editor, you can insert `\ref{label}` by browsing existing labels in the project.
- **Why it matters**: No need to remember label names.
- **Local Build Feasibility**: 🟡 MODERATE — Parse `.aux` files or scan `.tex` sources for `\label{...}` and present them in a dropdown.

### 3.9 Copy-Paste from Word / Google Docs
- **What**: Paste rich text from external word processors and it converts to appropriate LaTeX (bold → `\textbf`, lists → `\begin{itemize}`, etc.).
- **Why it matters**: Migrate existing documents into LaTeX without manual conversion.
- **Local Build Feasibility**: 🔴 HARD — Requires a robust HTML/RTF-to-LaTeX converter that handles edge cases.

---

## 4. PDF Preview & Compilation

The compilation pipeline and live preview system.

### 4.1 Auto-Compile (Live Preview)
- **What**: The document automatically recompiles every few seconds as you type. The PDF updates in near-real-time.
- **Why it matters**: See the effect of your changes without manually pressing "Compile".
- **Local Build Feasibility**: 🟡 MODERATE — Use a file watcher (e.g., `chokidar` / `nodemon`) to trigger `pdflatex` on save or after a debounce period. The compilation itself can take 2–30 seconds depending on document complexity.

### 4.2 Manual Compile Button
- **What**: A "Recompile" button to trigger compilation on demand.
- **Why it matters**: Sometimes you want to batch your changes before compiling (especially for heavy documents).
- **Local Build Feasibility**: ✅ EASY — A button that shells out to `pdflatex`/`xelatex`/`lualatex`.

### 4.3 Draft / Fast Compile Mode
- **What**: A "Fast [draft]" mode that skips image rendering (replaces with blank boxes) and disables `hyperref`. Dramatically faster compilation.
- **Why it matters**: Large documents with many high-res images can take 30+ seconds to compile. Draft mode gets you a preview in seconds.
- **Local Build Feasibility**: ✅ EASY — Pass `\PassOptionsToPackage{draft}{graphicx}` or use `\documentclass[draft]{...}` flag.

### 4.4 Stop on First Error
- **What**: Option to halt compilation at the first error instead of continuing and accumulating cascading errors.
- **Why it matters**: Makes debugging much easier — focus on one error at a time.
- **Local Build Feasibility**: ✅ EASY — Pass `-halt-on-error` or `-interaction=nonstopmode` flag to the TeX engine.

### 4.5 Embedded PDF Viewer
- **What**: The compiled PDF is displayed in a panel alongside the code editor. No need for an external PDF reader.
- **Why it matters**: Side-by-side code + output is the core Overleaf experience.
- **Local Build Feasibility**: 🟡 MODERATE — Use `pdf.js` (Mozilla's open-source PDF renderer) embedded in the web app. It supports rendering, zooming, scrolling, and text selection.

### 4.6 PDF Zoom (In/Out)
- **What**: Zoom the PDF preview using Ctrl+Scroll, pinch gestures, or a zoom menu with presets (Fit Page, Fit Width, 100%, 150%, etc.).
- **Why it matters**: Read fine print or get an overview of the page layout.
- **Local Build Feasibility**: ✅ EASY — `pdf.js` supports zoom natively. Just expose the controls.

### 4.7 SyncTeX — Editor to PDF (Forward Sync)
- **What**: Click "Show in PDF" or a toolbar button, and the PDF viewer scrolls to the location corresponding to your cursor position in the source code.
- **Why it matters**: "I'm editing line 247 — show me what that looks like in the PDF."
- **Local Build Feasibility**: 🟡 MODERATE — SyncTeX is an open-source tool that generates `.synctex.gz` files during compilation. Parse them to map source lines → PDF coordinates. Libraries exist (`synctex-parser`).

### 4.8 SyncTeX — PDF to Editor (Inverse Sync)
- **What**: Double-click on any element in the PDF preview and the editor jumps to the corresponding source line.
- **Why it matters**: "I see a typo in the PDF — take me to the source code."
- **Local Build Feasibility**: 🟡 MODERATE — Same SyncTeX infrastructure, just in the reverse direction. Need to handle click coordinates → PDF page position → source line mapping.

### 4.9 PDF Download
- **What**: Download the compiled PDF with one click.
- **Why it matters**: The whole point — get the final document.
- **Local Build Feasibility**: ✅ EASY — Serve the output `.pdf` file from the compilation directory.

### 4.10 Detach PDF to Separate Tab/Window
- **What**: Open the PDF preview in a separate browser tab or window. Useful for multi-monitor setups.
- **Why it matters**: Full-screen code on one monitor, full-screen PDF on another.
- **Local Build Feasibility**: ✅ EASY — Open a new window/tab pointing to the PDF URL.

### 4.11 Multiple Compile Passes
- **What**: Overleaf automatically runs multiple compilation passes (pdflatex → bibtex/biber → pdflatex × 2) to resolve cross-references, bibliographies, and table of contents.
- **Why it matters**: LaTeX requires multiple passes to resolve `\ref`, `\cite`, `\tableofcontents`. New users don't know this.
- **Local Build Feasibility**: ✅ EASY — Script the standard `pdflatex → bibtex → pdflatex → pdflatex` pipeline. Tools like `latexmk` automate this perfectly.

### 4.12 Recompile from Scratch
- **What**: Clear all generated files (`.aux`, `.toc`, `.bbl`, `.log`, etc.) and recompile from zero.
- **Why it matters**: Stale auxiliary files sometimes cause phantom errors.
- **Local Build Feasibility**: ✅ EASY — Delete `*.aux *.toc *.log *.bbl *.blg *.out *.synctex.gz` and rerun.

---

## 5. Search & Navigation

Finding things in your code and project.

### 5.1 Find in Current File
- **What**: `Ctrl+F` opens a search bar at the bottom of the editor. Highlights all matches. Navigate with Enter / Shift+Enter.
- **Why it matters**: Basic but essential.
- **Local Build Feasibility**: ✅ EASY — Built into CodeMirror / Monaco.

### 5.2 Find and Replace in Current File
- **What**: `Ctrl+H` (or expand the search bar) to find and replace text. Supports:
  - Case-sensitive toggle
  - Whole word matching
  - Regular expression support
  - Replace one / Replace all
- **Why it matters**: Batch rename variables, fix repeated typos.
- **Local Build Feasibility**: ✅ EASY — Built into CodeMirror / Monaco.

### 5.3 Project-Wide Search (Find in All Files)
- **What**: `Ctrl+Shift+F` opens a project-wide search panel in the sidebar. Searches across all `.tex`, `.bib`, `.sty`, and other text files (under 2 MB) in the project.
- **Why it matters**: Find where a label is defined, where a command is used, etc.
- **Local Build Feasibility**: 🟡 MODERATE — Implement a backend search using `grep` or a simple recursive file search. Display results with file name, line number, and context snippet.

### 5.4 File Outline / Document Structure Navigator
- **What**: A panel (bottom of the file tree) that shows the hierarchical structure of the current `.tex` file: `\chapter`, `\section`, `\subsection`, etc. Click to jump to that section.
- **Why it matters**: Navigate long documents (50+ pages) without scrolling.
- **Local Build Feasibility**: 🟡 MODERATE — Parse the current `.tex` file for sectioning commands and build a tree. Update on each save.

### 5.5 Go-to-Line Number
- **What**: `Ctrl+Shift+L` opens a dialog to jump to a specific line.
- **Why it matters**: Error messages reference line numbers.
- **Local Build Feasibility**: ✅ EASY — Standard CodeMirror/Monaco feature.

### 5.6 Clickable Error Navigation
- **What**: Click on an error/warning in the compilation log, and the editor jumps to the offending line.
- **Why it matters**: Eliminates manual line searching.
- **Local Build Feasibility**: 🟡 MODERATE — Parse the `.log` file for error line numbers. Create clickable links that trigger `editor.scrollToLine()`.

---

## 6. Layout & UI Customization

How you arrange the workspace.

### 6.1 Resizable Editor / Preview Panels
- **What**: Drag the vertical divider between the code editor and PDF preview to allocate more space to either side.
- **Why it matters**: Writing-heavy? Make the editor wider. Reviewing? Make the PDF wider.
- **Local Build Feasibility**: ✅ EASY — CSS `resize` or a JS draggable divider (e.g., `split.js` library). Very straightforward.

### 6.2 Three Layout Modes
- **What**: Toggle between:
  - **Split View**: Editor + PDF side by side (default)
  - **Editor Only**: Full-screen code editor, PDF hidden
  - **PDF Only**: Full-screen PDF preview, editor hidden
- **Why it matters**: Maximize focus for the task at hand.
- **Local Build Feasibility**: ✅ EASY — CSS class toggles to show/hide panels.

### 6.3 Collapsible File Tree
- **What**: The left sidebar (file tree) can be collapsed/expanded to give more horizontal space to the editor.
- **Why it matters**: On small screens, every pixel counts.
- **Local Build Feasibility**: ✅ EASY — Toggle sidebar visibility.

### 6.4 Light / Dark Theme
- **What**: Choose between light and dark color schemes for the editor interface.
- **Why it matters**: Dark mode reduces eye strain for late-night writing sessions.
- **Local Build Feasibility**: ✅ EASY — CodeMirror and Monaco both support theme switching. Add a CSS variable-based theme system.

### 6.5 Multiple Editor Themes
- **What**: Beyond just light/dark, choose from various color themes (e.g., Monokai, Solarized, Dracula, GitHub, etc.).
- **Why it matters**: Personal preference and accessibility.
- **Local Build Feasibility**: ✅ EASY — CodeMirror has many community themes. Monaco inherits VS Code themes.

### 6.6 Adjustable Font Size
- **What**: Increase or decrease the editor font size from settings.
- **Why it matters**: Accessibility and readability on different screen sizes/resolutions.
- **Local Build Feasibility**: ✅ EASY — CSS `font-size` property on the editor container.

### 6.7 Adjustable Font Family
- **What**: Choose between monospace fonts (e.g., Source Code Pro, Fira Code, Courier New) for the editor.
- **Why it matters**: Some fonts have better ligature support or readability.
- **Local Build Feasibility**: ✅ EASY — CSS `font-family` + bundled web fonts.

### 6.8 Adjustable Line Height
- **What**: Configure the spacing between lines in the editor.
- **Why it matters**: Dense or spacious layout preference.
- **Local Build Feasibility**: ✅ EASY — CSS `line-height` property.

---

## 7. Project Management

Managing multiple LaTeX projects.

### 7.1 Project Dashboard
- **What**: A landing page listing all your projects with title, last modified date, owner, and tags. Projects displayed in a list or grid view.
- **Why it matters**: Quick overview and access to all your work.
- **Local Build Feasibility**: ✅ EASY — A simple page that lists directories/projects from the filesystem or a database.

### 7.2 Create New Project
- **What**: Options to create:
  - Blank project
  - Project from template
  - Upload a `.zip` project
  - Import from GitHub (premium)
- **Why it matters**: Multiple entry points for starting work.
- **Local Build Feasibility**: ✅ EASY — Directory creation with template files.

### 7.3 Project Tagging / Labels
- **What**: Assign colored tags (e.g., "Thesis", "Journal Paper", "Class Notes") to projects for organization and filtering.
- **Why it matters**: When you have 50+ projects, tags are essential.
- **Local Build Feasibility**: ✅ EASY — Store tags in a JSON config or database. Filter UI is straightforward.

### 7.4 Project Search & Filter
- **What**: Search projects by name, filter by tag, sort by date modified / created / name.
- **Why it matters**: Find the right project fast.
- **Local Build Feasibility**: ✅ EASY — Client-side filtering of the project list.

### 7.5 Archive / Trash Projects
- **What**: Archive projects to hide them from the dashboard without deleting. Trash for soft-delete with recovery.
- **Why it matters**: Keep the dashboard clean without losing work.
- **Local Build Feasibility**: ✅ EASY — Move to an `_archive` or `_trash` directory, or set a flag in metadata.

### 7.6 Copy / Clone a Project
- **What**: Duplicate an entire project (all files, settings) to create a variant.
- **Why it matters**: Start a revised version without risking the original.
- **Local Build Feasibility**: ✅ EASY — Copy the project directory.

### 7.7 Rename a Project
- **What**: Change the project title from the dashboard or within the editor.
- **Why it matters**: Keep projects organized as scope changes.
- **Local Build Feasibility**: ✅ EASY — Rename the directory or update metadata.

### 7.8 Download Project as ZIP
- **What**: Download the entire project source (all `.tex`, `.bib`, images, etc.) as a `.zip` archive.
- **Why it matters**: Backup or migrate to a different editor/system.
- **Local Build Feasibility**: ✅ EASY — Use `archiver` or the built-in `zip` command.

### 7.9 Project Word Count
- **What**: Menu option to display the word count of the compiled document (via `texcount`).
- **Why it matters**: Many journals and theses have word limits.
- **Local Build Feasibility**: ✅ EASY — Run `texcount main.tex` and display the result.

---

## 8. File & Folder Management

Working with files and directories inside a project.

### 8.1 File Tree Panel
- **What**: A sidebar showing all project files and folders in a hierarchical tree with expand/collapse.
- **Why it matters**: Navigate complex multi-file projects (thesis chapters, appendices, etc.).
- **Local Build Feasibility**: ✅ EASY — Recursively list the project directory. Many tree-view JS components exist (e.g., `react-treebeard`, vanilla JS solutions).

### 8.2 Create New File
- **What**: Right-click or button to create a new `.tex`, `.bib`, `.sty`, or any other file.
- **Why it matters**: Add chapters, bibliography files, custom style files.
- **Local Build Feasibility**: ✅ EASY — File creation API.

### 8.3 Create New Folder
- **What**: Organize files into folders (e.g., `images/`, `chapters/`, `appendices/`).
- **Why it matters**: Keep large projects manageable.
- **Local Build Feasibility**: ✅ EASY — Directory creation.

### 8.4 Rename Files & Folders
- **What**: Right-click → Rename.
- **Why it matters**: Refactor project structure.
- **Local Build Feasibility**: ✅ EASY — File/directory rename API. Note: Should also update `\include{}` references (advanced).

### 8.5 Delete Files & Folders
- **What**: Right-click → Delete with confirmation.
- **Why it matters**: Remove obsolete files.
- **Local Build Feasibility**: ✅ EASY — File deletion with confirmation dialog.

### 8.6 Upload Files
- **What**: Upload button and drag-and-drop to add files to the project. Supports uploading entire folders (preserving directory structure).
- **Why it matters**: Add images, data files, bibliography databases.
- **Local Build Feasibility**: ✅ EASY — Standard HTML file upload with `<input type="file">` or drag-and-drop zone.

### 8.7 Upload a ZIP (Preserve Structure)
- **What**: Upload a `.zip` file and it auto-extracts into the project, preserving folder structure.
- **Why it matters**: Migrate existing local projects.
- **Local Build Feasibility**: ✅ EASY — Extract ZIP server-side with `adm-zip` or similar.

### 8.8 File Type Icons
- **What**: Different icons for `.tex`, `.bib`, `.png`, `.jpg`, `.pdf`, `.sty`, `.cls` files in the tree.
- **Why it matters**: Visual identification at a glance.
- **Local Build Feasibility**: ✅ EASY — Map file extensions to icons (e.g., VS Code's file icon theme).

### 8.9 Main Document Selection
- **What**: Designate which `.tex` file is the "main document" (the one the compiler starts from).
- **Why it matters**: Multi-file projects need a root file (e.g., `main.tex` that `\include`s chapters).
- **Local Build Feasibility**: ✅ EASY — A setting/config that specifies the entry point `.tex` file.

### 8.10 File Size & Count Limits
- **What**: Overleaf limits: 2,000 files per project, 50 MB per upload, individual files must be under certain sizes.
- **Why it matters**: Guardrails to prevent abuse on shared infrastructure.
- **Local Build Feasibility**: ✅ EASY — We can set our own limits (or have none — it's our machine).

---

## 9. Collaboration Features

Real-time multi-user editing and review tools.

### 9.1 Real-Time Collaborative Editing
- **What**: Multiple users edit the same document simultaneously. Changes from each user appear in real-time (like Google Docs). Uses Operational Transformation (OT) to merge concurrent edits without conflicts.
- **Why it matters**: Co-authoring papers without emailing files back and forth.
- **Local Build Feasibility**: 🔴 HARD — Implementing OT or CRDT (Conflict-free Replicated Data Types) for real-time sync is extremely complex. Libraries like `Yjs` or `ShareDB` can help, but integrating them with a LaTeX-aware editor is a major project.

### 9.2 User Cursors / Presence Indicators
- **What**: See where each collaborator's cursor is in the document, with their name and a colored highlight.
- **Why it matters**: Know who is editing what — avoid stepping on each other's toes.
- **Local Build Feasibility**: 🔴 HARD — Requires the real-time sync infrastructure (9.1) plus cursor position broadcasting via WebSocket.

### 9.3 Sharing via Link
- **What**: Generate a shareable link with configurable permissions (Edit, Review, or View-only).
- **Why it matters**: Invite collaborators without requiring them to have an Overleaf account.
- **Local Build Feasibility**: 🟡 MODERATE — Generate a unique token URL. Requires authentication/authorization middleware if running as a server.

### 9.4 Sharing via Email Invitation
- **What**: Invite specific email addresses with role-based permissions (Editor, Reviewer, Viewer).
- **Why it matters**: Controlled access — only authorized people can edit.
- **Local Build Feasibility**: 🟡 MODERATE — Requires user accounts + email sending (SMTP integration).

### 9.5 Comments / Annotations
- **What**: Select text in the document and add a comment. Comments appear in a sidebar. Other collaborators can reply, creating threaded discussions.
- **Why it matters**: Discuss specific passages without modifying the document.
- **Local Build Feasibility**: 🟡 MODERATE — Store comments as metadata (keyed to text ranges). Display in a sidebar. Need to handle range invalidation when text is edited.

### 9.6 Resolve / Delete Comments
- **What**: Mark a comment as resolved (hides it) or permanently delete it.
- **Why it matters**: Keep the comment sidebar clean after addressing feedback.
- **Local Build Feasibility**: ✅ EASY — Toggle a flag on the comment object.

### 9.7 Track Changes (Review Mode)
- **What**: Premium feature. When enabled, all edits are tracked with colored highlights (insertions in green, deletions in red with strikethrough). The document owner can Accept or Reject each change.
- **Why it matters**: Formal review workflow for advisors reviewing student theses, co-authors reviewing sections, etc.
- **Local Build Feasibility**: 🔴 HARD — Requires diff tracking at the character level, storing change provenance, and a UI for accept/reject. Very complex to build from scratch.

### 9.8 Role-Based Permissions
- **What**: Three roles:
  - **Owner**: Full control (settings, delete, share)
  - **Editor**: Can edit content
  - **Reviewer**: Can only comment and use track changes
  - **Viewer**: Read-only
- **Why it matters**: Control who can change what.
- **Local Build Feasibility**: 🟡 MODERATE — Requires user authentication and authorization middleware.

### 9.9 Notification of Collaborator Activity
- **What**: Email notifications when collaborators make edits or leave comments.
- **Why it matters**: Stay informed without constantly checking.
- **Local Build Feasibility**: 🟡 MODERATE — Requires SMTP integration and event tracking.

---

## 10. Version Control & History

Tracking changes over time.

### 10.1 Automatic Version Snapshots
- **What**: Overleaf automatically saves snapshots of the project at regular intervals (typically every few minutes of active editing).
- **Why it matters**: Never lose work — even if you don't manually save.
- **Local Build Feasibility**: 🟡 MODERATE — Implement periodic auto-commits to a local Git repository, or maintain a simple snapshot system (copy project state to a timestamped directory).

### 10.2 Full Project History Timeline
- **What**: Premium feature. A timeline view showing all changes over time. Scrub through the history to see the project at any point in time.
- **Why it matters**: "What did the document look like last Tuesday?"
- **Local Build Feasibility**: 🟡 MODERATE — If using Git, `git log` + `git show` provides this. Build a UI timeline on top.

### 10.3 Diff View (Compare Versions)
- **What**: Compare two versions side by side with highlighted additions (green) and deletions (red).
- **Why it matters**: See exactly what changed between versions.
- **Local Build Feasibility**: 🟡 MODERATE — Use `diff` or `jsdiff` library to compute text diffs. Render with syntax highlighting.

### 10.4 Restore Previous Versions
- **What**: Click "Restore" on any historical version to revert the entire project (or individual files) to that state.
- **Why it matters**: Undo catastrophic edits or recover deleted content.
- **Local Build Feasibility**: ✅ EASY — `git checkout <commit>` or copy from snapshot directory.

### 10.5 Version Labels (Named Snapshots)
- **What**: Manually label specific versions with descriptive names (e.g., "Submitted to ICML", "After reviewer feedback", "Final draft v3").
- **Why it matters**: Milestones are easier to find than timestamps.
- **Local Build Feasibility**: ✅ EASY — `git tag -a "v1.0" -m "Submitted to ICML"` or equivalent metadata.

### 10.6 Per-User Change Attribution
- **What**: See which user made each change in the history (color-coded by author).
- **Why it matters**: Accountability in multi-author projects.
- **Local Build Feasibility**: 🟡 MODERATE — Git tracks author by default. Need UI to display per-user contributions.

### 10.7 Git Integration (Premium)
- **What**: Sync your Overleaf project with a Git repository. Clone, push, pull directly.
- **Why it matters**: Use professional version control workflows alongside Overleaf.
- **Local Build Feasibility**: 🟢 FREE EXISTING — We *are* the local machine. Just use Git directly. This is actually easier than Overleaf's approach.

### 10.8 GitHub Integration (Premium)
- **What**: Two-way sync between an Overleaf project and a GitHub repository.
- **Why it matters**: Publish your LaTeX source alongside code (e.g., for reproducible research).
- **Local Build Feasibility**: 🟢 FREE EXISTING — Just use `git remote add origin` + `git push`. No intermediary needed.

### 10.9 Dropbox Integration (Premium)
- **What**: Sync project files with a Dropbox folder.
- **Why it matters**: Backup and access from Dropbox ecosystem.
- **Local Build Feasibility**: ✅ EASY — If Dropbox is installed locally, just put the project in the Dropbox folder. Or use `rclone`.

---

## 11. Templates & Gallery

Pre-built document templates.

### 11.1 Template Gallery
- **What**: Thousands of free, searchable templates organized by category: journal articles, theses, presentations (Beamer), CVs/resumes, cover letters, lab reports, homework, posters, books, etc.
- **Why it matters**: Start with a professional layout instead of building from scratch.
- **Local Build Feasibility**: 🟡 MODERATE — Curate a local template library. Download popular templates from CTAN or Overleaf's public gallery (they're openly accessible). Store them as starter projects.

### 11.2 Publisher-Approved Templates
- **What**: Official templates from IEEE, Springer, Elsevier, ACM, Nature, PNAS, and hundreds of other publishers/conferences.
- **Why it matters**: Guarantee compliance with submission formatting requirements.
- **Local Build Feasibility**: ✅ EASY — These `.cls` and `.sty` files are freely available from publisher websites and CTAN. Just bundle them.

### 11.3 One-Click "Open as Template"
- **What**: On any template in the gallery, click "Open as Template" to create a new project pre-populated with that template.
- **Why it matters**: Zero-friction template adoption.
- **Local Build Feasibility**: ✅ EASY — Copy the template directory into a new project directory.

### 11.4 User-Submitted Templates
- **What**: Users can publish their own templates to the gallery for others to use.
- **Why it matters**: Community-driven template ecosystem.
- **Local Build Feasibility**: 🟡 MODERATE — If building a shared platform, needs a submission/review workflow. For local use, just save your own templates to a shared folder.

### 11.5 Beamer Presentation Templates
- **What**: Specific templates for LaTeX presentations using the Beamer document class.
- **Why it matters**: Create academic presentations with LaTeX quality math and formatting.
- **Local Build Feasibility**: ✅ EASY — Beamer is a standard LaTeX package. Templates are freely available.

---

## 12. Bibliography & Citations

Reference management and citation handling.

### 12.1 BibTeX / BibLaTeX Support
- **What**: Full support for `.bib` bibliography files. Compiles with `bibtex` or `biber` backend automatically.
- **Why it matters**: Standard academic citation workflow.
- **Local Build Feasibility**: ✅ EASY — `bibtex` and `biber` come with TeX Live. `latexmk` handles the multi-pass compilation automatically.

### 12.2 Citation Key Autocomplete
- **What**: When typing `\cite{`, a dropdown appears listing all citation keys from the project's `.bib` files.
- **Why it matters**: No need to remember exact citation keys.
- **Local Build Feasibility**: 🟡 MODERATE — Parse `.bib` files for `@article{key, ...}` entries and provide them to the autocomplete system.

### 12.3 Advanced Reference Search (Premium)
- **What**: Search your bibliography by author name, title, or year while typing `\cite{}`. Triggered via `Ctrl+Space`.
- **Why it matters**: Find the right paper even if you forgot the citation key.
- **Local Build Feasibility**: 🟡 MODERATE — Parse `.bib` files into structured objects and implement fuzzy search over author/title/year fields.

### 12.4 Mendeley Integration (Premium)
- **What**: Link your Mendeley library to Overleaf. Auto-sync references.
- **Why it matters**: Use Mendeley as your reference manager and have the `.bib` file always up to date.
- **Local Build Feasibility**: 🟡 MODERATE — Mendeley can export `.bib` files. Set up a sync script or use Mendeley's local `.bib` export directly.

### 12.5 Zotero Integration (Premium)
- **What**: Link your Zotero library to Overleaf. Auto-sync references via a `.bib` file.
- **Why it matters**: Zotero is the most popular free, open-source reference manager.
- **Local Build Feasibility**: 🟢 FREE EXISTING — Zotero with the Better BibTeX plugin can auto-export a `.bib` file to your project directory. No custom code needed.

### 12.6 Multiple Bibliography Styles
- **What**: Support for hundreds of citation styles (APA, IEEE, Chicago, Harvard, MLA, etc.) via `\bibliographystyle{}` or `biblatex` options.
- **Why it matters**: Each journal/discipline has its own citation format.
- **Local Build Feasibility**: ✅ EASY — All `.bst` files come with TeX Live. No extra work needed.

### 12.7 natbib Support
- **What**: Support for the `natbib` package with its `\citet{}`, `\citep{}`, etc. commands.
- **Why it matters**: Fine-grained control over citation formatting (parenthetical vs. textual).
- **Local Build Feasibility**: ✅ EASY — `natbib` is a standard LaTeX package. Already included in TeX Live.

---

## 13. External Integrations

Connections to third-party services.

### 13.1 GitHub Sync (Premium)
- **What**: Two-way sync between Overleaf and a GitHub repository. Changes on either side can be pushed/pulled.
- **Why it matters**: Version control with the world's largest code hosting platform.
- **Local Build Feasibility**: 🟢 FREE EXISTING — We're already local. Just use Git + GitHub directly. Strictly better than Overleaf's integration.

### 13.2 Dropbox Sync (Premium)
- **What**: Sync project files with a Dropbox folder.
- **Why it matters**: Cloud backup and access from any device.
- **Local Build Feasibility**: 🟢 FREE EXISTING — Place the project inside the Dropbox folder. Done.

### 13.3 Direct Journal Submission
- **What**: Submit your manuscript directly to certain journals (e.g., some Springer, Elsevier journals) from within Overleaf.
- **Why it matters**: Skip the manual download-upload-to-journal workflow.
- **Local Build Feasibility**: 🔴 HARD — Requires API integrations with individual publishers. Not feasible to replicate independently. However, you can manually download and upload — this is just a convenience.

### 13.4 Grammarly / Browser Extensions
- **What**: Overleaf works with browser extensions like Grammarly, Paperpal, and others for advanced grammar/style checking.
- **Why it matters**: AI-powered writing improvement on top of the LaTeX editor.
- **Local Build Feasibility**: 🟢 FREE EXISTING — If our tool is web-based, browser extensions work automatically. No effort needed.

### 13.5 SSO / SAML / LDAP (Institutional)
- **What**: Enterprise/institutional plans support Single Sign-On via SAML, LDAP, etc.
- **Why it matters**: University users can log in with their institutional credentials.
- **Local Build Feasibility**: 🟡 MODERATE — For local single-user use, irrelevant. For a shared server, libraries like `passport-saml` exist for Node.js.

### 13.6 Link Sharing for Published Documents
- **What**: Generate a read-only link to share your compiled PDF publicly.
- **Why it matters**: Share drafts without giving editing access.
- **Local Build Feasibility**: ✅ EASY — Serve the PDF at a public URL.

---

## 14. Error Handling & Logs

Understanding and fixing compilation issues.

### 14.1 Compilation Log Panel
- **What**: After compilation, view the full LaTeX log output. Errors, warnings, and info messages are parsed and displayed in a structured panel.
- **Why it matters**: Debug compilation failures without reading raw `.log` files.
- **Local Build Feasibility**: 🟡 MODERATE — Parse the `.log` file output from `pdflatex`. Extract errors (lines starting with `!`), warnings (`LaTeX Warning:`), and overfull/underfull box messages. Display in a structured UI.

### 14.2 Color-Coded Error Severity
- **What**: Errors are shown in red, warnings in orange/yellow, overfull/underfull boxes in blue/gray.
- **Why it matters**: Instantly see severity at a glance.
- **Local Build Feasibility**: ✅ EASY — CSS color coding based on parsed message type.

### 14.3 Clickable Error → Line Navigation
- **What**: Click on an error message and the editor scrolls to and highlights the offending line.
- **Why it matters**: "Error on line 247" → click → you're on line 247.
- **Local Build Feasibility**: 🟡 MODERATE — Parse line numbers from log messages. Wire up click handlers to `editor.scrollToLine()`.

### 14.4 Error Count Badge
- **What**: A badge on the "Logs" button showing the count of errors and warnings (e.g., "3 errors, 2 warnings").
- **Why it matters**: Know at a glance if compilation succeeded or how many issues exist.
- **Local Build Feasibility**: ✅ EASY — Count parsed errors/warnings and display a badge.

### 14.5 Stop on First Error Mode
- **What**: Toggle to stop compilation at the first error (see also 4.4).
- **Why it matters**: Prevents cascading errors that obscure the root cause.
- **Local Build Feasibility**: ✅ EASY — Pass `-halt-on-error` flag.

### 14.6 Raw Log Download
- **What**: Download the full `.log` file for advanced debugging.
- **Why it matters**: Sometimes you need to grep through the full log or share it with someone for help.
- **Local Build Feasibility**: ✅ EASY — Serve the `.log` file from the output directory.

### 14.7 Output Files Access
- **What**: Access intermediate output files (`.aux`, `.toc`, `.bbl`, `.synctex.gz`) from the logs panel.
- **Why it matters**: Advanced debugging of cross-reference or bibliography issues.
- **Local Build Feasibility**: ✅ EASY — List files in the output directory and provide download links.

### 14.8 Compilation Timeout Handling
- **What**: If compilation takes too long (Overleaf's limit is typically 1–4 minutes depending on plan), it's terminated with a timeout error.
- **Why it matters**: Prevents infinite loops from hanging the system.
- **Local Build Feasibility**: ✅ EASY — Use a process timeout (`setTimeout` + `kill`, or `timeout` command). We can set our own generous limits.

---

## 15. Editor Settings & Customization

Per-project and global preferences.

### 15.1 TeX Engine Selection
- **What**: Choose between pdfLaTeX, XeLaTeX, LuaLaTeX per project.
- **Why it matters**: Different documents require different engines (Unicode fonts → XeLaTeX, Lua scripting → LuaLaTeX).
- **Local Build Feasibility**: ✅ EASY — A project settings dropdown that changes the compilation command.

### 15.2 Compiler Version (TeX Live Year)
- **What**: Overleaf lets you select the TeX Live version year (e.g., 2023, 2024) for reproducibility.
- **Why it matters**: Packages change between TeX Live releases. Pinning a version ensures the document always compiles the same way.
- **Local Build Feasibility**: 🟡 MODERATE — Maintain multiple TeX Live installations or use Docker images tagged by year.

### 15.3 Auto-Compile Toggle
- **What**: Enable/disable automatic recompilation on edit.
- **Why it matters**: Turn off for large documents where compilation is slow.
- **Local Build Feasibility**: ✅ EASY — Toggle the file watcher on/off.

### 15.4 Spell Check Language
- **What**: Select the spell check language (English, French, German, Spanish, Portuguese, etc.) — over 30 languages supported.
- **Why it matters**: Multilingual document support.
- **Local Build Feasibility**: 🟡 MODERATE — `hunspell` supports many languages. Need to ship/download dictionaries.

### 15.5 Editor Font Size
- **What**: Slider or preset options for editor font size.
- **Why it matters**: Accessibility.
- **Local Build Feasibility**: ✅ EASY — CSS property change.

### 15.6 Editor Theme
- **What**: Select a color theme for the editor (light, dark, monokai, etc.).
- **Why it matters**: Visual comfort.
- **Local Build Feasibility**: ✅ EASY — CodeMirror theme switching.

### 15.7 Keybinding Mode
- **What**: Choose between Default, Vim, or Emacs keybindings.
- **Why it matters**: Muscle memory for power users.
- **Local Build Feasibility**: ✅ EASY — CodeMirror Vim/Emacs extensions.

### 15.8 PDF Viewer Selection
- **What**: Choose between "Overleaf" (built-in) viewer and "Browser" (native browser PDF viewer).
- **Why it matters**: The built-in viewer supports SyncTeX; the browser viewer may be faster/have different features.
- **Local Build Feasibility**: ✅ EASY — Toggle between `pdf.js` embedded viewer and opening the PDF in a new tab.

### 15.9 Auto-Close Brackets Toggle
- **What**: Enable/disable automatic bracket closing.
- **Why it matters**: Some users find auto-close annoying.
- **Local Build Feasibility**: ✅ EASY — CodeMirror configuration option.

### 15.10 Auto-Complete Toggle
- **What**: Enable/disable the autocomplete dropdown.
- **Why it matters**: Some users prefer to type everything manually.
- **Local Build Feasibility**: ✅ EASY — CodeMirror configuration option.

### 15.11 Overall Theme (Interface)
- **What**: Beyond the editor itself, the entire Overleaf UI (toolbars, sidebars, menus) can be light or dark.
- **Why it matters**: Consistent visual experience.
- **Local Build Feasibility**: ✅ EASY — CSS variable-based theme system for the entire app.

---

## 16. Keyboard Shortcuts

Productivity accelerators.

### 16.1 Compile
- `Ctrl+Enter` or `Ctrl+S` — Trigger compilation.
- **Local Build Feasibility**: ✅ EASY

### 16.2 Find / Replace
- `Ctrl+F` — Find in file
- `Ctrl+H` — Find and Replace
- `Ctrl+Shift+F` — Find in all files
- **Local Build Feasibility**: ✅ EASY

### 16.3 Go to Line
- `Ctrl+Shift+L` — Jump to line number
- **Local Build Feasibility**: ✅ EASY

### 16.4 Comment Toggle
- `Ctrl+/` — Toggle comment on selected lines
- **Local Build Feasibility**: ✅ EASY

### 16.5 Select All
- `Ctrl+A` — Select all text
- **Local Build Feasibility**: ✅ EASY

### 16.6 Indent / Outdent
- `Tab` / `Shift+Tab` — Indent or dedent selection
- **Local Build Feasibility**: ✅ EASY

### 16.7 Delete Line
- `Ctrl+D` — Delete current line
- **Local Build Feasibility**: ✅ EASY

### 16.8 Uppercase / Lowercase
- `Ctrl+U` — Uppercase selection
- `Ctrl+Shift+U` — Lowercase selection
- **Local Build Feasibility**: ✅ EASY

### 16.9 Autocomplete Trigger
- `Ctrl+Space` — Open autocomplete/citation search
- **Local Build Feasibility**: ✅ EASY

### 16.10 Bold / Italic (Visual Editor)
- `Ctrl+B` — Bold (`\textbf{}`)
- `Ctrl+I` — Italic (`\textit{}`)
- **Local Build Feasibility**: ✅ EASY — Wrap selection in the appropriate LaTeX command.

### 16.11 Navigate Start / End of Document
- `Ctrl+Home` — Go to first line
- `Ctrl+End` — Go to last line
- **Local Build Feasibility**: ✅ EASY

### 16.12 Custom Shortcut Mapping
- **What**: Overleaf doesn't support custom shortcut remapping (beyond Vim/Emacs modes).
- **Local Build Feasibility**: 🟡 MODERATE — We can build this as an improvement over Overleaf. CodeMirror supports custom keymaps.

---

## 17. Learning Resources & Documentation

Help and educational content.

### 17.1 "Learn LaTeX" Tutorial Library
- **What**: Hundreds of free articles and tutorials covering LaTeX basics, math typesetting, tables, TikZ diagrams, Beamer presentations, custom classes, etc.
- **Why it matters**: Integrated learning without leaving the platform.
- **Local Build Feasibility**: 🟡 MODERATE — Curate links to existing free resources (LaTeX Wikibook, Overleaf's public tutorials, CTAN documentation). Or embed a documentation browser.

### 17.2 In-Editor Help Tooltips
- **What**: Hover over certain error messages or features to see brief help text.
- **Why it matters**: Contextual learning.
- **Local Build Feasibility**: 🟡 MODERATE — Build a tooltip system that maps error codes/commands to help text.

### 17.3 Quick-Start Guide
- **What**: An onboarding experience for new users showing the basics of the editor.
- **Why it matters**: Reduce time-to-first-compile for beginners.
- **Local Build Feasibility**: ✅ EASY — A simple tutorial page or interactive walkthrough.

### 17.4 Video Tutorials
- **What**: Overleaf hosts video tutorials on YouTube and their site.
- **Why it matters**: Visual learners.
- **Local Build Feasibility**: ✅ EASY — Link to existing free YouTube tutorials. No need to create our own.

### 17.5 LaTeX Math Symbol Reference
- **What**: A searchable reference of common LaTeX math symbols and commands.
- **Why it matters**: Nobody memorizes all 1000+ math symbols.
- **Local Build Feasibility**: 🟡 MODERATE — Embed an existing reference (e.g., `detexify` for hand-drawn symbol recognition) or build a searchable symbol table.

---

## 18. Account & Access Management

User account features (relevant for multi-user / online deployment).

### 18.1 User Registration / Login
- **What**: Create an account with email/password or OAuth (Google, ORCID, Twitter, institutional SSO).
- **Why it matters**: Personalized workspace.
- **Local Build Feasibility**: ✅ EASY (single user) / 🟡 MODERATE (multi-user) — For local single-user, no auth needed. For a shared server, use `passport.js` or similar.

### 18.2 Account Settings
- **What**: Change email, password, name, default settings (spell check language, editor theme, etc.).
- **Why it matters**: Personalization.
- **Local Build Feasibility**: ✅ EASY — A settings page that reads/writes a config file or database record.

### 18.3 ORCID Integration
- **What**: Link your ORCID iD for academic identity.
- **Why it matters**: Professional academic identity.
- **Local Build Feasibility**: ✅ EASY — Just store the ORCID string in settings. No deep integration needed for local use.

### 18.4 Institutional Dashboard (Admin)
- **What**: For university subscriptions, an admin panel showing usage metrics, user management, and compliance.
- **Why it matters**: IT administrators need oversight.
- **Local Build Feasibility**: 🟡 MODERATE — Only needed for multi-user deployment. Standard admin panel.

### 18.5 API Access (for bots / automation)
- **What**: Overleaf doesn't have an official public API, but the Git integration and some undocumented endpoints allow programmatic access.
- **Why it matters**: Automate workflows (e.g., CI/CD for LaTeX documents).
- **Local Build Feasibility**: ✅ EASY — If we build a web app, we define our own REST API. We can make it better than Overleaf's.

---

## 19. Security & Infrastructure

Backend and platform concerns.

### 19.1 Sandboxed Compilation
- **What**: Each compilation runs in an isolated sandbox (container/VM) so malicious LaTeX code (e.g., `\write18` shell escape) can't compromise the server.
- **Why it matters**: Overleaf is multi-tenant — one user's compilation shouldn't affect another's.
- **Local Build Feasibility**: 🟡 MODERATE — For local single-user, not critical. For a shared server, use Docker containers per compilation. The Community Edition does NOT include sandboxing.

### 19.2 HTTPS / TLS Encryption
- **What**: All traffic is encrypted in transit.
- **Why it matters**: Protect intellectual property (unpublished research).
- **Local Build Feasibility**: ✅ EASY — Use `nginx` with Let's Encrypt SSL certificates. For local-only, not needed.

### 19.3 Data Encryption at Rest
- **What**: Project data is encrypted on Overleaf's servers.
- **Why it matters**: Compliance with institutional data policies.
- **Local Build Feasibility**: ✅ EASY — Use full-disk encryption (BitLocker, LUKS) on the server. Or it's your own machine — you control it.

### 19.4 GDPR Compliance
- **What**: Overleaf complies with EU data protection regulations.
- **Why it matters**: Required for European institutional users.
- **Local Build Feasibility**: ✅ EASY — If data stays on your machine, GDPR concerns are minimal. For a shared server, implement data deletion and export features.

### 19.5 Automatic Backups
- **What**: Overleaf maintains server-side backups of all project data.
- **Why it matters**: Disaster recovery.
- **Local Build Feasibility**: ✅ EASY — Set up a `cron` job or scheduled task to backup the projects directory. Use `rsync`, `rclone`, or Git.

### 19.6 Rate Limiting & Fair Use
- **What**: Compilation rate limits to prevent abuse on shared infrastructure.
- **Why it matters**: Keep the platform responsive for all users.
- **Local Build Feasibility**: ✅ EASY — It's our machine. No rate limits needed. Or set them if hosting for multiple users.

---

## 20. Miscellaneous / Hidden Gems

Small but valuable features that make Overleaf special.

### 20.1 URL-Based Project Access
- **What**: Each project has a unique URL. Bookmark it and return directly to the editor.
- **Why it matters**: No need to navigate through dashboards.
- **Local Build Feasibility**: ✅ EASY — Standard web app routing (`/project/:id`).

### 20.2 Auto-Save
- **What**: Changes are saved automatically to the server. No "Save" button needed.
- **Why it matters**: Never lose work due to forgetting to save.
- **Local Build Feasibility**: ✅ EASY — Write to disk on every keystroke (debounced) or on blur/interval.

### 20.3 Offline Resilience
- **What**: If your internet drops briefly, Overleaf buffers changes and syncs when reconnected.
- **Why it matters**: Don't lose edits during network hiccups.
- **Local Build Feasibility**: 🟢 FREE EXISTING — If local, there's no network dependency at all. For online mode, implement a queue with retry logic.

### 20.4 Mobile-Friendly (Responsive)
- **What**: Overleaf's interface works on tablets and phones (though not ideal).
- **Why it matters**: Emergency edits on the go.
- **Local Build Feasibility**: 🟡 MODERATE — Responsive CSS design. The editor may need special handling for touch input.

### 20.5 PDF Text Selection & Copy
- **What**: Select and copy text from the PDF preview.
- **Why it matters**: Copy a rendered equation, reference number, or paragraph.
- **Local Build Feasibility**: ✅ EASY — `pdf.js` supports text selection natively.

### 20.6 Page Navigation in PDF
- **What**: Scroll through pages, jump to a specific page number, or use a page thumbnail sidebar.
- **Why it matters**: Navigate long documents in the preview.
- **Local Build Feasibility**: ✅ EASY — `pdf.js` provides page navigation controls.

### 20.7 Compilation Time Display
- **What**: After compilation, Overleaf shows how long it took (e.g., "Compiled in 4.2s").
- **Why it matters**: Monitor performance and identify slow compilations.
- **Local Build Feasibility**: ✅ EASY — Time the compilation process and display the duration.

### 20.8 Cursor Position Indicator
- **What**: Status bar showing current line number and column number of the cursor.
- **Why it matters**: Know exactly where you are in the document.
- **Local Build Feasibility**: ✅ EASY — CodeMirror provides cursor position events.

### 20.9 Character / Word Count in Editor
- **What**: Some status bar indicators for current selection or document stats.
- **Why it matters**: Quick reference while writing.
- **Local Build Feasibility**: ✅ EASY — Count characters/words in the editor buffer.

### 20.10 Image Preview on Hover
- **What**: In the file tree, hovering over an image file shows a thumbnail preview.
- **Why it matters**: Quickly identify images without opening them.
- **Local Build Feasibility**: ✅ EASY — Generate thumbnails and show on hover via CSS/JS tooltip.

### 20.11 Multilingual UI
- **What**: The Overleaf interface is available in multiple languages (English, Chinese, Spanish, etc.).
- **Why it matters**: Accessibility for non-English speakers.
- **Local Build Feasibility**: 🟡 MODERATE — Use an i18n library (e.g., `i18next`). Requires translating all UI strings.

### 20.12 Print PDF
- **What**: Print the compiled PDF directly from the browser.
- **Why it matters**: Physical copies for review meetings.
- **Local Build Feasibility**: ✅ EASY — Standard browser print functionality.

---

## Grand Summary — Feasibility Scorecard

### Feature Count by Feasibility

| Rating | Count | Percentage |
|--------|-------|------------|
| ✅ EASY | ~85 | ~65% |
| 🟢 FREE EXISTING | ~8 | ~6% |
| 🟡 MODERATE | ~28 | ~22% |
| 🔴 HARD | ~9 | ~7% |

### The 🔴 HARD Features (the ones that are genuinely difficult):

1. **Visual Editor (toggle code/WYSIWYG)** — Requires a full LaTeX↔DOM bidirectional renderer
2. **GUI Table Editor** — Complex LaTeX tabular code generation & sync
3. **Rich Text Formatting Toolbar** — Deep LaTeX markup mapping
4. **Copy-Paste from Word → LaTeX** — Robust HTML/RTF parser
5. **Real-Time Collaborative Editing** — OT/CRDT implementation
6. **User Cursors / Presence** — Requires real-time sync infrastructure
7. **Track Changes** — Character-level diff tracking with accept/reject
8. **Direct Journal Submission** — Publisher API integrations (not worth building)

### Recommended Build Priority for a Local "Overleaf Clone"

**Phase 1 — MVP (1–2 weeks)**:
Core platform, code editor (CodeMirror 6), file tree, PDF viewer (pdf.js), manual compile, basic project management.

**Phase 2 — Polished Editor (2–4 weeks)**:
Autocomplete, code folding, spell check, search (in-file + project-wide), SyncTeX, document outline, error log parsing, themes.

**Phase 3 — Power Features (4–8 weeks)**:
Template library, bibliography autocomplete, auto-compile with debounce, version history (Git-backed), resizable panels, drag-and-drop images.

**Phase 4 — Collaboration (8+ weeks, optional)**:
Real-time editing (Yjs + WebSocket), comments, track changes, user management.

### Our Key Advantages Over Overleaf:

1. **No compile time limits** — Compile a 500-page thesis with 200 TikZ diagrams. Take as long as you need.
2. **No file limits** — No 2,000 file cap or 50 MB upload limit.
3. **Full TeX Live** — Every CTAN package available. No "missing package" errors ever.
4. **Custom TeX engines** — Use ConTeXt, Plain TeX, or any engine you want.
5. **Git integration is native** — No premium paywall. Just use Git.
6. **Privacy** — Your documents never leave your machine.
7. **Free forever** — No subscription tiers. No premium paywalls.
8. **Custom API** — Build automation workflows that Overleaf doesn't support.
9. **Shell escape** — Enable `\write18` for complex builds (Minted, external tools).
10. **Offline-first** — Works without internet.

---

> **Total features cataloged: ~130+**
>
> **Verdict**: We can build a local Overleaf that covers **~93% of features** (everything except real-time collaboration and the visual editor). For a single user or small team, this is strictly superior to Overleaf in many ways (no limits, free, private, offline).
