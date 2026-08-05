from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for every API schema: snake_case in Python, camelCase over the wire."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ReviseRequest(CamelModel):
    instruction: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
