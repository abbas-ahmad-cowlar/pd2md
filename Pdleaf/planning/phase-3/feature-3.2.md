# Feature 3.2 — Draft / Fast Compile Mode

> **Phase**: 3 | **Feature**: 2 of 13
> **Goal**: Add a "Draft" toggle that skips image rendering and hyperlink generation during compilation for significantly faster builds. Critical for auto-compile responsiveness.
> **Estimated Effort**: 1–2 hours
> **Dependencies**: Feature 1.3 (compilation backend), Feature 1.4 (compiler module).

---

## Overview

Two changes:
1. **Backend**: Modify `compileLaTeX()` to accept a `draft` option and inject draft flags
2. **Frontend**: Add a toggle button and pass the draft flag when compiling

---

## Step 1: Backend — Add Draft Flag Support

### What to Do
Modify `server/utils/latex.js` to support draft mode.

```javascript
// In compileLaTeX(), add to options:
const { engine = 'pdflatex', timeout = 60000, draft = false } = options;

// Modify the args array:
const args = [
  `-${engine === 'pdflatex' ? 'pdf' : engine === 'xelatex' ? 'pdfxe' : 'pdflua'}`,
  '-interaction=nonstopmode',
  '-synctex=1',
  '-halt-on-error',
  `-outdir=${outputDir}`,
];

// Add draft flags if enabled
if (draft) {
  // latexmk doesn't have a native "draft" flag, so we pass it to pdflatex:
  args.push(`-pdflatex=${engine} -interaction=nonstopmode -draftmode`);
  // NOTE: -draftmode tells pdflatex to skip PDF generation entirely (only .dvi/.xdv)
  // That's too aggressive — we still want a PDF, just without images.
  //
  // Better approach: Use latexmk's -e flag to inject options:
  // args.push('-e', '$pdflatex=q/pdflatex %O -interaction=nonstopmode/');
  //
  // Actually best approach: Prepend \PassOptionsToPackage{draft}{graphicx} to the .tex file
  // This tells graphicx to show bounding boxes instead of rendering images.
}

// Push mainFile last
args.push(mainFile);
```

### Best Approach for Draft Mode

Instead of modifying latexmk flags, **prepend draft commands to the .tex file**:

```javascript
if (draft) {
  // Create a temporary wrapper file that loads draft mode
  const wrapperContent = `\\PassOptionsToPackage{draft}{graphicx}
\\PassOptionsToPackage{draft}{hyperref}
\\input{${mainFile}}`;

  const wrapperPath = path.join(projectDir, '_draft_wrapper.tex');
  await fs.writeFile(wrapperPath, wrapperContent, 'utf-8');
  args.push('_draft_wrapper.tex'); // compile wrapper instead of mainFile
} else {
  args.push(mainFile);
}
```

### Why this approach?
- `\PassOptionsToPackage{draft}{graphicx}` → images show as bounding boxes (fast)
- `\PassOptionsToPackage{draft}{hyperref}` → hyperlinks are skipped (fast)
- The wrapper `\input{main.tex}` includes the real file unchanged
- No modification to the user's `.tex` files
- The wrapper file is named `_draft_wrapper.tex` (prefixed with `_` to be obviously temporary)

### Cleanup
After compilation, delete the wrapper file:
```javascript
if (draft) {
  try {
    await fs.unlink(path.join(projectDir, '_draft_wrapper.tex'));
  } catch { /* ignore cleanup errors */ }
}
```

---

## Step 2: Backend — Accept Draft Flag in API

Modify `server/routes/compile.js`:
```javascript
router.post('/compile', async (req, res) => {
  const { projectPath, mainFile = 'main.tex', draft = false } = req.body;
  // ... existing validation ...
  const result = await compileLaTeX(projectDir, mainFile, { draft });
  // ... existing response ...
});
```

---

## Step 3: Frontend — Draft Toggle Button

### HTML
```html
<button id="btn-draft" class="btn btn-toolbar" title="Draft mode: OFF (faster compilation)">
  <span class="btn-icon">⚡</span>
  <span class="btn-text">Draft</span>
</button>
```

### JavaScript
In `src/js/compiler.js`:
```javascript
let draftMode = false;

export function toggleDraftMode() {
  draftMode = !draftMode;
  const btn = document.getElementById('btn-draft');
  if (draftMode) {
    btn.classList.add('btn-active');
    btn.title = 'Draft mode: ON (images skipped for speed)';
  } else {
    btn.classList.remove('btn-active');
    btn.title = 'Draft mode: OFF';
  }
  console.log(`Draft mode: ${draftMode ? 'ON' : 'OFF'}`);
  return draftMode;
}

// In runCompile(), update the fetch body:
body: JSON.stringify({
  projectPath: PROJECT_PATH,
  mainFile: MAIN_FILE,
  draft: draftMode,  // ← pass the flag
}),
```

### Wiring in `app.js`
```javascript
import { toggleDraftMode } from './compiler.js';
document.getElementById('btn-draft').addEventListener('click', toggleDraftMode);
```

---

## Edge Cases

### 4.1 — Draft mode + images
Images show as empty bounding boxes with filenames. This is standard LaTeX `draft` behavior — not a bug.

### 4.2 — Draft mode + hyperref
Hyperlinks are not generated. TOC links, URL links, and cross-reference links are all plain text.

### 4.3 — Draft mode + SyncTeX
SyncTeX data is still generated in draft mode. Forward/inverse sync should still work.

### 4.4 — User forgets draft is ON
The purple "⚡ Draft" button is a persistent visual reminder. When the user does a final build, they should toggle it OFF. Consider adding a warning in the compile status: "Draft mode — images omitted".

### 4.5 — Wrapper file and git
`_draft_wrapper.tex` should be in `.gitignore`. It's deleted after compilation anyway, but add it for safety.

---

## Do's & Don'ts

### Do's
- ✅ Use `\PassOptionsToPackage` — doesn't modify user files
- ✅ Delete the wrapper file after compilation
- ✅ Show clear visual indicator when draft mode is active
- ✅ Add `_draft_wrapper.tex` to `.gitignore`

### Don'ts
- ❌ Don't modify the user's `.tex` file directly
- ❌ Don't use `-draftmode` flag (skips PDF generation entirely — too aggressive)
- ❌ Don't persist draft state across sessions (yet — Phase 6)

---

## Final Checklist

| # | Check | Status |
|---|-------|--------|
| 1 | Draft toggle button exists in toolbar | ☐ |
| 2 | Default state: OFF | ☐ |
| 3 | Toggle ON → button turns purple with ⚡ | ☐ |
| 4 | Compile in draft mode → images show as bounding boxes in PDF | ☐ |
| 5 | Compile in draft mode → noticeably faster than normal | ☐ |
| 6 | Toggle OFF → next compile renders images normally | ☐ |
| 7 | `_draft_wrapper.tex` is deleted after compilation | ☐ |
| 8 | `_draft_wrapper.tex` is in `.gitignore` | ☐ |
| 9 | SyncTeX still works in draft mode | ☐ |
| 10 | No modification to user's `.tex` files | ☐ |

> **Done → Proceed to Features 3.5–3.7 (Error Log Panel).**
