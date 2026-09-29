import uuid

from app.core.exceptions import NotFoundException
from app.repositories.report_document_repository import ReportDocumentRepository
from app.services.s3_storage_service import S3StorageService

REPORT_URL_EXPIRES_SECONDS = 15 * 60


class ReportService:
    def __init__(
        self, repository: ReportDocumentRepository, s3_storage_service: S3StorageService
    ) -> None:
        self._repository = repository
        self._s3_storage_service = s3_storage_service

    async def get_download_url(self, request_id: uuid.UUID) -> str:
        document = await self._repository.get_by_request_id(request_id)
        if document is None:
            raise NotFoundException(msg=f"Report for request {request_id} not found")

        return await self._s3_storage_service.generate_presigned_url(
            document.blob_name, REPORT_URL_EXPIRES_SECONDS
        )
