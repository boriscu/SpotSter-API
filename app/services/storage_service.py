import boto3
from typing import Optional
from botocore.exceptions import ClientError

from config.app_config import AppConfig
from app.init.logger_setup import LoggerSetup


class StorageService:
    """
    Service class for interacting with S3-compatible object storage.
    Abstracts all storage operations behind a clean interface.
    All file interactions from other services must go through this class.
    """

    _client = None

    @classmethod
    def _get_client(cls):
        """
        Returns a cached boto3 S3 client instance.

        Returns:
            boto3.client: The configured S3 client.
        """
        if cls._client is None:
            cls._client = boto3.client(
                "s3",
                endpoint_url=AppConfig.S3_ENDPOINT_URL,
                aws_access_key_id=AppConfig.S3_ACCESS_KEY,
                aws_secret_access_key=AppConfig.S3_SECRET_KEY,
                region_name=AppConfig.S3_REGION,
            )
        return cls._client

    @classmethod
    def upload_file(
        cls,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        bucket: Optional[str] = None,
    ) -> str:
        """
        Uploads a file to S3 storage.

        Args:
            file_data: The raw file bytes to upload.
            key: The S3 object key (path) for the file.
            content_type: The MIME type of the file.
            bucket: The target bucket. Defaults to configured bucket.

        Returns:
            str: The full URL path to the uploaded file.

        Raises:
            RuntimeError: If the upload fails.
        """
        logger = LoggerSetup.get_logger("general")
        bucket = bucket or AppConfig.S3_BUCKET_NAME

        try:
            cls._get_client().put_object(
                Bucket=bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
            )

            file_url = f"{AppConfig.S3_ENDPOINT_URL}/{bucket}/{key}"
            logger.info(f"File uploaded successfully: {key}")
            return file_url

        except ClientError as error:
            logger.error(f"Failed to upload file {key}: {error}")
            raise RuntimeError(f"Failed to upload file: {error}")

    @classmethod
    def delete_file(cls, key: str, bucket: Optional[str] = None) -> None:
        """
        Deletes a file from S3 storage.

        Args:
            key: The S3 object key (path) of the file to delete.
            bucket: The target bucket. Defaults to configured bucket.

        Raises:
            RuntimeError: If the deletion fails.
        """
        logger = LoggerSetup.get_logger("general")
        bucket = bucket or AppConfig.S3_BUCKET_NAME

        try:
            cls._get_client().delete_object(Bucket=bucket, Key=key)
            logger.info(f"File deleted successfully: {key}")

        except ClientError as error:
            logger.error(f"Failed to delete file {key}: {error}")
            raise RuntimeError(f"Failed to delete file: {error}")

    @classmethod
    def get_file_url(cls, key: str, bucket: Optional[str] = None) -> str:
        """
        Constructs the public URL for a stored file.

        Args:
            key: The S3 object key (path) of the file.
            bucket: The target bucket. Defaults to configured bucket.

        Returns:
            str: The full URL to the file.
        """
        bucket = bucket or AppConfig.S3_BUCKET_NAME
        return f"{AppConfig.S3_ENDPOINT_URL}/{bucket}/{key}"

    @classmethod
    def generate_presigned_url(
        cls,
        key: str,
        expiration: int = 3600,
        bucket: Optional[str] = None,
    ) -> str:
        """
        Generates a presigned URL for temporary access to a private file.

        Args:
            key: The S3 object key (path) of the file.
            expiration: Time in seconds before the URL expires. Defaults to 1 hour.
            bucket: The target bucket. Defaults to configured bucket.

        Returns:
            str: A presigned URL granting temporary access to the file.

        Raises:
            RuntimeError: If URL generation fails.
        """
        logger = LoggerSetup.get_logger("general")
        bucket = bucket or AppConfig.S3_BUCKET_NAME

        try:
            url = cls._get_client().generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expiration,
            )
            return url

        except ClientError as error:
            logger.error(f"Failed to generate presigned URL for {key}: {error}")
            raise RuntimeError(f"Failed to generate presigned URL: {error}")

    @classmethod
    def file_exists(cls, key: str, bucket: Optional[str] = None) -> bool:
        """
        Checks if a file exists in S3 storage.

        Args:
            key: The S3 object key (path) to check.
            bucket: The target bucket. Defaults to configured bucket.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        bucket = bucket or AppConfig.S3_BUCKET_NAME

        try:
            cls._get_client().head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
