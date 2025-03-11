from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from pathlib import Path
import asyncio
from datetime import datetime

from app.schemas.presentation import Presentation
from app.core.pptx_generator import create_presentation
from app.storage.storage import PresentationStorage

app = FastAPI(
    title="PPTX API",
    description="API for generating PowerPoint presentations from JSON schema",
    version="0.1.0",
)

# Create files directory if not exists for static file serving
files_dir = Path(__file__).parent / "storage" / "files"
files_dir.mkdir(exist_ok=True)

# Set up templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files directory
app.mount("/presentations", StaticFiles(directory=str(files_dir)), name="presentations")


@app.get("/")
def read_root():
    return {"status": "ok", "message": "PPTX API is running"}


@app.post("/generate-pptx")
def generate_pptx(request: Request, presentation: Presentation):
    try:
        # Generate the presentation
        pptx_bytes = create_presentation(presentation)
        
        # Save the presentation to storage with custom filename
        presentation_id = PresentationStorage.save_presentation(
            pptx_bytes, 
            filename=presentation.filename
        )
        
        # Generate download URL
        base_url = str(request.base_url).rstrip('/')
        download_url = f"{base_url}/download/{presentation_id}"
        
        return JSONResponse(
            status_code=200,
            content={
                "presentation_id": presentation_id,
                "download_url": download_url,
                "filename": presentation.filename,
                "expires_in_hours": 24
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{presentation_id}")
def download_presentation(request: Request, presentation_id: str):
    # Get the presentation from storage
    result = PresentationStorage.get_presentation(presentation_id)
    
    if not result:
        # Return the expired presentation page with the sad horse
        return templates.TemplateResponse(
            "expired.html",
            {"request": request}
        )
    
    pptx_bytes, metadata = result
    filename = metadata.get("filename", f"{presentation_id}.pptx")
    
    return StreamingResponse(
        pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )


@app.on_event("startup")
async def startup_event():
    # Start the cleanup task
    asyncio.create_task(cleanup_old_presentations())


async def cleanup_old_presentations():
    """Background task to periodically clean up old presentations."""
    while True:
        try:
            PresentationStorage.delete_old_presentations(max_age_hours=24)
        except Exception as e:
            print(f"Error cleaning up old presentations: {e}")
        
        # Run once per hour
        await asyncio.sleep(3600)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)