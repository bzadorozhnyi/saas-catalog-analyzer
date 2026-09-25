import json
from typing import Any

from aiobotocore.client import AioBaseClient


class SQSService:
    def __init__(self, client: AioBaseClient, queue_url: str) -> None:
        self._client = client
        self._queue_url = queue_url

    async def send_message(self, body: dict[str, Any]) -> None:
        await self._client.send_message(QueueUrl=self._queue_url, MessageBody=json.dumps(body))

    async def receive_messages(self, max_messages: int, wait_seconds: int) -> list[dict[str, Any]]:
        response = await self._client.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_seconds,
        )
        return response.get("Messages", [])

    async def delete_message(self, receipt_handle: str) -> None:
        await self._client.delete_message(QueueUrl=self._queue_url, ReceiptHandle=receipt_handle)
