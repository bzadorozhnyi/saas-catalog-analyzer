from typing import Annotated

from fastapi import Depends

from app.dependency.service import (
    CatalogServiceDep,
    ClassificationServiceDep,
    DuplicateDetectionServiceDep,
)
from app.use_cases.classify_software import ClassifySoftwareUseCase
from app.use_cases.create_catalog_item import CreateCatalogItemUseCase
from app.use_cases.find_duplicates import FindDuplicatesUseCase
from app.use_cases.get_catalog_item import GetCatalogItemUseCase
from app.use_cases.list_catalog_items import ListCatalogItemsUseCase


def get_classify_software_use_case(service: ClassificationServiceDep) -> ClassifySoftwareUseCase:
    return ClassifySoftwareUseCase(service)


def get_create_catalog_item_use_case(service: CatalogServiceDep) -> CreateCatalogItemUseCase:
    return CreateCatalogItemUseCase(service)


def get_list_catalog_items_use_case(service: CatalogServiceDep) -> ListCatalogItemsUseCase:
    return ListCatalogItemsUseCase(service)


def get_get_catalog_item_use_case(service: CatalogServiceDep) -> GetCatalogItemUseCase:
    return GetCatalogItemUseCase(service)


def get_find_duplicates_use_case(
    service: DuplicateDetectionServiceDep,
) -> FindDuplicatesUseCase:
    return FindDuplicatesUseCase(service)


ClassifySoftwareUseCaseDep = Annotated[
    ClassifySoftwareUseCase, Depends(get_classify_software_use_case)
]
CreateCatalogItemUseCaseDep = Annotated[
    CreateCatalogItemUseCase, Depends(get_create_catalog_item_use_case)
]
ListCatalogItemsUseCaseDep = Annotated[
    ListCatalogItemsUseCase, Depends(get_list_catalog_items_use_case)
]
GetCatalogItemUseCaseDep = Annotated[
    GetCatalogItemUseCase, Depends(get_get_catalog_item_use_case)
]
FindDuplicatesUseCaseDep = Annotated[
    FindDuplicatesUseCase, Depends(get_find_duplicates_use_case)
]
