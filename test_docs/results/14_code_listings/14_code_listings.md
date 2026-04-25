---
date: "D:20260413043827+05'00'"
source: "14_code_listings.pdf"
pages: 2
---

## Code Listings Test

### Developer

### April 13, 2026

### 1 Python Example

1 def fibonacci(n):
2 ’’’Calculate the nth Fibonacci number.’’’
3 if n <= 1:
4 return n
5 a, b = 0, 1
6 for _ in range (2, n + 1):
7 a, b = b, a + b
8 return b

9

10 # Print first 10 Fibonacci numbers
11 for i in range (10):
12 print(f"F({i})␣=␣{fibonacci(i)}")

### 2 JavaScript Example

1 async function fetchData(url) {
2 try {
3 const response = await fetch(url);
4 const data = await response.json ();
5 return data;
6 } catch (error) {
7 console.error(’Fetch failed:’, error);
8 throw error;
9 }

[^10]: }

### 3 Inline Code

Use the pip install pd2md command to install the package. Then run pd2md convert
input.pdf to convert a file. The output will be saved to the output/ directory by default.


### 4 Shell Commands

1 # Clone the repository
2 git clone https :// github.com/user/pd2md.git
3 cd pd2md

4

5 # Install dependencies
6 python -m venv .venv
7 source .venv/bin/activate
8 pip install -e ".[dev]"

9

10 # Run tests
11 pytest backend/tests/ -v


---

[^10]: }
