# Features 2.3, 2.5, 2.6 — Built-in CodeMirror Features

> **Phase**: 2 | **Features**: 3, 5, 6
> **Goal**: Verify and configure three features that are already built into CodeMirror 6.
> **Estimated Effort**: 1 hour total
> **Dependencies**: Feature 1.2 (editor module).

These three features require minimal or zero custom code. They are grouped together because they are primarily "verify it works + add CSS" tasks.

---

## Feature 2.3 — Bracket Matching / Highlighting

### Status: Already included in Phase 1
`bracketMatching()` was added to the editor extensions in Feature 1.2.

### What to Verify
1. Cursor on `{` → matching `}` highlights
2. Cursor on `)` → matching `(` highlights
3. Unmatched bracket → red/error highlight

### CSS to Add
```css
.cm-matchingBracket {
  background-color: rgba(124, 111, 247, 0.3);
  border-bottom: 2px solid var(--accent-primary);
}
.cm-nonmatchingBracket {
  background-color: rgba(248, 113, 113, 0.3);
  border-bottom: 2px solid var(--accent-error);
}
```

### Checklist
| # | Check | Status |
|---|-------|--------|
| 1 | Matching brackets highlight with purple tint | ☐ |
| 2 | Unmatched brackets highlight with red tint | ☐ |
| 3 | Works for `{}`, `()`, `[]` | ☐ |

---

## Feature 2.5 — Comment / Uncomment Toggle

### What to Do
Configure `Ctrl+/` to toggle `%` line comments.

### Implementation
```javascript
import { toggleComment } from '@codemirror/commands';

// In the keymap array:
keymap.of([
  { key: 'Ctrl-/', run: toggleComment },
]),
```

If the LaTeX language mode doesn't auto-detect `%` as the comment character, configure it manually:
```javascript
// After the language is defined, ensure commentTokens is set:
// The stex StreamLanguage may already handle this.
// Test first — if Ctrl+/ doesn't add %, then add a custom commentTokens config.
```

**Fallback** — if `toggleComment` doesn't detect `%`, create a manual handler:
```javascript
function toggleLatexComment(view) {
  const { state } = view;
  const changes = [];
  for (const range of state.selection.ranges) {
    const fromLine = state.doc.lineAt(range.from);
    const toLine = state.doc.lineAt(range.to);
    for (let i = fromLine.number; i <= toLine.number; i++) {
      const line = state.doc.line(i);
      if (line.text.startsWith('% ')) {
        changes.push({ from: line.from, to: line.from + 2, insert: '' });
      } else if (line.text.startsWith('%')) {
        changes.push({ from: line.from, to: line.from + 1, insert: '' });
      } else {
        changes.push({ from: line.from, insert: '% ' });
      }
    }
  }
  view.dispatch({ changes });
  return true;
}
```

### Checklist
| # | Check | Status |
|---|-------|--------|
| 1 | `Ctrl+/` on a line adds `% ` prefix | ☐ |
| 2 | `Ctrl+/` on a commented line removes `% ` | ☐ |
| 3 | Multi-line selection + `Ctrl+/` comments all lines | ☐ |
| 4 | `Ctrl+/` again on the same selection uncomments all | ☐ |

---

## Feature 2.6 — Multiple Cursors / Multi-Select

### Status: Already built into CodeMirror 6
These are part of the default keybindings and `drawSelection()` / `rectangularSelection()` extensions from Feature 1.2.

### What to Verify
| Shortcut | Action |
|----------|--------|
| `Ctrl+D` | Select next occurrence of current word/selection |
| `Alt+Click` | Place additional cursor |
| `Ctrl+Alt+↑` | Add cursor on line above |
| `Ctrl+Alt+↓` | Add cursor on line below |
| `Ctrl+Shift+L` | Select all occurrences |

### Checklist
| # | Check | Status |
|---|-------|--------|
| 1 | `Ctrl+D` selects next occurrence | ☐ |
| 2 | Repeated `Ctrl+D` selects additional occurrences | ☐ |
| 3 | `Alt+Click` places a second cursor | ☐ |
| 4 | Typing with multi-cursors edits all positions | ☐ |
| 5 | `Escape` reduces to single cursor | ☐ |

---

> **All three features verified → Proceed to Feature 2.4.**
