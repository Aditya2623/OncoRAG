import json
from typing import Optional

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)
from loguru import logger

from src.ingestion.s3.exceptions import (
    S3ClientError,
    S3DeleteError,
    S3FetchError,
    S3FolderDeleteError,
    S3UploadError,
)


class S3Client:
    def __init__(self, bucket_name: str = "oncorag"):
        self.bucket_name = bucket_name
        self._client = boto3.client("s3")

    def upload_data(
        self,
        key: str,
        data: str | dict | list,
        content_type: Optional[str] = None,
    ) -> bool:
        """
        Uploads string/json/xml/etc directly to S3.
        """

        try:
            if isinstance(data, (dict, list)):
                body = json.dumps(data).encode("utf-8")
                content_type = content_type or "application/json"
            else:
                body = data.encode("utf-8")

            self._client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=body,
                ContentType=content_type or "text/plain",
            )

            logger.info(f"Uploaded file to S3: {key}")
            return True

        except NoCredentialsError as e:
            logger.exception("AWS credentials not found.")
            raise S3UploadError("AWS credentials not found.") from e

        except EndpointConnectionError as e:
            logger.exception(f"Could not connect to AWS endpoint: {e}")
            raise S3UploadError("Could not connect to AWS endpoint.") from e

        except ClientError as e:
            message = e.response["Error"]["Message"]

            logger.exception(f"S3 upload failed for key={key}: {message}")

            raise S3UploadError(
                f"Failed to upload file to S3. key={key}, error={message}"
            ) from e

        except BotoCoreError as e:
            logger.exception(f"BotoCore error while uploading {key}: {e}")

            raise S3UploadError(
                f"BotoCore error while uploading file. key={key}"
            ) from e

        except Exception as e:
            logger.exception(f"Unexpected error while uploading {key}: {e}")

            raise S3UploadError(
                f"Unexpected error while uploading file. key={key}"
            ) from e

    def fetch_single_file(self, key: str) -> str:
        """
        Fetch a single file by exact S3 key.
        """

        try:
            response = self._client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )

            data = response["Body"].read().decode("utf-8")

            logger.info(f"Fetched file from S3: {key}")

            return data

        except self._client.exceptions.NoSuchKey as e:
            logger.exception(f"File not found in S3: {key}")

            raise S3FetchError(f"File not found in S3. key={key}") from e

        except ClientError as e:
            message = e.response["Error"]["Message"]

            logger.exception(f"S3 fetch failed for key={key}: {message}")

            raise S3FetchError(
                f"Failed to fetch file from S3. key={key}, error={message}"
            ) from e

        except BotoCoreError as e:
            logger.exception(f"BotoCore error while fetching {key}: {e}")

            raise S3FetchError(f"BotoCore error while fetching file. key={key}") from e

        except Exception as e:
            logger.exception(f"Unexpected error while fetching {key}: {e}")

            raise S3FetchError(
                f"Unexpected error while fetching file. key={key}"
            ) from e

    def delete_file(self, key: str) -> bool:
        """
        Deletes a single file from S3.
        """

        try:
            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )

            logger.info(f"Deleted file from S3: {key}")

            return True

        except ClientError as e:
            message = e.response["Error"]["Message"]

            logger.exception(f"S3 delete failed for key={key}: {message}")

            raise S3DeleteError(
                f"Failed to delete file from S3. key={key}, error={message}"
            ) from e

        except BotoCoreError as e:
            logger.exception(f"BotoCore error while deleting {key}: {e}")

            raise S3DeleteError(f"BotoCore error while deleting file. key={key}") from e

        except Exception as e:
            logger.exception(f"Unexpected error while deleting {key}: {e}")

            raise S3DeleteError(
                f"Unexpected error while deleting file. key={key}"
            ) from e

    def delete_folder(self, folder_name: str) -> bool:
        """
        Deletes all objects under a folder.
        """

        try:
            prefix = folder_name.rstrip("/") + "/"

            response = self._client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
            )

            contents = response.get("Contents", [])

            if not contents:
                logger.warning(f"No files found in folder: {folder_name}")
                return True

            objects = [{"Key": obj["Key"]} for obj in contents]

            self._client.delete_objects(
                Bucket=self.bucket_name,
                Delete={"Objects": objects},
            )

            logger.info(f"Deleted folder from S3: {folder_name}")

            return True

        except ClientError as e:
            message = e.response["Error"]["Message"]

            logger.exception(
                f"S3 folder delete failed for folder={folder_name}: {message}"
            )

            raise S3FolderDeleteError(
                f"Failed to delete folder from S3. "
                f"folder={folder_name}, error={message}"
            ) from e

        except BotoCoreError as e:
            logger.exception(f"BotoCore error while deleting folder {folder_name}: {e}")

            raise S3FolderDeleteError(
                f"BotoCore error while deleting folder. " f"folder={folder_name}"
            ) from e

        except Exception as e:
            logger.exception(
                f"Unexpected error while deleting folder {folder_name}: {e}"
            )

            raise S3FolderDeleteError(
                f"Unexpected error while deleting folder. " f"folder={folder_name}"
            ) from e
