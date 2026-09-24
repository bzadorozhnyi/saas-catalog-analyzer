import asyncio

from app.ai.embeddings import embedding_client
from app.core.observability import configure_logfire
from app.db.session import async_session_factory
from app.models.category import SoftwareCategory
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.embedding_cache_repository import EmbeddingCacheRepository
from app.services.catalog_service import CatalogService
from app.services.embedding_service import EmbeddingService

SEED_ITEMS: list[tuple[str, str, SoftwareCategory]] = [
    (
        "Slack",
        "Team messaging and chat app for workplace communication",
        SoftwareCategory.COMMUNICATION,
    ),
    (
        "Microsoft Teams",
        "Chat, video calls and collaboration hub built into Microsoft 365",
        SoftwareCategory.COMMUNICATION,
    ),
    (
        "Discord",
        "Voice, video and text chat platform originally built for gaming communities",
        SoftwareCategory.COMMUNICATION,
    ),
    (
        "Jira",
        "Issue tracking and agile project management tool from Atlassian",
        SoftwareCategory.PROJECT_MANAGEMENT,
    ),
    (
        "Linear",
        "Fast, keyboard-driven issue tracker for software teams",
        SoftwareCategory.PROJECT_MANAGEMENT,
    ),
    (
        "Asana",
        "Task and project management tool for teams to plan and track work",
        SoftwareCategory.PROJECT_MANAGEMENT,
    ),
    (
        "Notion",
        "All-in-one workspace for notes, docs and knowledge base",
        SoftwareCategory.PROJECT_MANAGEMENT,
    ),
    (
        "Confluence",
        "Team workspace and wiki for documentation from Atlassian",
        SoftwareCategory.PROJECT_MANAGEMENT,
    ),
    (
        "Coda",
        "Doc that blends spreadsheets, databases and project tracking",
        SoftwareCategory.PROJECT_MANAGEMENT,
    ),
    (
        "QuickBooks",
        "Small business accounting software for invoicing and bookkeeping",
        SoftwareCategory.ACCOUNTING,
    ),
    (
        "Xero",
        "Cloud-based accounting software for small and medium businesses",
        SoftwareCategory.ACCOUNTING,
    ),
    (
        "FreshBooks",
        "Invoicing and accounting software for freelancers and small businesses",
        SoftwareCategory.ACCOUNTING,
    ),
    (
        "Figma",
        "Collaborative interface design tool for UI/UX teams",
        SoftwareCategory.DESIGN,
    ),
    (
        "Sketch",
        "Vector-based digital design toolkit for Mac",
        SoftwareCategory.DESIGN,
    ),
    (
        "Adobe XD",
        "UI/UX design and prototyping tool from Adobe",
        SoftwareCategory.DESIGN,
    ),
    (
        "Okta",
        "Identity and access management platform for single sign-on",
        SoftwareCategory.SECURITY,
    ),
    (
        "OneLogin",
        "Cloud-based identity and access management solution",
        SoftwareCategory.SECURITY,
    ),
    (
        "Auth0",
        "Developer-focused authentication and authorization platform",
        SoftwareCategory.SECURITY,
    ),
    (
        "BambooHR",
        "HR software for hiring, onboarding and employee data management",
        SoftwareCategory.HR,
    ),
    (
        "Gusto",
        "Payroll, benefits and HR platform for small businesses",
        SoftwareCategory.HR,
    ),
    (
        "Workday",
        "Enterprise HR and finance management cloud platform",
        SoftwareCategory.HR,
    ),
    (
        "Salesforce",
        "Customer relationship management platform for sales teams",
        SoftwareCategory.SALES,
    ),
    (
        "HubSpot",
        "CRM and marketing platform for inbound sales and marketing",
        SoftwareCategory.SALES,
    ),
    (
        "Pipedrive",
        "Sales-focused CRM built around visual pipeline management",
        SoftwareCategory.SALES,
    ),
    (
        "GitHub",
        "Git-based code hosting and collaboration platform",
        SoftwareCategory.DEVELOPER_TOOLS,
    ),
    (
        "GitLab",
        "DevOps platform with Git repository hosting and CI/CD",
        SoftwareCategory.DEVELOPER_TOOLS,
    ),
    (
        "Bitbucket",
        "Git repository hosting with built-in CI/CD from Atlassian",
        SoftwareCategory.DEVELOPER_TOOLS,
    ),
]


async def seed() -> None:
    async with async_session_factory() as session:
        repository = CatalogRepository(session)
        embedding_service = EmbeddingService(embedding_client, EmbeddingCacheRepository(session))
        service = CatalogService(session, repository, embedding_service)

        for name, description, category in SEED_ITEMS:
            existing = await repository.get_by_name(name)
            if existing is not None:
                print(f"skip (exists): {name}")
                continue

            await service.create_item(name=name, description=description, category=category)
            print(f"created: {name}")


if __name__ == "__main__":
    configure_logfire()
    asyncio.run(seed())
