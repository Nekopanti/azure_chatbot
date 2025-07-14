import os
from datetime import datetime, timedelta, timezone
from typing import List
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
from config.config import get_parameter
from common.utils import parse_blob_data
from common.logger import get_logger


logger = get_logger("blob_client")


class AzureStorageBlobClient:
    def __init__(self) -> None:
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                get_parameter("azure.blob.conn_str")
            )
        except KeyError:
            logger.error("AZURE_STORAGE_CONNECTION_STRING not set.")
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING must be set.")

    def download_blob(
        self, container: str, blob_file_name: str, blob_file_path: str, local_dir: str
    ):
        blob_file_full_path = os.path.join(blob_file_path, blob_file_name)
        blob_client = self.blob_service_client.get_blob_client(
            container=container, blob=blob_file_full_path
        )

        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        download_file_local = os.path.join(local_dir, blob_file_name)

        if os.path.exists(download_file_local):
            return download_file_local

        try:
            with open(download_file_local, "wb") as temp_blob:
                download_stream = blob_client.download_blob()
                temp_blob.write(download_stream.readall())
        except Exception as e:
            logger.error(f"Failed to download blob file: {blob_file_full_path}", e)
            raise ValueError(
                f"Cannot download file [{blob_file_full_path}] from Azure Storage! {e}"
            )

        return download_file_local

    def download_blobs_to_local(
        self, container: str, blob_file_path: str, local_dir: str
    ):
        container_client = self.blob_service_client.get_container_client(container)
        blob_list = [
            b.name
            for b in list(container_client.list_blobs(name_starts_with=blob_file_path))
        ]

        download_file_list = []
        try:
            for blob in blob_list:
                file_name = os.path.basename(blob)
                input_file_temp = self.download_blob(
                    container, file_name, blob_file_path, local_dir
                )
                download_file_list.append(input_file_temp)
        except Exception as e:
            logger.error("Failed to download blobs to local.", e)
            raise ValueError(f"Cannot download file from Azure Storage! {e}")

        return download_file_list

    def get_blob_content_list(self, container: str, folder_path: str):
        try:
            container_client = self.blob_service_client.get_container_client(container)
            blob_list = [
                b.name
                for b in list(container_client.list_blobs(name_starts_with=folder_path))
            ]

            data_dict = {}
            file_name_list = []

            for blob in blob_list:
                base_name = os.path.basename(blob)
                result = self.read_azure_blob(container, blob)
                data_dict[base_name] = result or ""
                file_name_list.append(base_name)

            return file_name_list, data_dict

        except Exception as e:
            logger.error("Failed to get blob content list.", e)
            raise ValueError("Cannot get blob data from Azure Storage!")

    def upload_to_blob_storage(
        self, container: str, local_file_path_name: str, blob_path_name: str
    ) -> str:
        blob_client = self.blob_service_client.get_blob_client(
            container=container, blob=blob_path_name
        )

        try:
            with open(local_file_path_name, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
        except Exception as e:
            logger.error(f"Failed to upload file to blob: {local_file_path_name}", e)
            raise ValueError(
                f"Cannot upload file [{local_file_path_name}] to Azure Storage! {e}"
            )

        return blob_client.url

    def batch_upload_to_blob_storage(
        self, container: str, file_list: List[str], server_root_folder: str
    ):
        if len(file_list) > 0:
            for file in file_list:
                local_file_name = os.path.basename(file)
                blob_path_name = f"{server_root_folder}/{local_file_name}"
                try:
                    blob_client = self.blob_service_client.get_blob_client(
                        container=container, blob=blob_path_name
                    )
                    with open(file, "rb") as data:
                        blob_client.upload_blob(data, overwrite=True)
                except Exception as e:
                    logger.error(f"Failed to upload batch file: {file}", e)
                    raise ValueError(
                        f"Cannot upload result file [{file}] to Azure Storage! {e}"
                    )

    def write_file(self, container_name: str, data: str, output_name: str):
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container_name, output_name
            )
            blob_client.upload_blob(data, overwrite=True)
        except Exception as e:
            logger.error(f"Failed to write blob: {output_name}", e)
            raise ValueError(
                f"Failed to upload result file [{output_name}] to Azure Storage! {e}"
            )

    def read_azure_blob(self, container: str, blob_file: str):
        container_client = self.blob_service_client.get_container_client(container)
        try:
            download_stream = container_client.download_blob(blob_file)
            raw_data = download_stream.readall()
            return parse_blob_data(blob_file, raw_data)

        except Exception as e:
            logger.error(f"Failed to read blob file: {blob_file}", e)
            raise ValueError(
                f"Cannot read file [{blob_file}] from Azure Storage! Error: {e}"
            )

    def get_blob_list(self, container: str, folder_path: str):
        container_client = self.blob_service_client.get_container_client(container)
        blob_list = [
            b.name
            for b in list(container_client.list_blobs(name_starts_with=folder_path))
        ]
        return blob_list

    def generate_sas_url(
        self, container_name: str, blob_name: str, expiry_hours: int = 1
    ) -> str:
        try:
            sas_token = generate_blob_sas(
                account_name=self.blob_service_client.account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=self.blob_service_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
            )

            blob_url = self.blob_service_client.get_blob_client(
                container_name, blob_name
            ).url
            return f"{blob_url}?{sas_token}"
        except Exception as e:
            logger.error(f"Failed to generate SAS URL for blob: {blob_name}", e)
            raise ValueError(f"Failed to generate SAS URL for blob '{blob_name}': {e}")

    def generate_batch_sas_urls(
        self, container_name: str, blob_names: list, expiry_hours: int = 1
    ) -> dict:
        try:
            sas_urls = {}

            for blob_name in blob_names:
                sas_token = generate_blob_sas(
                    account_name=self.blob_service_client.account_name,
                    container_name=container_name,
                    blob_name=blob_name,
                    account_key=self.blob_service_client.credential.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
                )

                blob_url = self.blob_service_client.get_blob_client(
                    container_name, blob_name
                ).url
                sas_urls[blob_name] = f"{blob_url}?{sas_token}"

            return sas_urls
        except Exception as e:
            logger.error("Failed to generate batch SAS URLs: ", e)
            raise ValueError(f"Failed to generate batch SAS URLs: {e}")
