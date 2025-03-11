from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

from app.schemas.presentation import Presentation
from app.core.pptx_generator import create_presentation

app = FastAPI(
    title="PPTX API",
    description="API for generating PowerPoint presentations from JSON schema",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "PPTX API is running"}


@app.post("/generate-pptx")
def generate_pptx(presentation: Presentation):
    try:
        pptx_bytes = create_presentation(presentation)
        return StreamingResponse(
            pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": "attachment; filename=presentation.pptx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)