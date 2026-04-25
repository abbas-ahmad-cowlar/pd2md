---
date: "D:20260425223543+05'00'"
source: "code_listing.pdf"
pages: 1
---

## Code Block Test Fixture

#### PD2MD Test Suite

#### 2026

### 1 Python Function

```python
def greet(name):
""" Say hello."""
return f"Hello ,␣{name }!"
result = greet("World")
print(result)

```

### 2 Shell Script

```

#!/bin/bash
echo "Installing␣PD2MD"
pip install pd2md
pd2md convert input.pdf

```

### 3 Plain Text

This paragraph is regular body text. It should NOT be detected as a code
block. The converter must distinguish between monospace code listings and
normal text paragraphs.

1
