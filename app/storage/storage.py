import os
import uuid
import boto3
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional, Dict, Tuple
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)

class PresentationStorage:
    """Storage for PowerPoint presentations using S3-compatible storage."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PresentationStorage, cls).__new__(cls)
            cls._instance._init_s3_client()
        return cls._instance
    
    def _init_s3_client(self):
        """Initialize the S3 client using environment variables."""
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv("AWS_ENDPOINT_URL_S3"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION")
            )
            self.bucket_name = os.getenv("BUCKET_NAME", "presentations")
            
            # Ensure bucket exists
            self._ensure_bucket_exists()
            
        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
            # Fall back to local storage if S3 fails
            self._use_local_storage = True
            
            # Create local directories as fallback
            from pathlib import Path
            self.storage_dir = Path(__file__).parent / "files"
            self.meta_dir = Path(__file__).parent / "metadata"
            self.storage_dir.mkdir(exist_ok=True)
            self.meta_dir.mkdir(exist_ok=True)
        else:
            self._use_local_storage = False
    
    def _ensure_bucket_exists(self):
        """Create the bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            # If bucket doesn't exist (404) create it
            if e.response['Error']['Code'] == '404':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                raise
    
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
        instance = PresentationStorage()
        presentation_id = str(uuid.uuid4())
        
        # Create metadata
        metadata = {
            "filename": filename,
            "created_at": datetime.now().isoformat(),
        }
        
        if instance._use_local_storage:
            # Fall back to local storage
            file_path = instance.storage_dir / f"{presentation_id}.pptx"
            meta_path = instance.meta_dir / f"{presentation_id}.json"
            
            # Save the presentation file
            with open(file_path, "wb") as f:
                f.write(presentation_bytes.getvalue())
            
            # Save metadata
            with open(meta_path, "w") as f:
                json.dump(metadata, f)
        else:
            # Store in S3
            try:
                instance.s3_client.put_object(
                    Bucket=instance.bucket_name,
                    Key=f"{presentation_id}.pptx",
                    Body=presentation_bytes.getvalue(),
                    Metadata=metadata
                )
            except Exception as e:
                logger.error(f"Error saving presentation to S3: {e}")
                raise
        
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
        instance = PresentationStorage()
        
        if instance._use_local_storage:
            # Fall back to local storage
            file_path = instance.storage_dir / f"{presentation_id}.pptx"
            meta_path = instance.meta_dir / f"{presentation_id}.json"
            
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
        else:
            # Get from S3
            try:
                response = instance.s3_client.get_object(
                    Bucket=instance.bucket_name,
                    Key=f"{presentation_id}.pptx"
                )
                
                # Get metadata from S3 response
                metadata = response.get("Metadata", {})
                if "filename" not in metadata:
                    metadata["filename"] = f"{presentation_id}.pptx"
                
                # Read the presentation data
                pptx_bytes = BytesIO(response["Body"].read())
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    return None
                else:
                    logger.error(f"Error retrieving presentation from S3: {e}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error retrieving presentation: {e}")
                return None
        
        return pptx_bytes, metadata
    
    @staticmethod
    def delete_old_presentations(max_age_hours: int = 24):
        """
        Delete presentations older than the specified age.
        
        Args:
            max_age_hours: Maximum age in hours
        """
        instance = PresentationStorage()
        max_age = datetime.now() - timedelta(hours=max_age_hours)
        
        if instance._use_local_storage:
            # Fall back to local storage
            for file_path in instance.storage_dir.glob("*.pptx"):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < max_age:
                    # Delete the presentation file
                    os.remove(file_path)
                    
                    # Delete the metadata file if it exists
                    presentation_id = file_path.stem
                    meta_path = instance.meta_dir / f"{presentation_id}.json"
                    if meta_path.exists():
                        os.remove(meta_path)
        else:
            # Delete from S3
            try:
                # List all objects in the bucket
                response = instance.s3_client.list_objects_v2(Bucket=instance.bucket_name)
                
                for obj in response.get("Contents", []):
                    try:
                        # Get metadata for this object
                        obj_response = instance.s3_client.head_object(
                            Bucket=instance.bucket_name, 
                            Key=obj["Key"]
                        )
                        
                        metadata = obj_response.get("Metadata", {})
                        created_at_str = metadata.get("created_at")
                        
                        # If created_at is in metadata, check if it's old enough to delete
                        if created_at_str:
                            try:
                                created_at = datetime.fromisoformat(created_at_str)
                                if created_at < max_age:
                                    instance.s3_client.delete_object(
                                        Bucket=instance.bucket_name,
                                        Key=obj["Key"]
                                    )
                            except (ValueError, TypeError):
                                # If the date is invalid, use last modified time instead
                                if obj["LastModified"].replace(tzinfo=None) < max_age:
                                    instance.s3_client.delete_object(
                                        Bucket=instance.bucket_name,
                                        Key=obj["Key"]
                                    )
                        else:
                            # If no created_at metadata, use last modified time
                            if obj["LastModified"].replace(tzinfo=None) < max_age:
                                instance.s3_client.delete_object(
                                    Bucket=instance.bucket_name,
                                    Key=obj["Key"]
                                )
                    except Exception as e:
                        logger.error(f"Error processing object {obj['Key']}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error deleting old presentations from S3: {e}")
                # If S3 deletion fails, don't raise exception to avoid breaking the cleanup task