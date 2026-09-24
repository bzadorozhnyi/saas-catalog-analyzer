from typing import Annotated

from fastapi import Depends

from app.dependency.service import ClassificationServiceDep
from app.use_cases.classify_software import ClassifySoftwareUseCase


def get_classify_software_use_case(service: ClassificationServiceDep) -> ClassifySoftwareUseCase:
    return ClassifySoftwareUseCase(service)


ClassifySoftwareUseCaseDep = Annotated[
    ClassifySoftwareUseCase, Depends(get_classify_software_use_case)
]
