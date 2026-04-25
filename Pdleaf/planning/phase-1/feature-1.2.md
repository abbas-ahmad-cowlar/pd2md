# Feature 1.2 — CodeMirror 6 Integration (Basic)

> **Phase**: 1 | **Feature**: 2 of 6
> **Goal**: Embed CodeMirror 6 in the editor panel with LaTeX syntax highlighting, line numbers, and basic editing. When this is done, the user should see the contents of `main.tex` in a professional code editor with colored LaTeX syntax.
> **Estimated Effort**: 3–5 hours
> **Dependencies**: Feature 1.1 (Project Scaffolding) must be complete.
> **Predecessor Output**: The `#editor-container` div exists in the HTML. The Express backend is running. Vite is configured.

---

## Overview

This feature transforms the empty left panel into a real code editor. We are:
1. Installing all required CodeMirror 6 packages
2. Creating a backend endpoint to read file contents
3. Creating a backend endpoint to write/save file contents
4. Initializing the CodeMirror editor with LaTeX syntax highlighting
5. Loading the sample `main.tex` from the backend into the editor
6. Exposing a `getContent()` API so other modules (compile button, auto-save) can read the editor text

**What this feature does NOT include**: autocomplete, code folding, spell check, multiple file tabs, vim/emacs modes. Those are Phase 2+.

---

## Step 1: Install CodeMirror 6 Packages

### What to Do
Install all the CodeMirror 6 npm packages needed for a basic LaTeX editor.

### Sub-Steps

#### 1.2.1 — Install core packages
```bash
npm install @codemirror/state @codemirror/view
npm install @codemirror/language @codemirror/commands
npm install @codemirror/search @codemirror/lint
npm install codemirror  # meta-package that bundles basicSetup
```

#### 1.2.2 — Install LaTeX language support
```bash
npm install @codemirror/legacy-modes
# OR if a dedicated LaTeX mode exists:
npm install codemirror-lang-latex
```

> **Important Research Step**: Before installing, check npm for the latest LaTeX language mode for CodeMirror 6. Options:
> - `codemirror-lang-latex` — community package (check if maintained)
> - `@codemirror/legacy-modes` — wraps CodeMirror 5 modes (has `stex` mode for LaTeX)
> - Custom StreamLanguage wrapper — if no good package exists, wrap the CM5 `stex` mode
>
> **Fallback plan**: If no CM6-native LaTeX mode exists, use:
> ```javascript
> import { StreamLanguage } from '@codemirror/language';
> import { stex } from '@codemirror/legacy-modes/mode/stex';
> const latexLanguage = StreamLanguage.define(stex);
> ```

#### 1.2.3 — Install the dark theme
```bash
npm install @codemirror/theme-one-dark
```

### Definition of Done
- [ ] All packages are installed without errors
- [ ] `package.json` lists all CodeMirror dependencies
- [ ] No peer dependency warnings
- [ ] Can import `EditorView` from `@codemirror/view` in a JS file without errors

### How to Test
```javascript
// Quick test in a scratch file or browser console:
import { EditorView } from '@codemirror/view';
console.log(typeof EditorView); // should log 'function'
```

---

## Step 2: Create Backend File API Endpoints

### What to Do
Create two backend API endpoints: one to read a file's contents, and one to write/save file contents. These are needed so the editor can load and save `.tex` files.

### Sub-Steps

#### 1.2.4 — Create the file routes module (`server/routes/files.js`)

```javascript
// server/routes/files.js
import express from 'express';
import fs from 'fs/promises';
import path from 'path';

const router = express.Router();

// Base directory for all projects
const PROJECTS_DIR = path.resolve(process.cwd(), 'projects');

/**
 * GET /api/file?path=relative/path/to/file.tex
 * Returns the file content as plain text.
 */
router.get('/file', async (req, res) => {
  try {
    const filePath = req.query.path;
    if (!filePath) {
      return res.status(400).json({ error: 'Missing "path" query parameter' });
    }

    // Security: resolve and verify the path is within PROJECTS_DIR
    const absolutePath = path.resolve(PROJECTS_DIR, filePath);
    if (!absolutePath.startsWith(PROJECTS_DIR)) {
      return res.status(403).json({ error: 'Path traversal not allowed' });
    }

    // Check file exists
    await fs.access(absolutePath);

    // Read and return content
    const content = await fs.readFile(absolutePath, 'utf-8');
    res.type('text/plain').send(content);

  } catch (err) {
    if (err.code === 'ENOENT') {
      return res.status(404).json({ error: 'File not found' });
    }
    console.error('Error reading file:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /api/file
 * Body: { path: "relative/path/to/file.tex", content: "..." }
 * Writes the content to the file.
 */
router.post('/file', async (req, res) => {
  try {
    const { path: filePath, content } = req.body;
    if (!filePath || content === undefined) {
      return res.status(400).json({ error: 'Missing "path" or "content" in body' });
    }

    // Security: resolve and verify
    const absolutePath = path.resolve(PROJECTS_DIR, filePath);
    if (!absolutePath.startsWith(PROJECTS_DIR)) {
      return res.status(403).json({ error: 'Path traversal not allowed' });
    }

    // Ensure parent directory exists
    await fs.mkdir(path.dirname(absolutePath), { recursive: true });

    // Write content
    await fs.writeFile(absolutePath, content, 'utf-8');
    res.json({ success: true, path: filePath });

  } catch (err) {
    console.error('Error writing file:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
```

#### 1.2.5 — Register the routes in the server

Add to `server/index.js`:
```javascript
import fileRoutes from './routes/files.js';
app.use('/api', fileRoutes);
```

### Security Considerations
- **Path traversal protection**: Always resolve the path and verify it starts with `PROJECTS_DIR`. Without this, a malicious request like `GET /api/file?path=../../etc/passwd` could read system files.
- **No arbitrary file execution**: We only read/write text files. Never execute file contents.
- **Content size limit**: Express `json()` middleware has a default 100KB limit. For LaTeX files, this is fine. If needed later, increase with `express.json({ limit: '5mb' })`.

### Do's
- ✅ Always validate the `path` parameter before any filesystem operation
- ✅ Use `path.resolve()` + `startsWith()` for path traversal protection
- ✅ Return proper HTTP status codes (400, 403, 404, 500)
- ✅ Use `utf-8` encoding for all text files
- ✅ Create parent directories with `{ recursive: true }` on write

### Don'ts
- ❌ Don't use `path.join()` without checking the resolved path — it doesn't prevent `../` traversal
- ❌ Don't return file contents as JSON — use `text/plain` for the GET endpoint (preserves exact content)
- ❌ Don't allow writing to paths outside the `projects/` directory
- ❌ Don't add file upload (multipart) here — that's a separate endpoint in Phase 4

### Definition of Done
- [ ] `GET /api/file?path=sample/main.tex` returns the file content as plain text
- [ ] `POST /api/file` with `{ path: "sample/test.txt", content: "hello" }` creates the file
- [ ] Path traversal attempts return 403
- [ ] Missing files return 404
- [ ] Missing parameters return 400

### How to Test
```bash
# Read the sample file
curl http://localhost:3001/api/file?path=sample/main.tex
# Should return the LaTeX source code

# Write a test file
curl -X POST http://localhost:3001/api/file \
  -H "Content-Type: application/json" \
  -d '{"path":"sample/test.txt","content":"hello world"}'
# Should return { success: true }

# Verify the file was written
curl http://localhost:3001/api/file?path=sample/test.txt
# Should return "hello world"

# Test path traversal protection
curl http://localhost:3001/api/file?path=../../etc/passwd
# Should return 403

# Test missing file
curl http://localhost:3001/api/file?path=nonexistent.tex
# Should return 404
```

---

## Step 3: Create the CodeMirror Editor Module

### What to Do
Build `src/js/editor.js` — the module that initializes the CodeMirror 6 editor inside the `#editor-container` div.

### Sub-Steps

#### 1.2.6 — Editor Module Structure

```javascript
// src/js/editor.js
import { EditorView, keymap, lineNumbers, highlightActiveLine,
         highlightActiveLineGutter, drawSelection,
         rectangularSelection, highlightSpecialChars } from '@codemirror/view';
import { EditorState, Compartment } from '@codemirror/state';
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import { syntaxHighlighting, defaultHighlightStyle,
         bracketMatching, indentOnInput } from '@codemirror/language';
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search';
import { oneDark } from '@codemirror/theme-one-dark';

// LaTeX language (use whichever approach works — see Step 1 research)
import { StreamLanguage } from '@codemirror/language';
import { stex } from '@codemirror/legacy-modes/mode/stex';

const latexLanguage = StreamLanguage.define(stex);

// Module-level reference to the editor instance
let editorView = null;

/**
 * Initialize the CodeMirror editor.
 * @param {HTMLElement} container - The DOM element to mount the editor into
 * @param {string} initialContent - The initial document text
 * @returns {EditorView} The editor instance
 */
export function initEditor(container, initialContent = '') {
  // Clear any previous editor
  container.innerHTML = '';

  const state = EditorState.create({
    doc: initialContent,
    extensions: [
      // Line numbers & gutter
      lineNumbers(),
      highlightActiveLineGutter(),

      // Editing features
      history(),
      drawSelection(),
      rectangularSelection(),
      highlightSpecialChars(),
      indentOnInput(),
      bracketMatching(),
      highlightActiveLine(),
      highlightSelectionMatches(),

      // Keymaps
      keymap.of([
        ...defaultKeymap,
        ...historyKeymap,
        ...searchKeymap,
        indentWithTab,
      ]),

      // Syntax highlighting
      latexLanguage,
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),

      // Theme
      oneDark,

      // Line wrapping (on by default)
      EditorView.lineWrapping,

      // Make editor fill its container
      EditorView.theme({
        '&': { height: '100%' },
        '.cm-scroller': { overflow: 'auto' },
      }),
    ],
  });

  editorView = new EditorView({
    state,
    parent: container,
  });

  return editorView;
}

/**
 * Get the current text content of the editor.
 * @returns {string} The full document text
 */
export function getContent() {
  if (!editorView) {
    console.warn('Editor not initialized');
    return '';
  }
  return editorView.state.doc.toString();
}

/**
 * Set the editor content (replaces everything).
 * @param {string} content - New document text
 */
export function setContent(content) {
  if (!editorView) return;
  editorView.dispatch({
    changes: {
      from: 0,
      to: editorView.state.doc.length,
      insert: content,
    },
  });
}

/**
 * Get the EditorView instance (for advanced operations by other modules).
 * @returns {EditorView|null}
 */
export function getEditorView() {
  return editorView;
}
```

### Key Design Decisions
- **Module-level singleton**: Only one editor instance exists. Stored in the module scope.
- **Exported API**: `initEditor()`, `getContent()`, `setContent()`, `getEditorView()` — clean interface for other modules.
- **Extensions are explicit**: We list every extension instead of using `basicSetup` so we have full control. `basicSetup` bundles too many things we might not want.
- **`EditorView.lineWrapping`**: Enabled by default. Users can toggle it later (Phase 2).
- **Height: 100%**: The editor fills its parent container completely.

### Do's
- ✅ Export `getContent()` — the compile button module needs it to save before compiling
- ✅ Export `setContent()` — useful for loading different files later
- ✅ Set the editor height to 100% of its container
- ✅ Enable `bracketMatching()` — even though it's "Phase 2 level", it's included in basic editing
- ✅ Use `indentWithTab` — Tab key should indent, not change focus

### Don'ts
- ❌ Don't add autocompletion extensions — that's Feature 2.1
- ❌ Don't add code folding extensions — that's Feature 2.4
- ❌ Don't add custom keybindings (Vim/Emacs) — that's Feature 2.8
- ❌ Don't add `onChange` listeners — that's for auto-compile (Phase 3) and auto-save (Phase 6)
- ❌ Don't try to validate LaTeX syntax — just highlight it

### Definition of Done
- [ ] `src/js/editor.js` exists with the code above
- [ ] Calling `initEditor(container, "test")` renders a code editor with "test" as content
- [ ] `getContent()` returns the current editor text
- [ ] `setContent("new text")` replaces the editor text
- [ ] The editor uses the oneDark theme (dark background, colored syntax)

### How to Test
1. Temporarily add to `app.js`:
   ```javascript
   import { initEditor, getContent } from './editor.js';
   const container = document.getElementById('editor-container');
   initEditor(container, '\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}');
   console.log(getContent()); // should log the LaTeX text
   ```
2. Check: editor renders with line numbers, dark theme
3. Check: `\documentclass` is highlighted differently from `Hello`
4. Check: typing works, undo/redo works

---

## Step 4: Load File Content from Backend on Startup

### What to Do
When the app starts, fetch the contents of the default file (`main.tex` from the sample project) from the backend and load it into the editor.

### Sub-Steps

#### 1.2.7 — Add file loading logic to `app.js`

```javascript
// src/js/app.js
import { initEditor } from './editor.js';

// Configuration — will be dynamic later (Phase 4)
const PROJECT_PATH = 'sample';
const MAIN_FILE = 'main.tex';

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Pdleaf v0.1.0 — Starting...');

  // 1. Get the editor container
  const container = document.getElementById('editor-container');
  if (!container) {
    console.error('FATAL: #editor-container not found');
    return;
  }

  // 2. Fetch the file content from the backend
  let content = '';
  try {
    const response = await fetch(`/api/file?path=${PROJECT_PATH}/${MAIN_FILE}`);
    if (response.ok) {
      content = await response.text();
      console.log(`Loaded ${MAIN_FILE} (${content.length} characters)`);
    } else {
      console.error(`Failed to load ${MAIN_FILE}: ${response.status}`);
      content = '% Could not load file. Check that the server is running.\n';
    }
  } catch (err) {
    console.error('Network error loading file:', err);
    content = '% Server unavailable. Start the backend with: npm run dev:server\n';
  }

  // 3. Initialize the editor with the loaded content
  initEditor(container, content);
  console.log('Pdleaf: Editor initialized ✅');
});
```

### Key Design Decisions
- **Hardcoded project/file for now**: `PROJECT_PATH` and `MAIN_FILE` are constants. In Phase 4, these will come from the project dashboard and file tree.
- **Graceful degradation**: If the backend is down, the editor still loads with an error comment instead of crashing.
- **`response.text()`**: We read the file as plain text, not JSON. This preserves exact content including line endings.

### Do's
- ✅ Use `response.text()` not `response.json()` — file contents are plain text
- ✅ Handle network errors gracefully — show a helpful message, don't crash
- ✅ Log the file size on successful load (helps with debugging)

### Don'ts
- ❌ Don't hardcode the file content — always fetch from the backend
- ❌ Don't show a blocking error dialog if the file fails to load — just put an error comment in the editor
- ❌ Don't add "open file" or "file tabs" logic — that's Phase 4

### Definition of Done
- [ ] On page load, the editor automatically shows the contents of `projects/sample/main.tex`
- [ ] If the backend is not running, the editor shows an error comment (doesn't crash)
- [ ] The console logs "Loaded main.tex (N characters)" on success
- [ ] The console logs "Editor initialized ✅"

### How to Test
1. Start both servers: `npm run dev`
2. Browser opens → editor should show the sample LaTeX document
3. The LaTeX syntax should be highlighted (commands in one color, comments in another)
4. Stop the backend (Ctrl+C on the server) → reload the page → editor should show error comment
5. Restart the backend → reload → editor shows the real content again

---

## Step 5: Wire Up File Saving

### What to Do
Create a `saveFile()` function that saves the current editor content to the backend. This will be called by the compile button (Feature 1.4) before compilation.

### Sub-Steps

#### 1.2.8 — Create a save utility

Add to `src/js/editor.js` (or create a separate `src/js/fileOps.js`):

```javascript
// Configuration — same constants as app.js (will be centralized later)
const PROJECT_PATH = 'sample';
const MAIN_FILE = 'main.tex';

/**
 * Save the current editor content to the backend.
 * @returns {Promise<boolean>} True if save succeeded
 */
export async function saveCurrentFile() {
  const content = getContent();
  try {
    const response = await fetch('/api/file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: `${PROJECT_PATH}/${MAIN_FILE}`,
        content,
      }),
    });

    if (response.ok) {
      console.log('File saved successfully');
      return true;
    } else {
      const err = await response.json();
      console.error('Save failed:', err);
      return false;
    }
  } catch (err) {
    console.error('Network error saving file:', err);
    return false;
  }
}
```

### Key Design Decisions
- **Returns boolean**: Simple success/failure. The caller (compile button) decides what to do.
- **Logs errors but doesn't show UI**: The caller handles UI feedback. This is a utility function.
- **Saves the entire file**: No partial saves or diffs. Full content every time. Good enough for Phase 1.

### Definition of Done
- [ ] `saveCurrentFile()` sends the editor content to `POST /api/file`
- [ ] Returns `true` on success, `false` on failure
- [ ] After saving, the file on disk matches the editor content exactly
- [ ] Works correctly with Unicode characters (important for LaTeX math symbols)

### How to Test
1. Open the app → edit the document → add "SAVE TEST" somewhere
2. In the browser console: `import('./editor.js').then(m => m.saveCurrentFile())`
3. Check the file on disk: `cat projects/sample/main.tex` — should contain "SAVE TEST"
4. Type Unicode: `αβγ` → save → check file → Unicode should be preserved

---

## Final Acceptance Checklist — Feature 1.2 Complete

| # | Check | Status |
|---|-------|--------|
| 1 | CodeMirror packages installed in `package.json` | ☐ |
| 2 | `GET /api/file?path=sample/main.tex` returns file content | ☐ |
| 3 | `POST /api/file` saves content to disk | ☐ |
| 4 | Path traversal (e.g., `../../etc/passwd`) returns 403 | ☐ |
| 5 | Editor renders in the left panel with dark theme | ☐ |
| 6 | LaTeX syntax is highlighted (commands, comments, math) | ☐ |
| 7 | Line numbers visible in the gutter | ☐ |
| 8 | Active line is highlighted | ☐ |
| 9 | Bracket matching works (cursor on `{` highlights matching `}`) | ☐ |
| 10 | Undo (Ctrl+Z) and Redo (Ctrl+Shift+Z) work | ☐ |
| 11 | Tab key indents (doesn't change focus) | ☐ |
| 12 | File content loads automatically from backend on page load | ☐ |
| 13 | `getContent()` returns the current text | ☐ |
| 14 | `saveCurrentFile()` writes content to disk | ☐ |
| 15 | Editor fills 100% of its container (no scrollbars on the panel itself) | ☐ |
| 16 | No JavaScript errors in the console | ☐ |

> **When all 16 checks pass, Feature 1.2 is DONE. Proceed to Feature 1.3 (TeX Live Compilation Backend).**
