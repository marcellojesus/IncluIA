"""Base compartilhada dos schemas Pydantic: API em camelCase (convenção do frontend TS),
código Python em snake_case (convenção idiomática) — via alias automático."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
