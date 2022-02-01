from typing import Optional, Any

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
    extensions: Optional[Any] = Field(default=None)

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

from typing import Dict, Any


class PathsBase(ObjectBase):
    __root__: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from pydantic import Extra

        extra = Extra.allow

    @property
    def extensions(self):
        return self._extensions

    def __getitem__(self, item):
        return self._paths[item]

    def items(self):
        return self._paths.items()

    def values(self):
        return self._paths.values()


class RootBase:
    @staticmethod
    def resolve(api, root, obj, _PathItem, _Reference):
        if isinstance(obj, ObjectBase):
            for slot in filter(lambda x: not x.startswith("_"), obj.__fields_set__):
                value = getattr(obj, slot)
                if value is None:
                    continue

                # v3.1 - Schema $ref
                if isinstance(value, SchemaBase):
                    r = getattr(value, "ref", None)
                    if r is not None:
                        value = _Reference.construct(ref=r)
                        setattr(obj, slot, value)

                """
                ref fields embedded in objects -> replace the object with a Reference object

                PathItem Ref is ambigous
                https://github.com/OAI/OpenAPI-Specification/issues/2635
                """
                if isinstance(obj, _PathItem) and slot == "ref":
                    ref = _Reference.construct(ref=value)
                    ref._target = api.resolve_jr(root, obj, ref)
                    setattr(obj, slot, ref)

                value = getattr(obj, slot)

                if isinstance(value, PathsBase):
                    value.items()
                    value = value._paths

                if isinstance(value, (str, int, float)):  # , datetime.datetime, datetime.date)):
                    continue
                elif isinstance(value, _Reference):
                    value._target = api.resolve_jr(root, obj, value)
                elif issubclass(type(value), ObjectBase) or isinstance(value, (dict, list)):
                    # otherwise, continue resolving down the tree
                    RootBase.resolve(api, root, value, _PathItem, _Reference)
                else:
                    raise TypeError(type(value))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, _Reference):
                    if v.ref:
                        v._target = api.resolve_jr(root, obj, v)
                elif isinstance(v, (ObjectBase, dict, list)):
                    RootBase.resolve(api, root, v, _PathItem, _Reference)
        elif isinstance(obj, list):
            # if it's a list, resolve its item's references
            for item in obj:
                if isinstance(item, _Reference):
                    item._target = api.resolve_jr(root, obj, item)
                elif isinstance(item, (ObjectBase, dict, list)):
                    RootBase.resolve(api, root, item, _PathItem, _Reference)

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

            if isinstance(node, PathsBase):  # forward
                node = node._paths  # will be dict

            if isinstance(node, dict):
                if part not in node:  # pylint: disable=unsupported-membership-test
                    raise ReferenceResolutionError(f"Invalid path {path} in Reference")
                node = node.get(part)
            elif isinstance(node, list):
                node = node[int(part)]
            elif isinstance(node, ObjectBase):
                if part == "schema":
                    part = "schema_"
                if not hasattr(node, part):
                    raise ReferenceResolutionError(f"Invalid path {path} in Reference")
                node = getattr(node, part)
            else:
                raise TypeError(node)

        return node


from typing import List, Dict
from .model import Model


class DiscriminatorBase:
    pass


class SchemaBase:
    def set_type(self, names: List[str] = None, discriminators: List[DiscriminatorBase] = None):
        self._model_type = Model.from_schema(self, names, discriminators)
        return self._model_type

    def get_type(self, names: List[str] = None, discriminators: List[DiscriminatorBase] = None):
        try:
            return self._model_type
        except AttributeError:
            return self.set_type(names, discriminators)

    def model(self, data: Dict):
        """
        Generates a model representing this schema from the given data.

        :param data: The data to create the model from.  Should match this schema.
        :type data: dict

        :returns: A new :any:`Model` created in this Schema's type from the data.
        :rtype: self.get_type()
        """
        if self.type in ("string", "number", "boolean", "integer"):
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


class ReferenceBase:
    pass


class ParameterBase:
    pass
