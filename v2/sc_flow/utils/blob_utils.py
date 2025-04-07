# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from azure.storage.blob import BlobClient, generate_blob_sas, BlobSasPermissions
import datetime

def create_service_sas_blob(blob_client: BlobClient, account_key: str, num_days=1):
    start_time = datetime.datetime.now(datetime.timezone.utc)
    expiry_time = start_time + datetime.timedelta(days=num_days)

    sas_token = generate_blob_sas(
        account_name=blob_client.account_name,
        container_name=blob_client.container_name,
        blob_name=blob_client.blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry_time,
        start=start_time
    )

    return f"{blob_client.url}?{sas_token}"