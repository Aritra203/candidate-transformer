import os
import json
import logging
from pathlib import Path
from typing import Any, List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, ValidationError

# Add root folder to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.pipeline.pipeline import CandidateTransformerPipeline
from src.models.config import ProjectionConfig
from src.utils.exceptions import CandidateTransformerError
from src.utils.logging import configure_logging

# Configure logging at start
configure_logging(verbose=True)

app = FastAPI(title="Multi-Source Candidate Data Transformer API")

# Enable CORS for the Next.js frontend (default port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class TransformRequest(BaseModel):
    csv_path: Optional[str] = None
    resume_path: Optional[str] = None
    config: Optional[dict] = None

class LogEntry(BaseModel):
    timestamp: str
    level: str
    stage: str
    message: str

# Custom logging handler to capture logs in memory for a single run
class CapturingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: List[dict] = []
        # Setup formatter matching src/utils/logging.py
        self.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        ))

    def emit(self, record: logging.LogRecord) -> None:
        # Extract stage name from the logger name (e.g. 'candidate_transformer.pipeline.merger' -> 'merger')
        parts = record.name.split('.')
        stage = parts[-1] if len(parts) > 1 else "system"
        
        self.records.append({
            "timestamp": self.formatter.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname.strip(),
            "stage": stage,
            "message": record.getMessage()
        })

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file (CSV or PDF) and save it locally in the uploads folder."""
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    ext = Path(filename).suffix.lower()
    if ext not in [".csv", ".pdf", ".json"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type '{ext}'. Only CSV, PDF, and JSON are supported."
        )

    file_path = UPLOAD_DIR / filename
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        file_type = "csv" if ext == ".csv" else "pdf" if ext == ".pdf" else "json"
        
        return {
            "filename": filename,
            "size": len(content),
            "type": file_type,
            "path": file_path.as_posix()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

@app.post("/api/validate-config")
async def validate_config(config_dict: dict):
    """Validate runtime JSON configuration before run."""
    try:
        # Validate structure using Pydantic model
        ProjectionConfig.model_validate(config_dict)
        return {"valid": True, "message": "Configuration is valid."}
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc_str = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "loc": loc_str,
                "msg": error["msg"],
                "type": error["type"]
            })
        return JSONResponse(
            status_code=422,
            content={"valid": False, "errors": errors, "message": "Configuration validation failed."}
        )

@app.post("/api/transform")
async def transform_candidate(request: TransformRequest):
    """Run the candidate transformer pipeline on selected inputs."""
    # Capture logs during this run
    capturing_handler = CapturingHandler()
    root_logger = logging.getLogger("candidate_transformer")
    root_logger.addHandler(capturing_handler)
    
    # Store previous logging level and set to DEBUG to get detailed pipeline logs
    prev_level = root_logger.level
    root_logger.setLevel(logging.DEBUG)

    source_paths = []
    if request.csv_path:
        source_paths.append(Path(request.csv_path))
    if request.resume_path:
        source_paths.append(Path(request.resume_path))

    if not source_paths:
        root_logger.removeHandler(capturing_handler)
        root_logger.setLevel(prev_level)
        raise HTTPException(
            status_code=400,
            detail="No files specified. Provide at least one CSV or Resume PDF file."
        )

    # Prepare configuration
    config_dict = request.config
    if not config_dict:
        # Load default configuration
        default_config_path = Path("config/default.json")
        try:
            with open(default_config_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        except Exception as e:
            root_logger.removeHandler(capturing_handler)
            root_logger.setLevel(prev_level)
            raise HTTPException(
                status_code=500,
                detail=f"Could not load default configuration: {str(e)}"
            )

    try:
        # Load and validate projection config
        config = ProjectionConfig.model_validate(config_dict)
    except ValidationError as e:
        root_logger.removeHandler(capturing_handler)
        root_logger.setLevel(prev_level)
        errors = [f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid configuration schema: {', '.join(errors)}"
        )

    try:
        # Run pipeline
        pipeline = CandidateTransformerPipeline()
        projected_profiles = pipeline.run(source_paths, config)

        # Write output to output/result.json (as specified in layout)
        output_path = Path("output/result.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(projected_profiles, f, indent=2, ensure_ascii=False)

        # Clean up logger
        root_logger.removeHandler(capturing_handler)
        root_logger.setLevel(prev_level)

        return {
            "success": True,
            "profiles": projected_profiles,
            "logs": capturing_handler.records,
            "outputPath": str(output_path)
        }

    except CandidateTransformerError as exc:
        root_logger.removeHandler(capturing_handler)
        root_logger.setLevel(prev_level)
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline error occurred: {str(exc)}"
        )
    except Exception as exc:
        root_logger.removeHandler(capturing_handler)
        root_logger.setLevel(prev_level)
        raise HTTPException(
            status_code=500,
            detail=f"System error: {str(exc)}"
        )

@app.get("/api/download")
async def download_output():
    """Serve the final output JSON file."""
    output_path = Path("output/result.json")
    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Output file not found. Run the pipeline first."
        )
    return FileResponse(
        path=output_path,
        filename="canonical_profile.json",
        media_type="application/json"
    )

@app.get("/api/download-design")
async def download_design(type: str = "konar"):
    """Serve the generated design document PDF."""
    if type == "victus":
        path = Path("Aritra_Victus_aritra_victus_Eightfold.pdf")
    else:
        path = Path("Aritra_Konar_konararitra72@gmail.com_Eightfold.pdf")
        
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Design PDF '{path.name}' not found. Run generate_design_pdf.py first."
        )
    return FileResponse(
        path=path,
        filename=path.name,
        media_type="application/pdf"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
