import os
import uuid
import json
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Tuple

# Create storage directory if it doesn't exist
STORAGE_DIR = Path(__file__).parent / "files"
STORAGE_DIR.mkdir(exist_ok=True)
META_DIR = Path(__file__).parent / "metadata"
META_DIR.mkdir(exist_ok=True)


class PresentationStorage:
    """Storage for PowerPoint presentations."""
    
    @staticmethod
    def save_presentation(presentation_bytes: BytesIO, filename: str = "presentation.pptx") -> str:
        """
        Save a presentation to storage and return its unique ID.
        
        Args:
            presentation_bytes: BytesIO object containing the presentation
            filename: Custom filename for the presentation
            
        Returns:
            str: Unique ID for the presentation
        """
        presentation_id = str(uuid.uuid4())
        file_path = STORAGE_DIR / f"{presentation_id}.pptx"
        meta_path = META_DIR / f"{presentation_id}.json"
        
        # Save the presentation file
        with open(file_path, "wb") as f:
            f.write(presentation_bytes.getvalue())
        
        # Save metadata
        metadata = {
            "filename": filename,
            "created_at": datetime.now().isoformat(),
        }
        
        with open(meta_path, "w") as f:
            json.dump(metadata, f)
        
        return presentation_id
    
    @staticmethod
    def get_presentation(presentation_id: str) -> Optional[Tuple[BytesIO, Dict]]:
        """
        Retrieve a presentation and its metadata from storage.
        
        Args:
            presentation_id: Unique ID of the presentation
            
        Returns:
            Optional[Tuple[BytesIO, Dict]]: BytesIO object containing the presentation
                                           and metadata dict, or None if not found
        """
        file_path = STORAGE_DIR / f"{presentation_id}.pptx"
        meta_path = META_DIR / f"{presentation_id}.json"
        
        if not file_path.exists():
            return None
        
        # Read the presentation file
        with open(file_path, "rb") as f:
            pptx_bytes = BytesIO(f.read())
        
        # Read metadata if it exists
        metadata = {}
        if meta_path.exists():
            with open(meta_path, "r") as f:
                try:
                    metadata = json.load(f)
                except json.JSONDecodeError:
                    metadata = {"filename": "presentation.pptx"}
        else:
            metadata = {"filename": "presentation.pptx"}
        
        return pptx_bytes, metadata
    
    @staticmethod
    def delete_old_presentations(max_age_hours: int = 24):
        """
        Delete presentations older than the specified age.
        
        Args:
            max_age_hours: Maximum age in hours
        """
        max_age = datetime.now() - timedelta(hours=max_age_hours)
        
        for file_path in STORAGE_DIR.glob("*.pptx"):
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if file_time < max_age:
                # Delete the presentation file
                os.remove(file_path)
                
                # Delete the metadata file if it exists
                presentation_id = file_path.stem
                meta_path = META_DIR / f"{presentation_id}.json"
                if meta_path.exists():
                    os.remove(meta_path)