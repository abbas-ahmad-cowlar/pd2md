# Feature 1.3 — TeX Live Compilation Backend

> **Phase**: 1 | **Feature**: 3 of 6
> **Goal**: Build the backend API endpoint that compiles a LaTeX project using the locally installed TeX Live distribution. When this is done, sending a POST request to `/api/compile` should run `latexmk`, produce a PDF, and return success/failure with the PDF URL.
> **Estimated Effort**: 3–5 hours
> **Dependencies**: Feature 1.1 (backend server running), Feature 1.2 (file API to save before compile).
> **External Dependency**: TeX Live (specifically `latexmk` and `pdflatex`) must be installed and on the system PATH.

---

## Overview

This feature builds the compilation engine — the heart of Pdleaf. We are:
1. Creating a robust LaTeX compilation helper that wraps `latexmk`
2. Creating the `/api/compile` endpoint
3. Configuring output directory separation (source vs. build artifacts)
4. Implementing timeout protection for runaway compilations
5. Serving the output PDF via Express static middleware

**What this feature does NOT include**: Error log parsing (Phase 3), auto-compile on edit (Phase 3), engine selection dropdown (Phase 6/7). We just run `pdflatex` via `latexmk` and return raw results.

---

## Step 1: Create the LaTeX Compilation Helper

### What to Do
Build `server/utils/latex.js` — a helper module that runs `latexmk` on a LaTeX project and returns structured results.

### Sub-Steps

#### 1.3.1 — The compilation function

```javascript
// server/utils/latex.js
import { execFile } from 'child_process';
import path from 'path';
import fs from 'fs/promises';

/**
 * Compile a LaTeX project using latexmk.
 *
 * @param {string} projectDir - Absolute path to the project directory
 * @param {string} mainFile - Name of the main .tex file (e.g., 'main.tex')
 * @param {object} options
 * @param {string} options.engine - 'pdflatex' | 'xelatex' | 'lualatex' (default: 'pdflatex')
 * @param {number} options.timeout - Timeout in ms (default: 60000)
 * @returns {Promise<{success, pdfPath, log, duration}>}
 */
export async function compileLaTeX(projectDir, mainFile, options = {}) {
  const {
    engine = 'pdflatex',
    timeout = 60000,  // 60 seconds
  } = options;

  const startTime = Date.now();
  const outputDir = path.join(projectDir, 'output');

  // Ensure output directory exists
  await fs.mkdir(outputDir, { recursive: true });

  // Build the latexmk command arguments
  const args = [
    `-${engine === 'pdflatex' ? 'pdf' : engine === 'xelatex' ? 'pdfxe' : 'pdflua'}`,
    '-interaction=nonstopmode',   // Don't stop on errors
    '-synctex=1',                 // Generate SyncTeX file (for Phase 3)
    '-halt-on-error',             // Stop at first error (cleaner output)
    `-outdir=${outputDir}`,       // Output to separate directory
    mainFile,                     // The main .tex file
  ];

  return new Promise((resolve) => {
    const child = execFile('latexmk', args, {
      cwd: projectDir,
      timeout,                     // Kill if exceeds timeout
      maxBuffer: 1024 * 1024 * 5,  // 5MB stdout/stderr buffer
      env: { ...process.env },     // Inherit PATH (where TeX Live is)
    }, async (error, stdout, stderr) => {
      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      const log = stdout + '\n' + stderr;

      // Determine the expected PDF filename
      const pdfName = mainFile.replace(/\.tex$/, '.pdf');
      const pdfPath = path.join(outputDir, pdfName);

      // Check if PDF was actually produced
      let pdfExists = false;
      try {
        await fs.access(pdfPath);
        pdfExists = true;
      } catch {
        pdfExists = false;
      }

      if (error) {
        // Compilation failed or timed out
        const isTimeout = error.killed || error.code === 'ETIMEDOUT';
        resolve({
          success: false,
          pdfPath: pdfExists ? pdfPath : null,
          log,
          duration: parseFloat(duration),
          error: isTimeout
            ? `Compilation timed out after ${timeout / 1000}s`
            : `Compilation failed with exit code ${error.code}`,
          timedOut: isTimeout,
        });
      } else {
        resolve({
          success: true,
          pdfPath,
          log,
          duration: parseFloat(duration),
          error: null,
          timedOut: false,
        });
      }
    });
  });
}
```

### Key Design Decisions

#### Why `latexmk` instead of raw `pdflatex`?
- `pdflatex` requires multiple manual runs to resolve cross-references (`\ref`, `\cite`, table of contents)
- `latexmk` automatically detects when re-runs are needed and does them
- `latexmk` handles `bibtex`/`biber` automatically
- It's the same tool Overleaf uses internally

#### Why `execFile` instead of `exec`?
- `exec` passes the command through the system shell → vulnerable to shell injection
- `execFile` runs the binary directly → no shell interpretation of special characters
- E.g., a filename like `main; rm -rf /` would be dangerous with `exec` but safe with `execFile`

#### Why separate output directory (`output/`)?
- Keeps `.aux`, `.log`, `.toc`, `.synctex.gz` files out of the source directory
- Makes "clean build" trivial (just delete the `output/` folder)
- Prevents clutter in the file tree (Phase 4)
- The `.gitignore` can ignore the entire `output/` directory

#### Why `-halt-on-error`?
- Without it, `pdflatex` tries to continue past errors, producing cascading nonsense
- With it, we get a clean error at the point of failure
- The user can toggle this in Phase 3 (error handling settings)

### Do's
- ✅ Use `execFile` — not `exec`, not `spawn` (unless streaming is needed later)
- ✅ Always pass `-interaction=nonstopmode` — prevents LaTeX from prompting for input
- ✅ Always pass `-synctex=1` — we'll need it in Phase 3, and it costs nothing
- ✅ Set a reasonable `maxBuffer` (5MB) — LaTeX can produce verbose logs
- ✅ Check if the PDF file actually exists after compilation (even on "success" exit code)
- ✅ Return `duration` for the UI to display

### Don'ts
- ❌ Don't parse the log file here — just return it raw. Parsing is Phase 3.
- ❌ Don't use `spawn` with streaming yet — we don't need real-time log output in Phase 1
- ❌ Don't hardcode `pdflatex` — use the `engine` option so it's easy to add XeLaTeX/LuaLaTeX later
- ❌ Don't catch the timeout error silently — report it clearly as a timeout
- ❌ Don't delete auxiliary files after compilation — they speed up subsequent builds (`latexmk` uses them to skip unnecessary re-runs)

### Definition of Done
- [ ] `compileLaTeX()` function exists in `server/utils/latex.js`
- [ ] Calling it with a valid project produces a PDF in the `output/` subdirectory
- [ ] Returns `{ success: true, pdfPath, log, duration }` on success
- [ ] Returns `{ success: false, error, log, duration }` on failure
- [ ] A `.tex` file with `\loop\iftrue\repeat` times out after 60 seconds
- [ ] The function handles missing `latexmk` gracefully (returns error, doesn't crash)

### How to Test
```javascript
// In a test script or Node REPL:
import { compileLaTeX } from './server/utils/latex.js';
import path from 'path';

const projectDir = path.resolve('projects/sample');
const result = await compileLaTeX(projectDir, 'main.tex');
console.log(result);
// Should print: { success: true, pdfPath: '...output/main.pdf', duration: X.X, ... }
```

---

## Step 2: Create the Compile API Route

### What to Do
Build `server/routes/compile.js` — the Express route that handles `POST /api/compile` requests.

### Sub-Steps

#### 1.3.2 — The compile route

```javascript
// server/routes/compile.js
import express from 'express';
import path from 'path';
import { compileLaTeX } from '../utils/latex.js';

const router = express.Router();
const PROJECTS_DIR = path.resolve(process.cwd(), 'projects');

// Track if a compilation is currently in progress (prevent concurrent compiles)
let isCompiling = false;

/**
 * POST /api/compile
 * Body: { projectPath: "sample", mainFile: "main.tex" }
 */
router.post('/compile', async (req, res) => {
  try {
    const { projectPath, mainFile = 'main.tex' } = req.body;

    // Validate input
    if (!projectPath) {
      return res.status(400).json({ error: 'Missing "projectPath" in body' });
    }

    // Resolve and validate the project directory
    const projectDir = path.resolve(PROJECTS_DIR, projectPath);
    if (!projectDir.startsWith(PROJECTS_DIR)) {
      return res.status(403).json({ error: 'Path traversal not allowed' });
    }

    // Prevent concurrent compilations
    if (isCompiling) {
      return res.status(429).json({ error: 'Compilation already in progress' });
    }

    isCompiling = true;
    console.log(`Compiling: ${projectPath}/${mainFile}`);

    // Run compilation
    const result = await compileLaTeX(projectDir, mainFile);

    isCompiling = false;

    // Build the PDF URL for the frontend
    const pdfName = mainFile.replace(/\.tex$/, '.pdf');
    const pdfUrl = result.success
      ? `/output/${projectPath}/output/${pdfName}`
      : null;

    res.json({
      success: result.success,
      pdfUrl,
      duration: result.duration,
      log: result.log,
      error: result.error,
      timedOut: result.timedOut,
    });

  } catch (err) {
    isCompiling = false;
    console.error('Compilation route error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
```

#### 1.3.3 — Register the route in the server

Add to `server/index.js`:
```javascript
import compileRoutes from './routes/compile.js';
app.use('/api', compileRoutes);
```

### Key Design Decisions
- **Concurrent compilation guard**: Only one compilation can run at a time. If a second request comes in while compiling, return 429 (Too Many Requests). This prevents resource exhaustion and file conflicts.
- **PDF URL construction**: The frontend needs a URL to fetch the PDF. We construct it from the project path and main file name. The `/output/` static middleware (Step 3) serves the actual file.

### Do's
- ✅ Validate `projectPath` for path traversal
- ✅ Log compilation start for debugging
- ✅ Return structured JSON with `success`, `pdfUrl`, `duration`, `log`, `error`
- ✅ Guard against concurrent compilations

### Don'ts
- ❌ Don't allow engine selection in the request body yet — hardcode `pdflatex`
- ❌ Don't stream the compilation output — just return the complete result
- ❌ Don't delete output files — they're needed for incremental builds

### Definition of Done
- [ ] `POST /api/compile` exists and responds
- [ ] Returns `success: true` with `pdfUrl` for valid LaTeX
- [ ] Returns `success: false` with `error` for invalid LaTeX
- [ ] Returns 429 if a compilation is already running
- [ ] Returns 400 if `projectPath` is missing
- [ ] Returns 403 for path traversal attempts

### How to Test
```bash
# Successful compilation
curl -X POST http://localhost:3001/api/compile \
  -H "Content-Type: application/json" \
  -d '{"projectPath":"sample","mainFile":"main.tex"}'
# Expected: { "success": true, "pdfUrl": "/output/sample/output/main.pdf", "duration": X.X, ... }

# Missing parameter
curl -X POST http://localhost:3001/api/compile \
  -H "Content-Type: application/json" \
  -d '{}'
# Expected: { "error": "Missing \"projectPath\" in body" }

# Path traversal
curl -X POST http://localhost:3001/api/compile \
  -H "Content-Type: application/json" \
  -d '{"projectPath":"../../etc"}'
# Expected: 403
```

---

## Step 3: Configure PDF Serving

### What to Do
Set up Express static middleware to serve the output PDFs so the frontend can load them into the PDF viewer.

### Sub-Steps

#### 1.3.4 — Update the static middleware in `server/index.js`

```javascript
// Serve project output files (PDFs, logs, etc.)
// URL: /output/<projectName>/output/<filename>
app.use('/output', express.static(
  path.join(__dirname, '..', 'projects'),
  {
    setHeaders: (res, filePath) => {
      // No cache for PDFs — always serve the latest
      if (filePath.endsWith('.pdf')) {
        res.set('Cache-Control', 'no-cache, no-store, must-revalidate');
        res.set('Pragma', 'no-cache');
        res.set('Expires', '0');
      }
    },
  }
));
```

### Key Points
- **Cache-busting**: PDFs must NOT be cached by the browser. Every compile should show the latest version. We set aggressive no-cache headers.
- **URL mapping**: `/output/sample/output/main.pdf` maps to `projects/sample/output/main.pdf` on disk.
- **Security**: Only files inside the `projects/` directory are served. The static middleware won't serve parent directories.

### Definition of Done
- [ ] `GET /output/sample/output/main.pdf` returns the compiled PDF (after compilation)
- [ ] The response has `Cache-Control: no-cache` headers
- [ ] Requesting a non-existent file returns 404

### How to Test
1. Run a compilation first (Step 2 test)
2. Then: `curl -I http://localhost:3001/output/sample/output/main.pdf`
3. Should return HTTP 200 with `Content-Type: application/pdf` and `Cache-Control: no-cache`

---

## Step 4: Add a "Clean Build" Endpoint

### What to Do
Create an endpoint that deletes all output files and forces a fresh compilation. This is useful when auxiliary files are corrupted.

### Sub-Steps

#### 1.3.5 — Clean endpoint

Add to `server/routes/compile.js`:
```javascript
import fs from 'fs/promises';

/**
 * POST /api/compile/clean
 * Body: { projectPath: "sample" }
 * Deletes the output directory for a fresh build.
 */
router.post('/compile/clean', async (req, res) => {
  try {
    const { projectPath } = req.body;
    if (!projectPath) {
      return res.status(400).json({ error: 'Missing "projectPath"' });
    }

    const projectDir = path.resolve(PROJECTS_DIR, projectPath);
    if (!projectDir.startsWith(PROJECTS_DIR)) {
      return res.status(403).json({ error: 'Path traversal not allowed' });
    }

    const outputDir = path.join(projectDir, 'output');

    // Delete the output directory
    await fs.rm(outputDir, { recursive: true, force: true });
    console.log(`Cleaned output for: ${projectPath}`);

    res.json({ success: true, message: 'Output directory cleaned' });
  } catch (err) {
    console.error('Clean error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

### Why This Matters
- Sometimes `latexmk` gets confused by stale `.aux` or `.toc` files
- "Delete all and recompile" is a common troubleshooting step in LaTeX
- Overleaf has this as "Recompile from scratch"

### Definition of Done
- [ ] `POST /api/compile/clean` deletes the `output/` directory
- [ ] After cleaning, a fresh compile produces the PDF again
- [ ] Path traversal is blocked

### How to Test
```bash
# Clean
curl -X POST http://localhost:3001/api/compile/clean \
  -H "Content-Type: application/json" \
  -d '{"projectPath":"sample"}'
# Expected: { "success": true }

# Verify output dir is gone
ls projects/sample/output/
# Should fail (directory doesn't exist)

# Recompile — should recreate the output dir and PDF
curl -X POST http://localhost:3001/api/compile \
  -H "Content-Type: application/json" \
  -d '{"projectPath":"sample","mainFile":"main.tex"}'
```

---

## Step 5: Windows Compatibility Notes

### Why This Matters
Since you're on Windows, there are a few gotchas to handle:

### 5.1 — PATH and `latexmk`
- TeX Live on Windows installs to something like `C:\texlive\2024\bin\windows\`
- MiKTeX installs to `C:\Users\<user>\AppData\Local\Programs\MiKTeX\miktex\bin\x64\`
- Make sure this directory is on your system PATH
- Test with: `latexmk --version` in PowerShell

### 5.2 — `latexmk` on Windows
- `latexmk` is a Perl script. TeX Live includes its own Perl, so it should work.
- MiKTeX may not include `latexmk` by default. Install it via MiKTeX Console or use `pdflatex` directly as a fallback.
- **Fallback**: If `latexmk` is not available, the compilation helper should detect this and fall back to running `pdflatex` directly (with manual multi-pass logic).

### 5.3 — Path separators
- Windows uses `\` but Node.js `path` module handles this correctly
- The `execFile` call with `cwd` should work with Windows paths
- The `-outdir` argument to `latexmk` should work with both `/` and `\`

### 5.4 — `execFile` on Windows
- On Windows, `execFile('latexmk', ...)` may need the full path or `.exe`/`.bat` extension
- `latexmk` is actually `latexmk.exe` (TeX Live) or `latexmk.bat` (some setups)
- If `execFile` fails, try: `execFile('latexmk.exe', ...)` or `exec('latexmk ...', { shell: true })`
- **Workaround**: Use `{ shell: true }` option in `execFile` if direct execution fails on Windows

### 5.5 — Add to compilation helper
```javascript
// In compileLaTeX(), add Windows compatibility:
const isWindows = process.platform === 'win32';
const latexmkCmd = isWindows ? 'latexmk.exe' : 'latexmk';

// Use shell on Windows if needed:
const execOptions = {
  cwd: projectDir,
  timeout,
  maxBuffer: 1024 * 1024 * 5,
  env: { ...process.env },
  ...(isWindows && { shell: true }), // Use shell on Windows
};
```

### Definition of Done
- [ ] `latexmk --version` runs successfully on the developer's machine
- [ ] The compilation helper works on Windows (tested, not just assumed)
- [ ] Path separators are handled correctly

---

## Final Acceptance Checklist — Feature 1.3 Complete

| # | Check | Status |
|---|-------|--------|
| 1 | `server/utils/latex.js` exists with `compileLaTeX()` | ☐ |
| 2 | `server/routes/compile.js` exists with POST endpoint | ☐ |
| 3 | `POST /api/compile` with valid project returns `{ success: true, pdfUrl }` | ☐ |
| 4 | Output PDF exists at `projects/sample/output/main.pdf` after compile | ☐ |
| 5 | `GET /output/sample/output/main.pdf` serves the PDF | ☐ |
| 6 | PDF response has `Cache-Control: no-cache` header | ☐ |
| 7 | Invalid LaTeX returns `{ success: false }` with error info | ☐ |
| 8 | Concurrent compilation returns 429 | ☐ |
| 9 | Path traversal returns 403 | ☐ |
| 10 | Compilation timeout works (kills after 60s) | ☐ |
| 11 | `POST /api/compile/clean` deletes the output directory | ☐ |
| 12 | After clean + recompile, PDF is produced again | ☐ |
| 13 | Works on Windows with TeX Live or MiKTeX | ☐ |
| 14 | No unhandled exceptions or crashes | ☐ |

> **When all 14 checks pass, Feature 1.3 is DONE. Proceed to Feature 1.4 (Manual Compile Button).**
