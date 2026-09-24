from typing import Annotated

from fastapi import Depends

from app.services.classification_service import ClassificationService


def get_classification_service() -> ClassificationService:
    return ClassificationService()


ClassificationServiceDep = Annotated[ClassificationService, Depends(get_classification_service)]
