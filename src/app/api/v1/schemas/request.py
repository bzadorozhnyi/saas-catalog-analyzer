from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    name: str
    description: str
