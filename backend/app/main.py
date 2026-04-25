"""
PD2MD — FastAPI Application Entry Point.

Serves the conversion API and the static frontend.
"""

from __future__ import annotations

import asyncio
import logging
import traceback
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.pipeline.orchestrator import PipelineOrchestrator
from backend.app.pipeline.emitter import create_output_zip

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App & State
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent PDF to Markdown converter",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job state (no database needed for single-user tool)
jobs: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file and start conversion.

    Returns a job_id for tracking progress and retrieving results.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum: {settings.max_file_size_mb} MB.",
        )

    # Save uploaded file
    job_id = uuid4().hex
    job_dir = settings.upload_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = job_dir / file.filename
    pdf_path.write_bytes(content)

    output_dir = settings.output_dir / job_id

    # Initialize job state
    jobs[job_id] = {
        "id": job_id,
        "filename": file.filename,
        "size_mb": round(size_mb, 2),
        "status": "processing",
        "progress": 0,
        "current_step": "Starting conversion",
        "pdf_path": str(pdf_path),
        "output_dir": str(output_dir),
        "md_filename": None,
        "result_stats": None,
        "error": None,
    }

    # Start background conversion
    asyncio.create_task(_run_pipeline(job_id, pdf_path, output_dir))

    return {"job_id": job_id, "filename": file.filename, "size_mb": round(size_mb, 2)}


async def _run_pipeline(job_id: str, pdf_path: Path, output_dir: Path):
    """Run the conversion pipeline in the background."""
    job = jobs[job_id]

    def on_progress(progress: float, step: str):
        job["progress"] = progress
        job["current_step"] = step

    try:
        pipe = PipelineOrchestrator(pdf_path, output_dir)
        pipe.set_progress_callback(on_progress)

        # Run synchronous pipeline in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, pipe.convert)

        # Determine output filename
        md_filename = pdf_path.stem + ".md"
        md_path = output_dir / md_filename

        job["status"] = "complete"
        job["progress"] = 100
        job["current_step"] = "Conversion complete"
        job["md_filename"] = md_filename
        job["result_stats"] = {
            "pages": len(result.pages),
            "blocks": result.total_blocks,
            "images": result.total_images,
            "tables": result.total_tables,
        }

        logger.info(f"Job {job_id} complete: {md_filename}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}\n{traceback.format_exc()}")
        job["status"] = "error"
        job["progress"] = 0
        job["current_step"] = "Failed"
        job["error"] = str(e)


@app.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the current status of a conversion job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    job = jobs[job_id]
    return {
        "id": job["id"],
        "filename": job["filename"],
        "status": job["status"],
        "progress": job["progress"],
        "current_step": job["current_step"],
        "result_stats": job.get("result_stats"),
        "error": job["error"],
    }


@app.get("/api/jobs/{job_id}/download/markdown")
async def download_markdown(job_id: str):
    """Download the generated Markdown file."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    job = jobs[job_id]
    if job["status"] != "complete":
        raise HTTPException(status_code=409, detail=f"Job is {job['status']}, not complete.")

    output_dir = Path(job["output_dir"])
    md_path = output_dir / job["md_filename"]

    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Markdown file not found.")

    return FileResponse(
        path=str(md_path),
        filename=job["md_filename"],
        media_type="text/markdown",
    )


@app.get("/api/jobs/{job_id}/download/zip")
async def download_zip(job_id: str):
    """Download the full output package (markdown + images) as ZIP."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    job = jobs[job_id]
    if job["status"] != "complete":
        raise HTTPException(status_code=409, detail=f"Job is {job['status']}, not complete.")

    output_dir = Path(job["output_dir"])

    # Create ZIP if not exists
    zip_path = output_dir.with_suffix(".zip")
    if not zip_path.exists():
        zip_path = create_output_zip(output_dir)

    return FileResponse(
        path=str(zip_path),
        filename=f"{job['md_filename'].replace('.md', '')}_package.zip",
        media_type="application/zip",
    )


@app.get("/api/jobs/{job_id}/preview")
async def preview_markdown(job_id: str):
    """Get the Markdown content for preview."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    job = jobs[job_id]
    if job["status"] != "complete":
        raise HTTPException(status_code=409, detail=f"Job is {job['status']}, not complete.")

    output_dir = Path(job["output_dir"])
    md_path = output_dir / job["md_filename"]

    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Markdown file not found.")

    content = md_path.read_text(encoding="utf-8")
    return {"content": content, "filename": job["md_filename"]}


# ---------------------------------------------------------------------------
# Frontend Static Files
# ---------------------------------------------------------------------------

# Mount frontend static files
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
