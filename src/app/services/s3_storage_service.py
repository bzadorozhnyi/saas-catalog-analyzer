from aiobotocore.client import AioBaseClient


class S3StorageService:
    def __init__(self, client: AioBaseClient, bucket_name: str) -> None:
        self._client = client
        self._bucket_name = bucket_name

    async def generate_presigned_url(self, key: str, expires_in_seconds: int) -> str:
        return await self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket_name, "Key": key},
            ExpiresIn=expires_in_seconds,
        )
