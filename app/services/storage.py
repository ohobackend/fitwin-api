from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Any
from urllib.parse import quote
import boto3
from app.core.config import Settings, get_settings

class ObjectStorageService:
    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = client or boto3.client(
            "s3", endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.s3_access_key_id,
            aws_secret_access_key=self.settings.s3_secret_access_key,
            region_name=self.settings.s3_region,
        )

    def upload_file(self, file_path: str | Path, object_key: str, content_type: str | None = None) -> str:
        extra_args = {"ContentType": content_type} if content_type else None
        self.client.upload_file(str(file_path), self.settings.s3_bucket_name, object_key, ExtraArgs=extra_args)
        return object_key

    def upload_fileobj(self, file_object: BinaryIO, object_key: str, content_type: str | None = None) -> str:
        extra_args = {"ContentType": content_type} if content_type else None
        self.client.upload_fileobj(file_object, self.settings.s3_bucket_name, object_key, ExtraArgs=extra_args)
        return object_key

    def download_file(self, object_key: str, destination: str | Path) -> Path:
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.settings.s3_bucket_name, object_key, str(destination_path))
        return destination_path

    def download_bytes(self, object_key: str) -> bytes:
        buffer = BytesIO()
        self.client.download_fileobj(self.settings.s3_bucket_name, object_key, buffer)
        return buffer.getvalue()

    def create_download_url(self, object_key: str, expires_in: int | None = None) -> str:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.settings.s3_bucket_name, "Key": object_key},
            ExpiresIn=expires_in or self.settings.s3_presigned_url_expire_seconds,
        )

    def get_object_url(self, object_key: str) -> str:
        escaped_key = quote(object_key, safe="/")
        if self.settings.s3_endpoint_url:
            return f"{self.settings.s3_endpoint_url.rstrip('/')}/{self.settings.s3_bucket_name}/{escaped_key}"
        return f"https://{self.settings.s3_bucket_name}.s3.{self.settings.s3_region}.amazonaws.com/{escaped_key}"
