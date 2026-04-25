# Phase 1 Blueprint — Foundation & Core Editor

> **Phase**: 1 of 7
> **Goal**: Build the absolute minimum viable Pdleaf — a working LaTeX editor where you can open a `.tex` file, edit it in a code editor, compile it, and see the resulting PDF side-by-side.
> **Estimated Effort**: 1–2 weeks
> **Prerequisite**: TeX Live (or MiKTeX) installed on the machine. Node.js 18+ installed.

---

## What Phase 1 Delivers

When Phase 1 is complete, a user should be able to:
1. Open `http://localhost:3000` in their browser
2. See a code editor on the left and a PDF preview on the right
3. The editor loads a sample `main.tex` file with LaTeX syntax highlighting
4. Edit the LaTeX code
5. Click "Compile" to generate the PDF
6. See the compiled PDF render in the right panel
7. Drag the divider to resize editor vs. preview

**What Phase 1 does NOT include**: No autocomplete, no folding, no file tree, no project management, no auto-compile, no error parsing, no SyncTeX, no settings panel. Those come in later phases.

---

## Feature 1.1 — Project Scaffolding & Web App Shell

### What We're Building
The foundational project structure: folder layout, entry files, dev server, and the basic three-panel layout skeleton (placeholder sidebar, editor pane, preview pane).

### Sub-Steps
1. **Initialize the project**
   - `npm init -y` in the `Pdleaf/` directory
   - Create `.gitignore` (ignore `node_modules/`, `dist/`, `.env`, `*.aux`, `*.log`, etc.)
   - Install core dependencies: `express` (backend), `vite` (dev server/bundler)

2. **Create directory structure**
   ```
   Pdleaf/
   ├── src/
   │   ├── index.html          # Main HTML entry
   │   ├── css/
   │   │   └── style.css        # Global styles
   │   ├── js/
   │   │   ├── app.js           # Frontend entry point
   │   │   ├── editor.js        # CodeMirror setup (Feature 1.2)
   │   │   ├── compiler.js      # Compile button logic (Feature 1.4)
   │   │   └── pdfViewer.js     # PDF.js setup (Feature 1.5)
   │   └── assets/              # Icons, fonts, etc.
   ├── server/
   │   ├── index.js             # Express server entry
   │   ├── routes/
   │   │   └── compile.js       # Compilation API route
   │   └── utils/
   │       └── latex.js          # LaTeX compilation helper
   ├── projects/                # Where user projects live
   │   └── sample/
   │       └── main.tex          # Sample starter document
   ├── package.json
   ├── vite.config.js           # Vite configuration
   └── .gitignore
   ```

3. **Create the HTML shell** (`index.html`)
   - Three-panel layout: sidebar (empty placeholder for now), editor pane, preview pane
   - A top toolbar with: project name, "Compile" button, status indicator
   - A bottom status bar (empty for now — will show cursor position later)

4. **Create the base CSS** (`style.css`)
   - CSS reset / normalize
   - CSS custom properties (variables) for colors, spacing, fonts
   - Dark theme by default (professional, modern look)
   - Flexbox layout for the three panels
   - The sidebar should be 0px wide for now (will be enabled in Phase 4)

5. **Set up the dev server**
   - Vite for frontend hot-reload during development
   - Express server for backend API (runs on port 3001)
   - Vite proxies API calls from frontend to Express
   - `npm run dev` starts both simultaneously (use `concurrently`)

### Do's
- ✅ Use CSS custom properties for ALL colors and spacing — makes theming easy later
- ✅ Use semantic HTML (`<main>`, `<aside>`, `<header>`, `<footer>`)
- ✅ Make the layout use `display: flex` or CSS Grid — no absolute positioning hacks
- ✅ Set up `package.json` scripts: `dev`, `build`, `start`
- ✅ Include a sample `main.tex` with a basic document (`\documentclass{article}`, `\begin{document}`, Hello World, `\end{document}`)

### Don'ts
- ❌ Don't use a CSS framework (Tailwind, Bootstrap) — we want full control
- ❌ Don't use React/Vue/Angular — keep it vanilla JS for simplicity and speed
- ❌ Don't over-engineer the layout — Phase 1 sidebar is just a placeholder div
- ❌ Don't set up authentication or user management — single user, no auth
- ❌ Don't worry about responsive design yet — desktop-first

### Definition of Done
- [ ] Running `npm run dev` starts the app and opens in browser
- [ ] The browser shows a dark-themed page with a toolbar at the top
- [ ] Two panels are visible: a left panel (editor area) and right panel (preview area)
- [ ] The toolbar shows the project name and a "Compile" button (button doesn't work yet)
- [ ] The sample `main.tex` file exists in `projects/sample/`

### How to Test
1. `npm run dev` → browser opens to `http://localhost:3000`
2. Visually confirm: dark background, two panels, toolbar visible
3. Resize the browser window → panels should maintain their proportions
4. Check the console — no JavaScript errors

---

## Feature 1.2 — CodeMirror 6 Integration (Basic)

### What We're Building
Embed the CodeMirror 6 code editor in the left panel with LaTeX syntax highlighting and basic editing features (line numbers, selection, copy/paste, undo/redo).

### Sub-Steps
1. **Install CodeMirror 6 packages**
   ```bash
   npm install @codemirror/state @codemirror/view @codemirror/language
   npm install @codemirror/commands @codemirror/search
   npm install @codemirror/lang-latex   # or codemirror-lang-latex
   npm install @codemirror/theme-one-dark  # dark theme
   ```

2. **Create the editor module** (`editor.js`)
   - Initialize an `EditorView` attached to the editor panel DOM element
   - Configure extensions:
     - `basicSetup` (line numbers, bracket matching, cursor, active line highlight, undo/redo history)
     - `latex()` language mode for syntax highlighting
     - `oneDark` theme (or a custom dark theme)
     - `EditorView.lineWrapping` (soft wrap on by default)
   - Load the content of `main.tex` into the editor state

3. **Load file content from backend**
   - Backend endpoint: `GET /api/file?path=projects/sample/main.tex`
   - Returns the file content as plain text
   - Frontend fetches this on page load and sets it as the editor's initial document

4. **Save file content to backend**
   - Backend endpoint: `POST /api/file` with `{ path, content }` body
   - Writes the content to disk
   - Frontend calls this before compilation (to ensure the on-disk file matches the editor)

### Do's
- ✅ Use `basicSetup` from `@codemirror/basic-setup` — it bundles line numbers, bracket matching, history, etc.
- ✅ Use a proper LaTeX language mode — don't just use plain text
- ✅ Set the editor to fill 100% of its parent container (both width and height)
- ✅ Make the editor export a function to `getContent()` — other modules will need it
- ✅ Use the `oneDark` theme to match the overall dark UI

### Don'ts
- ❌ Don't add autocomplete in this feature — that's Phase 2
- ❌ Don't add code folding — that's Phase 2
- ❌ Don't add spell checking — that's Phase 5
- ❌ Don't try to parse or validate LaTeX — just syntax highlight it
- ❌ Don't add file tabs — Phase 1 opens only one file

### Definition of Done
- [ ] The editor fills the entire left panel
- [ ] LaTeX syntax is highlighted (commands in one color, comments in another, math delimiters highlighted)
- [ ] Line numbers are visible in the gutter
- [ ] Typing, selecting, copy/paste, undo/redo all work
- [ ] The sample `main.tex` content loads automatically from the backend
- [ ] `editor.getContent()` returns the current text content as a string

### How to Test
1. Open the app → editor should show the `main.tex` content with syntax highlighting
2. Type `\textbf{test}` → `\textbf` should be highlighted differently from `test`
3. Type `% this is a comment` → entire line should be in a muted comment color
4. Select text, Ctrl+C, Ctrl+V → clipboard works
5. Ctrl+Z → undo works
6. Check that line numbers appear and scroll with the content

---

## Feature 1.3 — TeX Live Compilation Backend

### What We're Building
A backend API endpoint that compiles the current `.tex` file using the locally installed TeX Live distribution and returns the result (success + PDF path, or failure + error output).

### Sub-Steps
1. **Verify TeX Live installation**
   - On startup, the server should check that `pdflatex` and `latexmk` are available on `PATH`
   - If not found, log a clear error message: "TeX Live not found. Please install..."
   - Also check for `bibtex` and `biber` (needed later, but nice to verify upfront)

2. **Create the compilation helper** (`server/utils/latex.js`)
   - Function `compileLaTeX(projectDir, mainFile, engine = 'pdflatex')`:
     - Runs: `latexmk -pdf -interaction=nonstopmode -synctex=1 -outdir=./output <mainFile>`
     - Uses `child_process.execFile` (NOT `exec` — safer, no shell injection)
     - Captures `stdout` and `stderr`
     - Returns: `{ success: boolean, pdfPath: string | null, log: string, duration: number }`
   - Set a compilation timeout (e.g., 60 seconds) to prevent infinite hangs
   - The output directory should be `<projectDir>/output/` to keep generated files separate from source

3. **Create the compilation route** (`server/routes/compile.js`)
   - `POST /api/compile`
   - Request body: `{ projectPath: "projects/sample", mainFile: "main.tex" }`
   - Calls the `compileLaTeX` helper
   - Returns JSON: `{ success, pdfUrl, errors, warnings, duration }`
   - On success, the `pdfUrl` should point to the served output PDF

4. **Serve the output PDF**
   - Express static middleware to serve files from `projects/*/output/`
   - URL pattern: `/output/<project>/main.pdf`
   - Set `Cache-Control: no-cache` so the browser always fetches the latest PDF

### Do's
- ✅ Use `execFile` not `exec` — prevents shell injection attacks
- ✅ Use `latexmk` instead of raw `pdflatex` — it handles multi-pass compilation
- ✅ Always pass `-synctex=1` — we'll need the SyncTeX file later (Phase 3)
- ✅ Always pass `-interaction=nonstopmode` — prevents LaTeX from hanging on user input prompts
- ✅ Separate output files from source files (use `-outdir=./output`)
- ✅ Set a compilation timeout (60s default, configurable)

### Don'ts
- ❌ Don't parse the `.log` file in this feature — just return the raw log text. Parsing comes in Phase 3
- ❌ Don't support engine selection (XeLaTeX, LuaLaTeX) yet — hardcode `pdflatex` for now
- ❌ Don't run compilation in a Docker container — that's over-engineering for Phase 1
- ❌ Don't allow arbitrary paths — validate that `projectPath` is within the `projects/` directory (security)

### Definition of Done
- [ ] `POST /api/compile` with a valid project path returns `{ success: true, pdfUrl: "/output/sample/main.pdf" }`
- [ ] The output PDF file exists at the expected path
- [ ] If the `.tex` has errors, `success` is `false` and `log` contains the error text
- [ ] A timeout of 60 seconds kills hung compilations
- [ ] Accessing `/output/sample/main.pdf` in the browser shows the compiled PDF

### How to Test
1. Start the server → `curl -X POST http://localhost:3001/api/compile -H "Content-Type: application/json" -d '{"projectPath":"projects/sample","mainFile":"main.tex"}'`
2. Verify response has `success: true` and a `pdfUrl`
3. Open `http://localhost:3001/output/sample/main.pdf` in browser → PDF should render
4. Edit `main.tex` to have an error (e.g., remove `\end{document}`) → recompile → should get `success: false` with log
5. Edit `main.tex` to have `\loop\iftrue\repeat` (infinite loop) → should timeout after 60 seconds

---

## Feature 1.4 — Manual Compile Button

### What We're Building
Wire the "Compile" button in the toolbar to: (1) save the current editor content to disk, (2) trigger the compilation backend, and (3) report success/failure to the user.

### Sub-Steps
1. **Save before compile**
   - When the user clicks "Compile", first call `POST /api/file` to save the editor content to disk
   - Wait for the save to complete before triggering compilation

2. **Trigger compilation**
   - Call `POST /api/compile` with the current project path and main file
   - Show a "Compiling..." state on the button (disable the button, show a spinner)

3. **Handle the response**
   - **Success**: Update the PDF viewer to show the new PDF (Feature 1.5 will handle the rendering). Change the compile button back to normal. Show a brief "Compiled in X.Xs" toast/message.
   - **Failure**: Change the compile button to show an error state (red icon). Show a brief error message. For now, just show "Compilation failed" — detailed error logs come in Phase 3.

4. **Keyboard shortcut**
   - `Ctrl+S` and `Ctrl+Enter` both trigger the compile workflow (save + compile)
   - Register these as global keyboard shortcuts

### Do's
- ✅ Disable the compile button while compilation is in progress (prevent double-clicks)
- ✅ Show a visual loading indicator (spinner, pulsing icon, or button text change)
- ✅ Show the compilation duration on success ("Compiled in 3.2s")
- ✅ Use `async/await` for the save → compile → render pipeline
- ✅ Emit a custom event (`document.dispatchEvent(new Event('compile-success'))`) that the PDF viewer can listen to

### Don'ts
- ❌ Don't auto-compile on every keystroke — that's Phase 3
- ❌ Don't parse error logs — just show "failed" or "success" for now
- ❌ Don't show a modal dialog on error — a small toast/status message is enough

### Definition of Done
- [ ] Clicking "Compile" saves the file and triggers compilation
- [ ] The button shows a loading state during compilation
- [ ] On success, the button returns to normal and shows "Compiled in X.Xs"
- [ ] On failure, the button shows an error indicator and a brief error message
- [ ] `Ctrl+S` triggers compile
- [ ] `Ctrl+Enter` triggers compile
- [ ] Rapid double-clicks don't trigger two compilations

### How to Test
1. Edit the `main.tex` → add `\textbf{Hello Pdleaf!}` → click "Compile"
2. Button should show spinner → then "Compiled in X.Xs"
3. Press `Ctrl+S` → same behavior
4. Press `Ctrl+Enter` → same behavior
5. Remove `\end{document}` → compile → should show error state
6. Click compile rapidly 5 times → only one compilation should run

---

## Feature 1.5 — PDF Viewer (pdf.js)

### What We're Building
Embed Mozilla's pdf.js library in the right panel to render the compiled PDF. Basic scrollable rendering — no zoom controls, no SyncTeX, no text selection yet.

### Sub-Steps
1. **Install pdf.js**
   ```bash
   npm install pdfjs-dist
   ```
   - Also need to copy the `pdf.worker.js` file to a location Vite can serve (or use a CDN URL)

2. **Create the PDF viewer module** (`pdfViewer.js`)
   - Function `loadPDF(url)`:
     - Uses `pdfjsLib.getDocument(url)` to load the PDF
     - Renders each page into a `<canvas>` element inside the preview pane
     - Stack canvases vertically for a scrollable multi-page view
   - Function `clearPDF()`:
     - Removes all existing canvases (called before loading a new PDF)
   - Handle loading states:
     - Show "No PDF yet — click Compile" initially
     - Show "Loading..." while rendering pages

3. **Listen for compile events**
   - Listen for the `compile-success` event dispatched by the compile button (Feature 1.4)
   - When fired, call `loadPDF(pdfUrl)` with the URL from the compile response

4. **Handle PDF rendering performance**
   - Render pages lazily — only render visible pages + 1 page above/below
   - Use `IntersectionObserver` to detect which pages are in the viewport
   - Initial version can render all pages (optimize later if performance is an issue)

### Do's
- ✅ Set the `workerSrc` correctly — pdf.js needs its Web Worker
- ✅ Scale pages to fit the panel width (use `viewport.width` relative to container)
- ✅ Add `?t=<timestamp>` to the PDF URL to bust the browser cache on recompile
- ✅ Show a "No PDF yet" placeholder before the first compile
- ✅ Clear old pages before rendering new ones

### Don'ts
- ❌ Don't add zoom controls — that's Phase 3
- ❌ Don't add SyncTeX click-to-jump — that's Phase 3
- ❌ Don't add text selection layers — that's Phase 7
- ❌ Don't use an `<iframe>` to display the PDF — use pdf.js canvases for full control
- ❌ Don't try to render 100-page PDFs all at once — if there are many pages, consider lazy rendering

### Definition of Done
- [ ] After a successful compile, the PDF renders in the right panel
- [ ] All pages of the PDF are visible by scrolling
- [ ] Pages are scaled to fit the width of the preview panel
- [ ] Recompiling replaces the old PDF with the new one (no stale cache)
- [ ] Before the first compile, the panel shows "No PDF yet — click Compile"

### How to Test
1. Click "Compile" → PDF should appear in the right panel
2. Scroll the preview pane → all pages should be visible
3. Resize the browser → pages should maintain aspect ratio
4. Edit the LaTeX (add more text to make it 2 pages) → recompile → new PDF should show 2 pages
5. Check that the old PDF is gone and the new one is shown

---

## Feature 1.6 — Split-Panel Layout (Editor + Preview)

### What We're Building
Make the editor and preview panels resizable by dragging a vertical divider bar between them. The user should be able to allocate more space to either the editor or the preview.

### Sub-Steps
1. **Install or build a splitter**
   - Option A: Use `split.js` library (`npm install split.js`)
   - Option B: Build a custom CSS flexbox layout with a draggable divider (preferred for full control)

2. **Implement the draggable divider**
   - A 4-6px wide vertical bar between the editor and preview panels
   - Cursor changes to `col-resize` on hover
   - On `mousedown` → listen for `mousemove` → adjust panel widths via CSS `flex-basis`
   - On `mouseup` → stop listening

3. **Constraints**
   - Minimum editor width: 200px (prevent the editor from being crushed to 0)
   - Minimum preview width: 200px (prevent the preview from disappearing)
   - Default split: 50/50

4. **Re-render PDF on resize**
   - After the divider is dragged, trigger a re-render of the PDF pages to fit the new panel width
   - Use a debounced `ResizeObserver` on the preview pane to detect size changes

5. **Layout persistence (optional for Phase 1)**
   - Save the split position to `localStorage` so it persists across page reloads
   - If not saved, default to 50/50

### Do's
- ✅ Make the divider visually distinct (slightly different color, or a subtle grip pattern)
- ✅ Use `pointer-events: none` on iframes/canvases during drag (prevents them from capturing the mouse)
- ✅ Add `user-select: none` during drag to prevent text selection
- ✅ Debounce the PDF re-render on resize (don't re-render on every pixel of drag)

### Don'ts
- ❌ Don't add "Editor Only" / "Preview Only" toggle buttons — that's Phase 3 or later
- ❌ Don't add a sidebar (file tree) to the layout — that's Phase 4
- ❌ Don't use absolute positioning — use flexbox

### Definition of Done
- [ ] A visible divider bar separates the editor and preview panels
- [ ] Dragging the divider resizes both panels
- [ ] Panels respect minimum width constraints (can't be crushed to 0)
- [ ] After resizing, the PDF pages re-scale to fit the new preview width
- [ ] The cursor changes to `col-resize` when hovering over the divider

### How to Test
1. Hover over the divider → cursor should change to `col-resize`
2. Drag left → editor shrinks, preview grows
3. Drag right → editor grows, preview shrinks
4. Drag all the way left → should stop at minimum editor width (200px)
5. After dragging, the PDF should re-render to fit the new width
6. Reload the page → split should reset to 50/50 (or persist if implemented)

---

## Phase 1 Integration Test Plan

> After all 6 features are implemented, run this end-to-end test to verify Phase 1 is complete.

### The Happy Path (Full Workflow)
1. Start the app with `npm run dev`
2. Browser opens to `http://localhost:3000`
3. See a dark-themed page with a toolbar (project name + "Compile" button)
4. Editor fills the left panel with the sample `main.tex` — syntax highlighted
5. Right panel shows "No PDF yet — click Compile"
6. Click "Compile" → button shows spinner → "Compiled in X.Xs"
7. PDF appears in the right panel, showing "Hello World" or the sample content
8. Drag the divider → panels resize. PDF re-scales.
9. Edit the LaTeX: change "Hello World" to "Hello Pdleaf!"
10. Press `Ctrl+S` → compiles → PDF updates with "Hello Pdleaf!"
11. Add more content to create a 2-page document → compile → scroll through both pages

### The Error Path
1. Remove `\end{document}` from the LaTeX
2. Click "Compile" → button shows error state → "Compilation failed"
3. Add `\end{document}` back → compile → should succeed again

### Edge Cases
1. Empty editor → compile → should fail gracefully (no crash)
2. Very large document (100+ pages) → compile → should complete (maybe slow, but no crash)
3. Click compile while already compiling → should be debounced (only one compilation at a time)
4. Close the browser tab → reopen → app should load normally (no persistent state corruption)

---

> **Phase 1 is complete when all of the above tests pass without errors.**
>
> Next: Proceed to Phase 2 (Editor Enhancements) as defined in the roadmap.
