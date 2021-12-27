import sys
import datetime
import typing
from typing import List, Optional, Set
import dataclasses

from pydantic import BaseModel, Field, root_validator

from .errors import SpecError, ReferenceResolutionError

IS_PYTHON_2 = False
if sys.version_info[0] == 2:
    IS_PYTHON_2 = True
else:
    # unicode was removed in python3, but we need to support both here, so define
    # it in python 3 only
    unicode = str


def raise_on_unknown_type(parent, field, object_types, found):
    """
    Raises a SpecError describing a situation where an unknown type was given.
    This function attempts to produce as useful an error as possible based on the
    type of types that were expected.

    :param parent: The parent element who was attempting to parse the field
    :type parent: Subclass of ObjectBase
    :param field: The field we were trying to parse
    :type field: str
    :param object_types: The types allowed for this field
    :type object_types: List of str or Class
    :param found: The value that was found (and did not match any expected type)
    :type found: any

    :raises: A SpecError describing the failure
    """
    if len(object_types) == 1:
        expected_type = object_types[0]
        raise SpecError('Expected {}.{} to be of type {}, with required fields {}'.format(
                parent.get_path(),
                field,
                expected_type.__name__,
                sorted(expected_type.required_fields),
            ),
            path=parent._path,
            element=parent,
        )
    elif len(object_types) == 2 and len([c for c in object_types if isinstance(c, str)]) == 2 and "Reference" in object_types:
        # we can give a similar error here as above
        expected_type_str = [c for c in object_types if c != "Reference"][0]
        expected_type = ObjectBase.get_object_type(expected_type_str)
        raise SpecError("Expected {}.{} to be of type {} or Reference, but did not find required fields {} or '$ref'".format(
                parent.get_path(),
                field,
                expected_type_str,
                expected_type._get_required_fields,
            ),
            path=parent._path,
            element=parent,
        )
    print(object_types)
    raise SpecError('Expected {}.{} to be one of [{}], got {}'.format(
                parent.get_path(),
                field,
                ','.join([str(c) for c in object_types],
            ),
            type(found)
        ),
        path=parent._path,
        element=parent,
    )


class ObjectBase(BaseModel):
    """
    The base class for all schema objects.  Includes helpers for common schema-
    related functions.
    """

    extensions: Optional[object] = Field(default=None)


    _strict: bool
    _path: List[str]
    _raw_element: dict
    _root: object
    _accessed_members: object

    class Config:
        underscore_attrs_are_private = True
        arbitrary_types_allowed = True


    @root_validator(pre=True)
    def check_extensions(cls, values):
        """ FIXME
        https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#specificationExtensions
        :param values:
        :return: values
        """
        e = dict()
        for k,v in values.items():
            if k.startswith("x-"):
                e[k[2:]] = v
        if len(e):
            for i in e.keys():
                del values[f"x-{i}"]
            if "extensions" in values.keys():
                raise ValueError("extensions")
            values["extensions"] = e

        return values

    @classmethod
    def get_object_type(cls, typename):
        """
        Introspects the subclasses of this class to decide which to return for
        object_type

        :param object_type: The name of a class that inherits from this class.
                            Must exactly equal type(Class).__name__
        :type object_type: str

        :returns: The Type associated with this name
        :raises ValueError: if no Type with that name was found
        """
        if not hasattr(cls, '_subclass_map'):
            def resolve(c, d):
                r = {t.__name__: t for t in c.__subclasses__()}
                for k,v in r.items():
                    resolve(v, d)
                d.update(r)
                return d
            # generate subclass map on first call
            setattr(cls, '_subclass_map', resolve(cls, {}))

        # TODO - why?
        if typename not in cls._subclass_map:  # pylint: disable=no-member
            raise ValueError('ObjectBase has no subclass {}'.format(typename))

        return cls._subclass_map[typename]  # pylint: disable=no-member

    def get_path(self):
        """
        Get the full path for this element in the spec

        :returns: The path in the spec for this element
        :rtype: str
        """
        return '.'.join(self._path)


    def _resolve_references(self, api):
        """
        Resolves all reference objects below this object and notes their original
        value was a reference.
        """
        # don't circular import

        reference_type = ObjectBase.get_object_type('Reference')
        obj = root = self



        def resolve(obj):
            if isinstance(obj, ObjectBase):
                for slot in filter(lambda x: not x.startswith("_"), obj.__fields_set__):
                    value = getattr(obj, slot)
                    if value is None:
                        continue
                    elif isinstance(value, reference_type):
                        resolved_value = api._resolve_type(root, obj, value)
                        setattr(obj, slot, resolved_value)
                    elif issubclass(type(value), ObjectBase):
                        # otherwise, continue resolving down the tree
                        resolve(value)
                    elif isinstance(value, dict):  # pydantic does not use Map
                        resolve(value)
                    elif isinstance(value, list):
                        # if it's a list, resolve its item's references
                        resolved_list = []
                        for item in value:
                            if isinstance(item, reference_type):
                                resolved_value = api._resolve_type(root, obj, item)
                                resolved_list.append(resolved_value)
                            elif isinstance(item, (ObjectBase, dict, list)):
                                resolve(item)
                                resolved_list.append(item)
                            else:
                                resolved_list.append(item)
                        setattr(obj, slot, resolved_list)
                    elif isinstance(value, (str, int, float, datetime.datetime)):
                        continue
                    else:
                        raise TypeError(type(value))
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, reference_type):
                        if v.ref:
                            obj[k] = api._resolve_type(root, obj, v)
                    elif isinstance(v, (ObjectBase, dict, list)):
                        resolve(v)

        resolve(self)

