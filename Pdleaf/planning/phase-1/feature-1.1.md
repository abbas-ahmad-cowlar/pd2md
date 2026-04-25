# Feature 1.1 — Project Scaffolding & Web App Shell

> **Phase**: 1 | **Feature**: 1 of 6
> **Goal**: Set up the entire project foundation — directory structure, HTML entry point, CSS design system, backend server, dev server configuration, and a sample LaTeX project. When this feature is done, you should be able to run `npm run dev` and see a dark-themed web page with two empty panels and a toolbar.
> **Estimated Effort**: 2–4 hours
> **Dependencies**: Node.js 18+ installed. npm available.

---

## Overview

This is the very first feature. Everything else depends on it. We are creating:
1. The npm project with all base dependencies
2. The folder structure that the entire app will live in
3. The HTML page with the three-panel layout
4. The CSS design system (custom properties, reset, dark theme)
5. The Express backend server
6. The Vite frontend dev server
7. A sample LaTeX project to test with

---

## Step 1: Initialize the npm Project

### What to Do
Create the npm project and install all Phase 1 dependencies.

### Sub-Steps

#### 1.1.1 — Create `package.json`
```bash
cd Pdleaf
npm init -y
```
Edit `package.json` to set:
- `"name": "pdleaf"`
- `"version": "0.1.0"`
- `"description": "A local-first, free, personal LaTeX editor with live preview"`
- `"type": "module"` (use ES modules throughout)
- `"scripts"`:
  ```json
  {
    "dev": "concurrently \"npm run dev:server\" \"npm run dev:client\"",
    "dev:server": "node --watch server/index.js",
    "dev:client": "vite",
    "build": "vite build",
    "start": "node server/index.js"
  }
  ```

#### 1.1.2 — Install Dependencies
```bash
# Backend
npm install express cors

# Frontend build tool
npm install -D vite

# Dev utilities
npm install -D concurrently
```

> **Note**: CodeMirror and pdf.js will be installed in their respective features (1.2 and 1.5). Don't install them here.

#### 1.1.3 — Create `.gitignore`
```gitignore
node_modules/
dist/
.env

# LaTeX output files
*.aux
*.log
*.toc
*.bbl
*.blg
*.out
*.synctex.gz
*.fdb_latexmk
*.fls
*.pdf

# OS files
.DS_Store
Thumbs.db
```

### Definition of Done
- [ ] `package.json` exists with correct name, version, type, and scripts
- [ ] All dependencies are installed (`node_modules/` exists)
- [ ] `.gitignore` exists with appropriate entries
- [ ] Running `npm run dev:server` starts without errors (even if no routes exist yet)

### How to Test
```bash
npm run dev:server
# Should output: "Server listening on port 3001" (or similar)
# Ctrl+C to stop
```

---

## Step 2: Create the Directory Structure

### What to Do
Create all folders and empty placeholder files for the project.

### Sub-Steps

#### 1.1.4 — Create the directory tree
```
Pdleaf/
├── src/                        # Frontend source
│   ├── index.html              # Main HTML file
│   ├── css/
│   │   └── style.css           # Global styles + design system
│   ├── js/
│   │   ├── app.js              # Frontend entry point
│   │   ├── editor.js           # CodeMirror (Feature 1.2 — empty for now)
│   │   ├── compiler.js         # Compile button (Feature 1.4 — empty for now)
│   │   └── pdfViewer.js        # PDF viewer (Feature 1.5 — empty for now)
│   └── assets/
│       └── favicon.ico         # App icon (optional)
├── server/                     # Backend source
│   ├── index.js                # Express server entry point
│   ├── routes/
│   │   ├── compile.js          # Compilation endpoint (Feature 1.3 — stub)
│   │   └── files.js            # File read/write endpoints (Feature 1.2 — stub)
│   └── utils/
│       └── latex.js            # LaTeX compilation helper (Feature 1.3 — stub)
├── projects/                   # User projects directory
│   └── sample/                 # Sample starter project
│       └── main.tex            # Sample LaTeX document
├── templates/                  # Project templates (Phase 5 — empty for now)
├── package.json
├── vite.config.js
├── .gitignore
└── README.md
```

#### 1.1.5 — Create stub files
For files that belong to later features (editor.js, compiler.js, pdfViewer.js, compile.js, files.js, latex.js), create them with a comment placeholder:
```javascript
// This module will be implemented in Feature 1.X
// Placeholder for now.
export default {};
```

### Definition of Done
- [ ] All directories exist
- [ ] All stub files exist with placeholder comments
- [ ] The directory structure matches the specification above

### How to Test
```bash
find . -type f -not -path './node_modules/*' | sort
# Should list all files matching the tree above
```

---

## Step 3: Create the HTML Shell

### What to Do
Build `src/index.html` — the main HTML page with the three-panel layout structure.

### Sub-Steps

#### 1.1.6 — HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pdleaf — LaTeX Editor</title>
  <link rel="stylesheet" href="/css/style.css">
</head>
<body>
  <!-- Top Toolbar -->
  <header id="toolbar">
    <div class="toolbar-left">
      <span id="project-name" class="toolbar-title">sample</span>
    </div>
    <div class="toolbar-center">
      <button id="btn-compile" class="btn btn-primary">
        <span class="btn-icon">▶</span>
        <span class="btn-text">Compile</span>
      </button>
      <span id="compile-status" class="status-text"></span>
    </div>
    <div class="toolbar-right">
      <!-- Future: settings, theme toggle, etc. -->
    </div>
  </header>

  <!-- Main Content Area -->
  <main id="workspace">
    <!-- Sidebar (placeholder — hidden in Phase 1) -->
    <aside id="sidebar" class="panel panel-sidebar">
      <!-- File tree goes here in Phase 4 -->
    </aside>

    <!-- Editor Panel -->
    <section id="editor-panel" class="panel panel-editor">
      <!-- CodeMirror mounts here in Feature 1.2 -->
      <div id="editor-container"></div>
    </section>

    <!-- Resizable Divider -->
    <div id="divider" class="divider"></div>

    <!-- Preview Panel -->
    <section id="preview-panel" class="panel panel-preview">
      <div id="pdf-container">
        <p class="placeholder-text">No PDF yet — click Compile</p>
      </div>
    </section>
  </main>

  <!-- Bottom Status Bar -->
  <footer id="statusbar">
    <span id="cursor-position">Ln 1, Col 1</span>
    <span id="file-status">Ready</span>
  </footer>

  <script type="module" src="/js/app.js"></script>
</body>
</html>
```

### Key Design Decisions
- **IDs are descriptive and unique**: Every interactive element has an `id` for easy JS targeting and testing
- **Semantic HTML**: `<header>`, `<main>`, `<aside>`, `<section>`, `<footer>`
- **The sidebar is present but hidden**: Its `display: none` is set via CSS. Will be shown in Phase 4
- **The divider is a separate element**: Not part of either panel. It's a standalone draggable element
- **Script loaded as ES module**: `type="module"` enables `import`/`export` syntax

### Definition of Done
- [ ] `src/index.html` exists with the structure above
- [ ] All elements have unique `id` attributes
- [ ] The `<script>` tag loads `app.js` as a module
- [ ] Opening the HTML directly in a browser shows the raw structure (unstyled is fine)

### How to Test
1. Open `src/index.html` directly in a browser (not via Vite yet)
2. Should see raw HTML elements: toolbar, two sections, status bar
3. Inspect the DOM — all `id` values should be present
4. No JavaScript errors in the console (app.js may 404 if not served by Vite, that's ok)

---

## Step 4: Create the CSS Design System

### What to Do
Build `src/css/style.css` — the global stylesheet that defines the visual foundation of the entire app. This is the most important step for the "look and feel" of Pdleaf.

### Sub-Steps

#### 1.1.7 — CSS Custom Properties (Design Tokens)
Define all colors, spacing, and typography as CSS custom properties on `:root`. This makes future theming (light/dark) trivial.

```css
:root {
  /* Colors — Dark Theme */
  --bg-primary: #1e1e2e;        /* Main background (deep navy-charcoal) */
  --bg-secondary: #252536;      /* Panel backgrounds */
  --bg-tertiary: #2d2d44;       /* Hover states, active items */
  --bg-toolbar: #1a1a2e;        /* Toolbar and status bar */
  --bg-divider: #3a3a5c;        /* Divider bar */

  --text-primary: #e0e0e8;      /* Main text */
  --text-secondary: #a0a0b8;    /* Muted text */
  --text-placeholder: #666680;  /* Placeholder text */

  --accent-primary: #7c6ff7;    /* Primary accent (purple) */
  --accent-success: #4ade80;    /* Success green */
  --accent-error: #f87171;      /* Error red */
  --accent-warning: #fbbf24;    /* Warning yellow */

  --border-color: #3a3a5c;      /* Borders and separators */
  --border-radius: 6px;         /* Standard border radius */

  /* Spacing */
  --toolbar-height: 42px;
  --statusbar-height: 24px;
  --divider-width: 5px;
  --sidebar-width: 0px;          /* Hidden in Phase 1 */

  /* Typography */
  --font-ui: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
  --font-size-sm: 12px;
  --font-size-md: 13px;
  --font-size-lg: 14px;

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
}
```

#### 1.1.8 — CSS Reset
```css
*, *::before, *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  overflow: hidden;
  font-family: var(--font-ui);
  font-size: var(--font-size-md);
  color: var(--text-primary);
  background: var(--bg-primary);
}
```

#### 1.1.9 — Layout Styles
```css
/* Full-height layout */
body {
  display: flex;
  flex-direction: column;
}

/* Toolbar */
#toolbar {
  height: var(--toolbar-height);
  background: var(--bg-toolbar);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  flex-shrink: 0;
}

/* Main workspace — fills remaining height */
#workspace {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Sidebar (hidden in Phase 1) */
#sidebar {
  width: var(--sidebar-width);
  display: none;  /* Enabled in Phase 4 */
}

/* Editor panel */
#editor-panel {
  flex: 1;
  overflow: hidden;
  background: var(--bg-secondary);
}

#editor-container {
  width: 100%;
  height: 100%;
}

/* Divider */
.divider {
  width: var(--divider-width);
  background: var(--bg-divider);
  cursor: col-resize;
  flex-shrink: 0;
  transition: background var(--transition-fast);
}

.divider:hover {
  background: var(--accent-primary);
}

/* Preview panel */
#preview-panel {
  flex: 1;
  overflow: auto;
  background: var(--bg-secondary);
}

#pdf-container {
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Status bar */
#statusbar {
  height: var(--statusbar-height);
  background: var(--bg-toolbar);
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  flex-shrink: 0;
}
```

#### 1.1.10 — Button & Component Styles
```css
/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 14px;
  border: none;
  border-radius: var(--border-radius);
  font-family: var(--font-ui);
  font-size: var(--font-size-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary {
  background: var(--accent-primary);
  color: white;
}

.btn-primary:hover {
  filter: brightness(1.15);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Placeholder text */
.placeholder-text {
  color: var(--text-placeholder);
  font-size: var(--font-size-lg);
  text-align: center;
  margin-top: 40%;
}

/* Toolbar title */
.toolbar-title {
  font-weight: 600;
  font-size: var(--font-size-lg);
  color: var(--text-primary);
}

/* Status text (compile duration, etc.) */
.status-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-left: 10px;
}
```

#### 1.1.11 — Load Google Font (Inter)
Add to the `<head>` of `index.html`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Key Design Decisions
- **Dark theme by default**: Professional look, matches code editor expectations
- **Purple accent** (`#7c6ff7`): Distinctive, modern, differentiates from Overleaf's green
- **All values in CSS custom properties**: Changing the entire theme = changing ~15 variables
- **No CSS framework**: Full control over every pixel
- **Flexbox layout**: The body is a flex column (toolbar → workspace → statusbar). Workspace is a flex row (sidebar → editor → divider → preview)

### Definition of Done
- [ ] `src/css/style.css` exists with all the rules above
- [ ] The page has a dark background with proper contrast
- [ ] The toolbar is at the top, fixed height
- [ ] The workspace fills the remaining height
- [ ] The editor and preview panels are side by side
- [ ] The divider is visible between the panels
- [ ] The status bar is at the bottom, fixed height
- [ ] The "Compile" button is styled with the accent color
- [ ] Fonts load correctly (Inter for UI, JetBrains Mono available for code)

### How to Test
1. Run `npm run dev:client` → open in browser
2. Should see: dark background, toolbar at top, two panels, status bar at bottom
3. The "Compile" button should be purple
4. Hover over the divider → it should change color (purple highlight)
5. The text should use the Inter font (check in DevTools computed styles)

---

## Step 5: Create the Express Backend Server

### What to Do
Build `server/index.js` — a minimal Express server that serves as the API backend.

### Sub-Steps

#### 1.1.12 — Server Entry Point
```javascript
// server/index.js
import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Serve output PDFs with no-cache headers
app.use('/output', express.static(
  path.join(__dirname, '..', 'projects'),
  { setHeaders: (res) => res.set('Cache-Control', 'no-cache') }
));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
  console.log(`Pdleaf server running on http://localhost:${PORT}`);
});
```

#### 1.1.13 — TeX Live verification on startup
Add to `server/index.js` or a separate utility:
```javascript
import { execFile } from 'child_process';

function checkTexLive() {
  return new Promise((resolve) => {
    execFile('pdflatex', ['--version'], (error, stdout) => {
      if (error) {
        console.warn('⚠️  pdflatex not found on PATH. LaTeX compilation will not work.');
        console.warn('   Please install TeX Live: https://tug.org/texlive/');
        resolve(false);
      } else {
        const version = stdout.split('\n')[0];
        console.log(`✅ TeX Live found: ${version}`);
        resolve(true);
      }
    });
  });
}

// Call on startup
checkTexLive();
```

### Definition of Done
- [ ] `server/index.js` exists and starts without errors
- [ ] `GET /api/health` returns `{ status: 'ok' }`
- [ ] The server logs whether TeX Live is found on startup
- [ ] CORS is enabled (frontend on port 3000 can call backend on port 3001)

### How to Test
```bash
npm run dev:server
# Should see: "Pdleaf server running on http://localhost:3001"
# Should see: "✅ TeX Live found: ..." (if installed)
curl http://localhost:3001/api/health
# Should return: {"status":"ok","timestamp":"..."}
```

---

## Step 6: Configure Vite (Frontend Dev Server)

### What to Do
Create `vite.config.js` to configure the frontend dev server. Vite will serve the frontend and proxy API requests to the Express backend.

### Sub-Steps

#### 1.1.14 — Vite Configuration
```javascript
// vite.config.js
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  root: 'src',           // Frontend source lives in src/
  publicDir: '../public', // Static assets (if any)
  server: {
    port: 3000,
    open: true,           // Auto-open browser on start
    proxy: {
      // Proxy API calls to the Express backend
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      // Proxy PDF output files to the Express backend
      '/output': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../dist',    // Build output goes to dist/
    emptyOutDir: true,
  },
});
```

### Key Points
- **`root: 'src'`**: Vite serves from the `src/` directory, so `index.html` is at `src/index.html`
- **`proxy`**: All `/api/*` and `/output/*` requests are forwarded to Express on port 3001. This means the frontend can use relative URLs like `/api/compile` without worrying about CORS or port differences in development.
- **`open: true`**: Automatically opens the browser when you run `npm run dev`

### Definition of Done
- [ ] `vite.config.js` exists at the project root
- [ ] Running `npm run dev:client` starts Vite on port 3000
- [ ] Visiting `http://localhost:3000` shows the HTML page
- [ ] `/api/health` proxied through Vite returns the backend response

### How to Test
1. Start both servers: `npm run dev`
2. Browser auto-opens to `http://localhost:3000`
3. Open DevTools → Console → type `fetch('/api/health').then(r => r.json()).then(console.log)`
4. Should log `{ status: 'ok', timestamp: '...' }` — proving the proxy works

---

## Step 7: Create the Sample LaTeX Project

### What to Do
Create a sample LaTeX document in `projects/sample/main.tex` that serves as the default project for testing.

### Sub-Steps

#### 1.1.15 — Sample `main.tex`
```latex
\documentclass[12pt]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath, amssymb}
\usepackage{geometry}
\geometry{a4paper, margin=1in}

\title{Welcome to Pdleaf}
\author{Your Name}
\date{\today}

\begin{document}

\maketitle

\section{Introduction}
Welcome to \textbf{Pdleaf} --- your personal, local-first \LaTeX{} editor.

This is a sample document to help you get started. Try editing this text and clicking \textbf{Compile} to see the PDF update.

\section{Mathematics}
Here's a famous equation:
\begin{equation}
    E = mc^2
\end{equation}

And here's an integral:
\begin{equation}
    \int_{0}^{\infty} e^{-x^2} \, dx = \frac{\sqrt{\pi}}{2}
\end{equation}

\section{Lists}
\begin{itemize}
    \item Edit \LaTeX{} code in the left panel
    \item Click \textbf{Compile} to generate the PDF
    \item The PDF appears in the right panel
    \item Drag the divider to resize panels
\end{itemize}

\section{Conclusion}
Happy writing! Modify this document freely --- it's your playground.

\end{document}
```

### Why This Specific Document
- **Uses common packages** (`amsmath`, `geometry`): Verifies that packages work
- **Has math**: Tests math rendering (important for academic users)
- **Has multiple sections**: Verifies section formatting and creates a longer document
- **Has a list**: Tests environment rendering
- **Is friendly**: Makes a good first impression when the app loads
- **Is exactly 1 page**: Easy to verify the PDF viewer works without pagination issues

### Definition of Done
- [ ] `projects/sample/main.tex` exists with the content above
- [ ] Compiling it with `pdflatex main.tex` (from the sample directory) produces a valid PDF
- [ ] The PDF is exactly 1 page with title, sections, math, and a list

### How to Test
```bash
cd projects/sample
pdflatex main.tex
# Should produce main.pdf without errors
# Open main.pdf — should show "Welcome to Pdleaf" document
```

---

## Step 8: Create `app.js` (Frontend Entry Point)

### What to Do
Create `src/js/app.js` — the main JavaScript file that initializes the application.

### Sub-Steps

#### 1.1.16 — App Initialization
```javascript
// src/js/app.js

// Phase 1 only: Log that the app started
console.log('Pdleaf v0.1.0 — Starting...');

// Feature 1.2 will add: import and initialize the editor
// Feature 1.4 will add: import and initialize the compile button
// Feature 1.5 will add: import and initialize the PDF viewer
// Feature 1.6 will add: import and initialize the split panel divider

// For now, just verify the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('Pdleaf: DOM ready');

  // Verify critical elements exist
  const requiredIds = [
    'toolbar', 'btn-compile', 'compile-status',
    'workspace', 'editor-panel', 'editor-container',
    'divider', 'preview-panel', 'pdf-container',
    'statusbar', 'cursor-position', 'file-status'
  ];

  for (const id of requiredIds) {
    if (!document.getElementById(id)) {
      console.error(`FATAL: Missing element #${id}`);
    }
  }

  console.log('Pdleaf: All DOM elements verified ✅');
});
```

### Definition of Done
- [ ] `src/js/app.js` exists
- [ ] Loading the page shows "Pdleaf v0.1.0 — Starting..." in the console
- [ ] Shows "Pdleaf: All DOM elements verified ✅" after DOM loads
- [ ] If any element is missing, logs an error

### How to Test
1. Open `http://localhost:3000` with DevTools console open
2. Should see both log messages
3. Should NOT see any FATAL errors

---

## Final Acceptance Checklist — Feature 1.1 Complete

Run through this checklist to verify Feature 1.1 is done:

| # | Check | Status |
|---|-------|--------|
| 1 | `npm run dev` starts both frontend (port 3000) and backend (port 3001) | ☐ |
| 2 | Browser auto-opens to `http://localhost:3000` | ☐ |
| 3 | Page has a dark theme with purple accent color | ☐ |
| 4 | Toolbar visible at top with "sample" project name and "Compile" button | ☐ |
| 5 | Two panels visible side by side (editor area + preview area) | ☐ |
| 6 | A divider bar separates the panels (highlights on hover) | ☐ |
| 7 | Status bar visible at bottom with "Ln 1, Col 1" and "Ready" | ☐ |
| 8 | Preview panel shows "No PDF yet — click Compile" | ☐ |
| 9 | Console shows "Pdleaf v0.1.0" and "All DOM elements verified ✅" | ☐ |
| 10 | `fetch('/api/health')` from browser console returns ok | ☐ |
| 11 | Server logs show TeX Live detection result | ☐ |
| 12 | `projects/sample/main.tex` exists and compiles manually | ☐ |
| 13 | No JavaScript errors in the browser console | ☐ |
| 14 | No npm warnings about missing peer dependencies | ☐ |

> **When all 14 checks pass, Feature 1.1 is DONE. Proceed to Feature 1.2 (CodeMirror Integration).**
