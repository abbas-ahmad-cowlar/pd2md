---
date: "D:20260413043932+05'00'"
source: "19_headings.pdf"
pages: 2
---

## Multi-Level Heading Structure

#### Structure Tester

#### April 13, 2026

### 1 Level 1: Architecture

This section tests heading level detection across multiple depths.

#### 1.1 Level 2: Frontend
The frontend uses vanilla HTML, CSS, and JavaScript.

1.1.1 Level 3: HTML Structure

The HTML file contains the drag-and-drop upload zone, progress display, result view, and
error handling sections.

1.1.2 Level 3: CSS Design System

CSS variables define the color palette, typography, spacing, and animations. The design uses
a dark theme with glassmorphism effects.

#### 1.2 Level 2: Backend
The backend is built with FastAPI and Python.

1.2.1 Level 3: API Routes

Five routes handle the conversion lifecycle: upload, status, download Markdown, download
ZIP, and content preview.

1.2.2 Level 3: Pipeline

The conversion pipeline consists of six modular layers.

### 2 Level 1: Testing

Comprehensive tests verify each layer independently and the full pipeline end-to-end.


#### 2.1 Level 2: Unit Tests
Each pipeline module has dedicated unit tests with synthetic PDF fixtures.

#### 2.2 Level 2: Integration Tests
End-to-end tests verify that real PDFs convert correctly with all content preserved.

### 3 Level 1: Deployment

Deployment instructions for both development and production environments.
