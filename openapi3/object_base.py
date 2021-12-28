from typing import List, Optional


from pydantic import BaseModel, Field, root_validator, Extra

class ObjectBase(BaseModel):
    """
    The base class for all schema objects.  Includes helpers for common schema-
    related functions.
    """



    _strict: bool
    _path: List[str]
    _raw_element: dict
    _root: object
    _accessed_members: object

    class Config:
        underscore_attrs_are_private = True
        arbitrary_types_allowed = True
        extra = Extra.forbid


class ObjectExtended(ObjectBase):
    extensions: Optional[object] = Field(default=None)

    @root_validator(pre=True)
    def validate_ObjectExtended_extensions(cls, values):
        """ FIXME
        https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#specificationExtensions
        :param values:
        :return: values
        """
        e = dict()
        for k, v in values.items():
            if k.startswith("x-"):
                e[k[2:]] = v
        if len(e):
            for i in e.keys():
                del values[f"x-{i}"]
            if "extensions" in values.keys():
                raise ValueError("extensions")
            values["extensions"] = e

        return values
