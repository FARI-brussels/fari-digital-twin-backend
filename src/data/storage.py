import abc
import json
import os
from typing import Union

from azure.storage.blob import BlobServiceClient
import boto3
from botocore.client import Config


class StorageManager(abc.ABC):
    @abc.abstractmethod
    def write(self, file_name: str, data: bytes): ...

    @abc.abstractmethod
    def read(self, file_name: str) -> bytes: ...

    @abc.abstractmethod
    def delete(self, file_name: str): ...


class AzureBlobManager(StorageManager):
    def __init__(self, connection_string, container_name):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        self.container_client = self.blob_service_client.get_container_client(
            container_name
        )

    def write(self, file_name: str, data: bytes) -> str:
        if data is None:
            data = b""

        blob_client = self.container_client.get_blob_client(file_name)
        blob_client.upload_blob(data, overwrite=True)

        return blob_client.url

    def read(self, file_name: str) -> bytes:
        blob_client = self.container_client.get_blob_client(
            file_name.split(self.container_client.container_name + "/")[-1]
        )
        blob_data = blob_client.download_blob().readall()
        return blob_data

    def delete(self, file_name: str):
        blob_client = self.container_client.get_blob_client(
            file_name.split(self.container_client.container_name + "/")[-1]
        )
        blob_client.delete_blob()


class OVHBlobManager(StorageManager):
    def __init__(self, endpoint_url, access_key, secret_key, bucket_name):
        self.bucket_name = bucket_name
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="gra",
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required"
            ),
        )

    def write(self, file_name: str, data: bytes) -> str:
        self.s3.put_object(Bucket=self.bucket_name, Key=file_name, Body=data)
        return f"{self.s3.meta.endpoint_url}/{self.bucket_name}/{file_name}"

    def read(self, file_name: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket_name, Key=file_name)
        return response['Body'].read()

    def delete(self, file_name: str):
        self.s3.delete_object(Bucket=self.bucket_name, Key=file_name)


class FileStorageManager(StorageManager):
    def __init__(self, directory):
        self.directory = directory

    def write(self, file_name: str, data: Union[bytes, dict, list]) -> str:
        """
        Write data to a file in the local file system.

        :param file_name: Name of the file to create or update.
        :param data: Data to write to the file. Can be bytes, dict, or list (for JSON).

        :return: Path of the file.
        """
        file_path = os.path.join(self.directory, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if isinstance(data, (dict, list)):
            # Handle JSON data
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
        else:
            # Handle binary data
            with open(file_path, "wb") as file:
                file.write(data)

        return file_path

    def read(self, file_name: str) -> bytes:
        with open(file_name, "rb") as file:
            return file.read()

    def delete(self, file_name: str):
        os.remove(file_name)


# Storage manager selection based on environment variables
if "AZURE_STORAGE_CONNECTION_STRING" in os.environ:
    storage_manager = AzureBlobManager(
        os.environ["AZURE_STORAGE_CONNECTION_STRING"],
        os.environ["AZURE_STORAGE_CONTAINER"],
    )

elif "OVH_ENDPOINT_URL" in os.environ:
    storage_manager = OVHBlobManager(
        endpoint_url=os.environ["OVH_ENDPOINT_URL"],
        access_key=os.environ["OVH_ACCESS_KEY"],
        secret_key=os.environ["OVH_SECRET_KEY"],
        bucket_name=os.environ["OVH_BUCKET_NAME"],
    )

else:
    storage_manager = FileStorageManager(os.environ["FILE_STORAGE_DIRECTORY"])
