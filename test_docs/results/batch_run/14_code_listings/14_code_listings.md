---
date: "D:20260413043827+05'00'"
source: "14_code_listings.pdf"
pages: 2
---

## Code Listings Test

### Developer

### April 13, 2026

## 1 Python Example

```python
def fibonacci(n):
’’’Calculate the nth Fibonacci number.’’’
if n <= 1:
return n
a, b = 0, 1
for _ in range (2, n + 1):
a, b = b, a + b
return b

# Print first 10 Fibonacci numbers
for i in range (10):
print(f"F({i})␣=␣{fibonacci(i)}")

```

## 2 JavaScript Example

```javascript
1 async function fetchData(url) {
2 try {
const response = await fetch(url);
const data = await response.json ();
return data;
6 } catch (error) {
console.error(’Fetch failed:’, error);
throw error;

```

[^9]: }

[^10]: }

## 3 Inline Code

#### Use the `pip install pd2md` command to install the package. Then run `pd2md convert`
`input.pdf` to convert a file. The output will be saved to the `output/` directory by default.


## 4 Shell Commands

```

# Clone the repository
git clone https :// github.com/user/pd2md.git
cd pd2md

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest backend/tests/ -v

```


---

[^9]: }
[^10]: }
