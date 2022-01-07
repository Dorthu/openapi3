from typing import Optional

from pydantic import BaseModel, Field, root_validator, Extra

HTTP_METHODS = frozenset(["get", "delete", "head", "post", "put", "patch", "trace"])


class ObjectBase(BaseModel):
    """
    The base class for all schema objects.  Includes helpers for common schema-
    related functions.
    """

    class Config:
        underscore_attrs_are_private = True
        arbitrary_types_allowed = False
        extra = Extra.forbid


class ObjectExtended(ObjectBase):
    extensions: Optional[object] = Field(default=None)

    @root_validator(pre=True)
    def validate_ObjectExtended_extensions(cls, values):
        """FIXME
        https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#specification-extensions
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


from .json import JSONPointer
from .errors import ReferenceResolutionError
import datetime


class RootBase:
    @staticmethod
    def resolve(api, root, obj, _PathItem, _Reference):
        if isinstance(obj, ObjectBase):
            for slot in filter(lambda x: not x.startswith("_"), obj.__fields_set__):
                value = getattr(obj, slot)
                if value is None:
                    continue

                if isinstance(obj, _PathItem) and slot == "ref":
                    ref = _Reference.construct(ref=value)
                    ref._target = api.resolve_jr(root, obj, ref)
                    setattr(obj, slot, ref)

                value = getattr(obj, slot)
                if isinstance(value, _Reference):
                    value._target = api.resolve_jr(root, obj, value)
                #                        setattr(obj, slot, resolved_value)
                elif issubclass(type(value), ObjectBase):
                    # otherwise, continue resolving down the tree
                    RootBase.resolve(api, root, value, _PathItem, _Reference)
                elif isinstance(value, dict):  # pydantic does not use Map
                    RootBase.resolve(api, root, value, _PathItem, _Reference)
                elif isinstance(value, list):
                    # if it's a list, resolve its item's references
                    for item in value:
                        if isinstance(item, _Reference):
                            item._target = api.resolve_jr(root, obj, item)
                        elif isinstance(item, (ObjectBase, dict, list)):
                            RootBase.resolve(api, root, item, _PathItem, _Reference)
                elif isinstance(value, (str, int, float, datetime.datetime)):
                    continue
                else:
                    raise TypeError(type(value))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, _Reference):
                    if v.ref:
                        v._target = api.resolve_jr(root, obj, v)
                elif isinstance(v, (ObjectBase, dict, list)):
                    RootBase.resolve(api, root, v, _PathItem, _Reference)

    def _resolve_references(self, api):
        """
        Resolves all reference objects below this object and notes their original
        value was a reference.
        """
        # don't circular import

        root = self

        RootBase.resolve(api, self, self, None, None)
        raise NotImplementedError("specific")

    def resolve_jp(self, jp):
        """
        Given a $ref path, follows the document tree and returns the given attribute.

        :param jp: The path down the spec tree to follow
        :type jp: str #/foo/bar

        :returns: The node requested
        :rtype: ObjectBase
        :raises ValueError: if the given path is not valid
        """
        path = jp.split("/")[1:]
        node = self

        for part in path:
            part = JSONPointer.decode(part)
            if isinstance(node, dict):
                if part not in node:  # pylint: disable=unsupported-membership-test
                    raise ReferenceResolutionError(f"Invalid path {path} in Reference")
                node = node.get(part)
            else:
                if not hasattr(node, part):
                    raise ReferenceResolutionError(f"Invalid path {path} in Reference")
                node = getattr(node, part)

        return node


from typing import List, Dict
from .model import Model


class DiscriminatorBase:
    pass


class SchemaBase:
    #    @lru_cache
    def get_type(self, names: List[str] = None, discriminators: List[DiscriminatorBase] = None):
        return Model.from_schema(self, names, discriminators)

    def model(self, data: Dict):
        """
        Generates a model representing this schema from the given data.

        :param data: The data to create the model from.  Should match this schema.
        :type data: dict

        :returns: A new :any:`Model` created in this Schema's type from the data.
        :rtype: self.get_type()
        """
        if self.type in ("string", "number"):
            assert len(self.properties) == 0
            # more simple types
            # if this schema represents a simple type, simply return the data
            # TODO - perhaps assert that the type of data matches the type we
            # expected
            return data
        elif self.type == "array":
            return [self.items.get_type().parse_obj(i) for i in data]
        else:
            return self.get_type().parse_obj(data)


class ParameterBase:
    pass
