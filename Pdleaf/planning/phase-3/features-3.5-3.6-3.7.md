# Features 3.5, 3.6, 3.7 — Error Log Panel, Clickable Errors, & Badge

> **Phase**: 3 | **Features**: 5, 6, 7 (tightly coupled — built together)
> **Goal**: Parse the LaTeX `.log` file, display errors/warnings in a structured panel, make each entry clickable (jumps to source line), and show error/warning counts as a badge.
> **Estimated Effort**: 5–8 hours total
> **Dependencies**: Feature 1.3 (compile response includes `log` text), Feature 1.2 (editor `getEditorView()` for line navigation).

---

## Overview

This is the biggest chunk of Phase 3. Three sub-features are built together because they share the same data pipeline:

```
Compile response → logParser.js → structured entries → logPanel.js → UI
                                       ↓                      ↓
                                  badge counts          click → editor.goToLine()
```

### New Files
| File | Purpose |
|------|---------|
| `src/js/logParser.js` | Parse raw LaTeX log text into structured entries |
| `src/js/logPanel.js` | Render the log panel UI, handle clicks, update badge |

---

## Step 1: Create the LaTeX Log Parser

### What to Do
Build `src/js/logParser.js` — a module that takes raw `.log` file text and extracts structured error/warning/info entries.

### LaTeX Log Format

LaTeX logs have three types of messages we care about:

#### Errors
```
! Undefined control sequence.
l.42 \undefcommand
```
Pattern: Line starting with `! ` followed by the error message. The next line(s) contain `l.<number>` (the line number).

#### Warnings
```
LaTeX Warning: Reference `fig:missing' on page 3 undefined on input line 58.
```
Pattern: `LaTeX Warning:` or `Package <name> Warning:` followed by the message. Line number is in the text: `on input line <N>`.

#### Overfull/Underfull boxes (badboxes)
```
Overfull \hbox (3.45pt too wide) in paragraph at lines 23--25
Underfull \vbox (badness 10000) has occurred while \output is active
```
Pattern: `Overfull` or `Underfull` followed by `\hbox` or `\vbox`. Line number may be in `at lines <N>--<M>`.

### Parser Implementation

```javascript
// src/js/logParser.js

/**
 * @typedef {Object} LogEntry
 * @property {'error'|'warning'|'badbox'} type
 * @property {string} message - The human-readable message
 * @property {number|null} line - Source line number (null if unknown)
 * @property {string} raw - The raw log text for this entry
 */

/**
 * Parse a LaTeX log string into structured entries.
 * @param {string} logText - Raw log file content
 * @returns {LogEntry[]}
 */
export function parseLatexLog(logText) {
  const entries = [];
  const lines = logText.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // 1. Errors: lines starting with "! "
    if (line.startsWith('! ')) {
      const message = line.substring(2).trim();
      let sourceLine = null;
      let raw = line;

      // Look ahead for "l.<number>" on the next few lines
      for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
        raw += '\n' + lines[j];
        const lineMatch = lines[j].match(/^l\.(\d+)\s/);
        if (lineMatch) {
          sourceLine = parseInt(lineMatch[1], 10);
          break;
        }
      }

      entries.push({ type: 'error', message, line: sourceLine, raw });
      continue;
    }

    // 2. Warnings: "LaTeX Warning:" or "Package <name> Warning:"
    if (line.includes('Warning:')) {
      const warningMatch = line.match(/(LaTeX Warning|Package \w+ Warning):\s*(.*)/);
      if (warningMatch) {
        let message = warningMatch[2].trim();
        let raw = line;

        // Warning may span multiple lines — continue until empty line or next message
        let j = i + 1;
        while (j < lines.length && lines[j].trim() !== '' && !lines[j].startsWith('!') && !lines[j].includes('Warning:')) {
          message += ' ' + lines[j].trim();
          raw += '\n' + lines[j];
          j++;
        }

        // Extract line number from message text
        let sourceLine = null;
        const lineInText = message.match(/on input line (\d+)/);
        if (lineInText) {
          sourceLine = parseInt(lineInText[1], 10);
        }

        entries.push({ type: 'warning', message, line: sourceLine, raw });
        continue;
      }
    }

    // 3. Badboxes: "Overfull" or "Underfull"
    if (line.startsWith('Overfull') || line.startsWith('Underfull')) {
      const message = line.trim();
      let sourceLine = null;

      const lineMatch = line.match(/at lines? (\d+)/);
      if (lineMatch) {
        sourceLine = parseInt(lineMatch[1], 10);
      }

      entries.push({ type: 'badbox', message, line: sourceLine, raw: line });
    }
  }

  return entries;
}

/**
 * Count entries by type.
 * @param {LogEntry[]} entries
 * @returns {{ errors: number, warnings: number, badboxes: number }}
 */
export function countEntries(entries) {
  return {
    errors: entries.filter(e => e.type === 'error').length,
    warnings: entries.filter(e => e.type === 'warning').length,
    badboxes: entries.filter(e => e.type === 'badbox').length,
  };
}
```

### Key Design Decisions

#### Why regex-based parsing?
- LaTeX logs don't have a structured format (no JSON, no XML)
- Regex is the standard approach — Overleaf, TeXstudio, and VS Code LaTeX Workshop all use it
- The patterns are well-established and stable across TeX distributions

#### Why look-ahead for error line numbers?
- LaTeX errors print the error on one line (`! Undefined control sequence.`) and the line number on the next (`l.42 \undefcommand`). We need to scan ahead 1-5 lines to find it.

#### Why include `raw`?
- The parsed `message` is a clean summary for display
- The `raw` text preserves the full log context for a "details" view or tooltip

### Definition of Done — Parser
- [ ] `parseLatexLog()` extracts errors, warnings, and badboxes
- [ ] Each entry has `type`, `message`, `line` (nullable), `raw`
- [ ] `countEntries()` returns correct counts
- [ ] Works with real LaTeX log output (test with actual compilation logs)

---
