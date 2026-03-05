"""
CLONEAI ULTRA — MinIO Storage Service
=======================================
S3-compatible object storage for uploads, outputs, and model artifacts.
Falls back to local filesystem when MinIO is unavailable.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import structlog

from ..config import settings

logger = structlog.get_logger()


class StorageService:
    """
    S3-compatible storage via MinIO.
    
    Falls back to local filesystem when USE_MINIO=False or MinIO is unreachable.
    All paths are stored as relative keys (e.g. "uploads/photo/abc123.jpg").
    """

    def __init__(self):
        self._client = None
        self._use_minio = settings.USE_MINIO
        self._local_root = Path(".")

    def _get_client(self):
        """Lazy-initialize MinIO client."""
        if self._client is not None:
            return self._client

        if not self._use_minio:
            return None

        try:
            from minio import Minio

            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_SSL,
            )

            # Ensure bucket exists
            if not client.bucket_exists(settings.MINIO_BUCKET):
                client.make_bucket(settings.MINIO_BUCKET)
                logger.info("storage.bucket_created", bucket=settings.MINIO_BUCKET)

            self._client = client
            logger.info("storage.minio_connected", endpoint=settings.MINIO_ENDPOINT)
            return client

        except Exception as e:
            logger.warning("storage.minio_unavailable", error=str(e))
            self._use_minio = False
            return None

    async def upload_file(
        self,
        local_path: str,
        object_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a file to storage.

        Args:
            local_path: Path to local file
            object_key: Storage key (e.g. "uploads/photo/abc.jpg")
            content_type: MIME type

        Returns:
            URL or local path to the stored object
        """
        client = self._get_client()

        if client:
            def _upload():
                client.fput_object(
                    settings.MINIO_BUCKET,
                    object_key,
                    local_path,
                    content_type=content_type,
                )
                return self._get_object_url(object_key)

            url = await asyncio.to_thread(_upload)
            logger.info("storage.uploaded", key=object_key, backend="minio")
            return url
        else:
            # Local fallback — file already exists at local_path
            logger.info("storage.uploaded", key=local_path, backend="local")
            return local_path

    async def download_file(self, object_key: str, local_path: str) -> str:
        """Download an object to local filesystem."""
        client = self._get_client()

        if client:
            def _download():
                client.fget_object(settings.MINIO_BUCKET, object_key, local_path)
                return local_path

            result = await asyncio.to_thread(_download)
            logger.info("storage.downloaded", key=object_key)
            return result
        else:
            # Local fallback — assume object_key is a local path
            return object_key

    async def get_presigned_url(
        self,
        object_key: str,
        expires_seconds: int = 3600,
    ) -> str:
        """Get a presigned download URL (1 hour default)."""
        client = self._get_client()

        if client:
            from datetime import timedelta

            def _presign():
                return client.presigned_get_object(
                    settings.MINIO_BUCKET,
                    object_key,
                    expires=timedelta(seconds=expires_seconds),
                )

            url = await asyncio.to_thread(_presign)
            return url
        else:
            # Local fallback — return API path
            return f"/outputs/{object_key}"

    async def delete_file(self, object_key: str) -> bool:
        """Delete an object from storage."""
        client = self._get_client()

        if client:
            def _delete():
                client.remove_object(settings.MINIO_BUCKET, object_key)

            await asyncio.to_thread(_delete)
            logger.info("storage.deleted", key=object_key)
            return True
        else:
            # Local fallback
            local_path = self._local_root / object_key
            if local_path.exists():
                local_path.unlink()
                return True
            return False

    async def file_exists(self, object_key: str) -> bool:
        """Check if an object exists in storage."""
        client = self._get_client()

        if client:
            try:
                def _stat():
                    client.stat_object(settings.MINIO_BUCKET, object_key)
                    return True

                return await asyncio.to_thread(_stat)
            except Exception:
                return False
        else:
            return (self._local_root / object_key).exists()

    async def list_objects(self, prefix: str = "", recursive: bool = True) -> list:
        """List objects under a prefix."""
        client = self._get_client()

        if client:
            def _list():
                objects = client.list_objects(
                    settings.MINIO_BUCKET,
                    prefix=prefix,
                    recursive=recursive,
                )
                return [
                    {
                        "key": obj.object_name,
                        "size": obj.size,
                        "last_modified": str(obj.last_modified),
                    }
                    for obj in objects
                ]

            return await asyncio.to_thread(_list)
        else:
            # Local fallback
            local_dir = self._local_root / prefix
            if not local_dir.exists():
                return []
            items = []
            for f in local_dir.rglob("*") if recursive else local_dir.iterdir():
                if f.is_file():
                    items.append({
                        "key": str(f.relative_to(self._local_root)),
                        "size": f.stat().st_size,
                        "last_modified": str(f.stat().st_mtime),
                    })
            return items

    def _get_object_url(self, object_key: str) -> str:
        """Construct the object URL."""
        protocol = "https" if settings.MINIO_USE_SSL else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_key}"
