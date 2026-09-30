from minio import Minio
from minio.error import S3Error
from io import BytesIO
from uuid import UUID
from typing import Optional
import mimetypes
from llmsync.config import settings
import logging

logger = logging.getLogger(__name__)

def infer_mime_type(filename: str, content_type: Optional[str]) -> str:
    """Infer MIME type from filename if Content-Type not provided."""
    if content_type:
        return content_type

    # Guess from extension
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"

class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket = settings.minio_bucket

    async def init_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created MinIO bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Failed to create bucket: {e}")
            raise

    def upload_file(
        self,
        user_id: UUID,
        file_id: UUID,
        data: bytes,
        content_type: str
    ) -> str:
        """Upload encrypted file to MinIO."""
        storage_path = f"{user_id}/{file_id}.enc"

        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=storage_path,
                data=BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata={
                    "user-id": str(user_id),
                    "file-id": str(file_id),
                    "encrypted": "true"
                }
            )
            logger.info(f"Uploaded file {file_id} to {storage_path}")
            return storage_path
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def download_file(self, storage_path: str) -> bytes:
        """Download encrypted file from MinIO."""
        try:
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=storage_path
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Failed to download file: {e}")
            raise

    def delete_file(self, storage_path: str):
        """Delete file from MinIO."""
        try:
            self.client.remove_object(
                bucket_name=self.bucket,
                object_name=storage_path
            )
            logger.info(f"Deleted file {storage_path}")
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            raise

minio_client = MinioClient()
