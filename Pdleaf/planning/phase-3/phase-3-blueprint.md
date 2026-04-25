# Phase 3 Blueprint — Compilation & Preview Polish

> **Phase**: 3 of 7
> **Goal**: Make the compile → preview cycle fast, smart, and seamless. This phase adds auto-compile, error handling, SyncTeX bidirectional navigation, zoom controls, and several quality-of-life improvements.
> **Estimated Effort**: 2–3 weeks
> **Prerequisite**: Phases 1 and 2 are complete. The editor loads files, compiles LaTeX, displays PDFs, and has professional editing features.

---

## What Phase 3 Delivers

When Phase 3 is complete, the user should experience:
1. **Auto-compile**: Document recompiles automatically after a pause in typing
2. **Fast compile**: Draft mode for quick iterations (skip images/hyperlinks)
3. **Error visibility**: Structured error/warning panel with clickable line navigation
4. **Error badges**: At-a-glance error/warning counts on the Logs button
5. **SyncTeX forward**: Click in editor → PDF scrolls to that location
6. **SyncTeX inverse**: Double-click PDF → editor jumps to that source line
7. **Zoom controls**: Ctrl+Scroll, preset buttons, fit-width/fit-page
8. **Detach PDF**: Open preview in a separate browser tab
9. **Clean recompile**: One-click clear auxiliary files and rebuild
10. **Compilation timing**: "Compiled in 3.2s" display

**Key Insight**: This phase spans both frontend and backend. Features 3.1–3.4 modify compilation behavior (backend changes to `latex.js` and `compile.js`). Features 3.5–3.7 add a new UI panel. Features 3.8–3.9 require SyncTeX parsing (a significant new module). Features 3.10–3.13 are UI/UX polish.

---

## Architecture Changes

### New Files
| File | Purpose |
|------|---------|
| `src/js/autoCompile.js` | **[NEW]** Debounced auto-compile logic |
| `src/js/logPanel.js` | **[NEW]** Error/warning log panel controller |
| `src/js/logParser.js` | **[NEW]** LaTeX log file parser |
| `src/js/syncTeX.js` | **[NEW]** SyncTeX file parser + forward/inverse sync |
| `src/js/zoomControls.js` | **[NEW]** PDF zoom controller |
| `server/utils/synctex.js` | **[NEW]** Backend SyncTeX query endpoint |

### Modified Files
| File | What Changes |
|------|-------------|
| `server/utils/latex.js` | Add draft mode flags, engine options |
| `server/routes/compile.js` | Accept `draft`, `engine` params; return log content |
| `src/js/compiler.js` | Dispatch more detailed compile events |
| `src/js/pdfViewer.js` | Add zoom support, scroll-to-position, click handlers |
| `src/js/editor.js` | Add onChange listener hook, cursor position events |
| `src/index.html` | Add log panel, zoom toolbar, detach button |
| `src/css/style.css` | Log panel styles, zoom toolbar, badges |

### HTML Layout Change
Phase 3 introduces a **log panel** below the editor. The layout becomes:

```
┌─────────────────────────────────────────────────────────┐
│ Toolbar: [Compile] [Draft ⚡] [Logs 2✗ 3⚠]  │ zoom │  │
├──────────────────────┬──┬───────────────────────────────┤
│                      │  │                               │
│   Editor Panel       │▐▐│    PDF Preview Panel          │
│   (CodeMirror)       │▐▐│    (pdf.js canvases)          │
│                      │  │                               │
├──────────────────────┤  │                               │
│ Log Panel (collapsible)  │                               │
│ ✗ Error: l.42 Undef... │                               │
│ ⚠ Warn: Overfull hbox  │                               │
└──────────────────────┴──┴───────────────────────────────┘
```

The log panel sits below the editor (left side only) and can be collapsed.

---

## Feature Summary Table

| # | Feature | Effort | Frontend | Backend | New Module? |
|---|---------|--------|----------|---------|-------------|
| 3.1 | Auto-Compile with Debounce | 2–3 hrs | ✅ | — | `autoCompile.js` |
| 3.2 | Draft / Fast Compile Mode | 1–2 hrs | Toggle button | Flag passing | — |
| 3.3 | Stop on First Error | 15 min | — | Config flag | — |
| 3.4 | Multiple Compile Passes | 0 min | — | Already done | — |
| 3.5 | Error Log Panel | 4–6 hrs | New panel | Log content | `logPanel.js`, `logParser.js` |
| 3.6 | Clickable Error → Line Nav | 1–2 hrs | Click handlers | — | — (extends 3.5) |
| 3.7 | Error Count Badge | 30 min | Badge update | — | — (extends 3.5) |
| 3.8 | SyncTeX Forward Sync | 4–6 hrs | Scroll PDF | SyncTeX parse | `syncTeX.js` |
| 3.9 | SyncTeX Inverse Sync | 2–3 hrs | Click handler | SyncTeX query | — (extends 3.8) |
| 3.10 | PDF Zoom Controls | 3–4 hrs | Zoom UI | — | `zoomControls.js` |
| 3.11 | Detach PDF to Tab | 1 hr | `window.open()` | — | — |
| 3.12 | Recompile from Scratch | 30 min | Button | Already done | — |
| 3.13 | Compilation Time Display | 15 min | UI update | Already done | — |

**Total estimated effort**: 20–30 hours

---

## Implementation Order

```
Group A — Quick Wins (already mostly done)
  3.3 → 3.4 → 3.13 → 3.12

Group B — Auto-Compile & Draft Mode
  3.2 → 3.1

Group C — Error Handling (tightly coupled)
  3.5 → 3.6 → 3.7

Group D — SyncTeX (tightly coupled)
  3.8 → 3.9

Group E — Preview Polish
  3.10 → 3.11
```

**Rationale**:
- Start with the zero-effort wins (3.3, 3.4, 3.13 are already implemented in Phase 1's `latex.js`)
- Draft mode (3.2) before auto-compile (3.1) because auto-compile benefits from fast builds
- Error handling is one cohesive unit — build the parser, then the panel, then clickable navigation, then badge
- SyncTeX forward (3.8) before inverse (3.9) — forward is simpler and validates the SyncTeX parser
- Zoom and detach are independent polish features

---

## Features 3.3, 3.4, 3.12, 3.13 — Already Done / Trivial

These features are effectively complete from Phase 1 or require near-zero work:

### 3.3 — Stop on First Error
**Status**: Already done. Phase 1's `compileLaTeX()` passes `-halt-on-error` to `latexmk`.
**Remaining**: Nothing. Verify the flag is present. If you want to make it toggleable, add an `options.haltOnError` parameter (default: `true`).

### 3.4 — Multiple Compile Passes
**Status**: Already done. Phase 1 uses `latexmk` which handles multi-pass automatically.
**Remaining**: Nothing. `latexmk` detects when re-runs are needed for `\ref`, `\cite`, TOC, etc.

### 3.12 — Recompile from Scratch
**Status**: Already done. Phase 1's `POST /api/compile/clean` endpoint deletes the output directory.
**Remaining**: Add a UI button for it. Add a "Recompile from Scratch" option in the toolbar or a dropdown menu next to the compile button.

### 3.13 — Compilation Time Display
**Status**: Already done. Phase 1's compile response includes `duration` in seconds. Phase 1's compile button shows "Compiled in X.Xs" in the success state.
**Remaining**: Nothing. Already displayed in the toolbar status area.

### Combined Checklist for 3.3, 3.4, 3.12, 3.13

| # | Check | Status |
|---|-------|--------|
| 1 | `-halt-on-error` flag is passed to `latexmk` | ☐ |
| 2 | `latexmk` handles cross-references automatically (no manual multi-pass) | ☐ |
| 3 | "Recompile from Scratch" button/menu exists in the toolbar | ☐ |
| 4 | Clicking it calls `POST /api/compile/clean` then `POST /api/compile` | ☐ |
| 5 | "Compiled in X.Xs" shows after successful compilation | ☐ |

---

## Feature 3.1 — Auto-Compile with Debounce (Summary)
**Scope**: Listen for editor changes, wait N seconds after last keystroke, then save + compile. Toggle on/off. Configurable delay.
**Key Points**: Uses CodeMirror `EditorView.updateListener` to detect doc changes. Debounce with `setTimeout`/`clearTimeout`. Respects the `isCompiling` guard from Phase 1. Shows a subtle "Auto-compiling..." status instead of the button animation.
**Depends on**: 3.2 (draft mode makes auto-compile much faster)

## Feature 3.2 — Draft / Fast Compile Mode (Summary)
**Scope**: Add a "Draft" toggle button. When active, compilation skips image rendering and PDF hyperlinks for ~2-3x faster builds.
**Key Points**: Backend passes `\PassOptionsToPackage{draft}{graphicx}` as a preamble injection or uses `-draftmode` latexmk flag. Frontend adds a toggle button with ⚡ icon. State is stored per-session (not persisted yet).

## Features 3.5–3.7 — Error Log Panel (Summary)
**Scope**: Parse the LaTeX `.log` file to extract errors, warnings, and badbox messages. Display them in a collapsible panel below the editor. Each entry is clickable → jumps to the line in the editor. Badge shows counts.
**Key Points**: This is the biggest chunk of Phase 3. The log parser is a new module (`logParser.js`) with regex-based extraction. The panel (`logPanel.js`) is a new DOM component. The badge is a simple counter overlay on the "Logs" toolbar button.

## Features 3.8–3.9 — SyncTeX (Summary)
**Scope**: Bidirectional navigation between editor and PDF. Forward: cursor position → scroll PDF to corresponding location. Inverse: double-click PDF → jump to source line.
**Key Points**: Requires parsing the `.synctex.gz` file (generated by `-synctex=1` flag, already set in Phase 1). Two approaches: (a) parse the gzipped file in the browser, or (b) use a backend endpoint that calls `synctex view` CLI tool. Backend approach is recommended for reliability.

## Feature 3.10 — PDF Zoom Controls (Summary)
**Scope**: Zoom in/out with keyboard shortcuts, Ctrl+Scroll, and preset buttons. Presets: Fit Width, Fit Page, 50%, 75%, 100%, 125%, 150%, 200%.
**Key Points**: The pdf.js `viewport.scale` parameter controls zoom. We already scale to fit width — this feature makes scale configurable. State stored in module. Re-renders all pages at new scale.

## Feature 3.11 — Detach PDF to Separate Tab (Summary)
**Scope**: Button to open the compiled PDF in a new browser tab for multi-monitor setups.
**Key Points**: Simple `window.open(pdfUrl, '_blank')`. The PDF URL is already served by Express static middleware. Add a small "↗" button in the preview toolbar.

---

## Phase 3 Integration Test Plan

> After all features are implemented, run this end-to-end test.

### Full Workflow
1. Open Pdleaf → editor loads `main.tex`
2. Enable auto-compile → type some text → wait 3 seconds → PDF updates automatically
3. Toggle Draft mode ON → auto-compile is faster
4. Introduce a LaTeX error (e.g., `\undefined`) → compile fails
5. Log panel appears/opens → shows the error with line number
6. Click the error → editor scrolls to that line
7. Error badge shows "1 ✗" on the Logs button
8. Fix the error → auto-compile succeeds → badge clears → PDF updates
9. Place cursor on a `\section` line → press Forward Sync shortcut → PDF scrolls to that section
10. Double-click a paragraph in the PDF → editor jumps to the corresponding source
11. Use Ctrl+Scroll to zoom in → PDF pages get larger
12. Click "Fit Width" → pages fit the panel width again
13. Click "Detach" → PDF opens in a new tab
14. Click "Recompile from Scratch" → output cleared and rebuilt
15. Compilation time shows "Compiled in X.Xs"

### Edge Cases
1. Auto-compile while already compiling → should queue, not overlap
2. Draft mode + SyncTeX → SyncTeX should still work in draft mode
3. Error in preamble (no line number) → log panel handles gracefully
4. Zoom + resize panel → zoom level preserved, pages re-render
5. Detach + recompile → detached tab doesn't auto-update (expected — it's a static URL)

---

> **Phase 3 is complete when all integration tests pass without errors.**
>
> Next: Proceed to Phase 4 (File & Project Management).
