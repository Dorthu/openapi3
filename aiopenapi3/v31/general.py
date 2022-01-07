from typing import Optional
from pydantic import Field
from ..v30.general import Reference as Reference30, ExternalDocumentation


class Reference(Reference30):
    summary: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
