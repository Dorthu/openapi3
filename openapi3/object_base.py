import sys
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


def _asdict(x):
    if hasattr(x, '__getstate__'):
        return x.__getstate__()
    elif isinstance(x, dict):
        return {k: _asdict(v) for k, v in x.items()}
    elif isinstance(x, (list, tuple, set)):
        return x.__class__(_asdict(y) for y in x)
    else:
        return x


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

def isoptional(x):
    pass

from pydantic.fields import ModelField

class ObjectBase(BaseModel):
    """
    The base class for all schema objects.  Includes helpers for common schema-
    related functions.
    """
#    __slots__ = ['path', 'raw_element', '_accessed_members', 'strict', '_root',
#                 'extensions', '_original_ref']

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
        e = dict()
        for k,v in values.items():
            if k.startswith("x-"):
                e[k[2]] = v
        if len(e):
            for i in e.keys():
                del values[f"x-{i}"]
            if "extensions" in values.keys():
                raise ValueError("extensions")
            values["extensions"] = e

        return values

    @property
    def _get_required_fields(self):
        return set(map(lambda y: y.alias, filter(lambda z: z.required is True, self.__fields__.values())))

    @classmethod
    def create(cls, path, raw_element, root, obj=None):
        """
        Creates a new Object for a OpenAPI schema with a reference to its own
        path in the schema.

        :param path: The path to this element in the spec.
        :type path: list[str]
        :param raw_element: The raw element parsed from the spec that this object
                            is parsing.
        :type raw_element: dict
        :param root: The root of the spec, for reference
        :type root: OpenAPI
        """
        # init empty slots
        obj = obj or cls(raw_element)
#        for k in type(obj).__slots__:
#            if k in ('_spec_errors', 'validation_mode'):
#                # allow these two fields to keep their values
#                continue
#            setattr(obj, k, None)

        obj._path = path
        obj._raw_element = raw_element
        obj._root = root

        obj._accessed_members = []
        obj.extensions = {}

        # TODO - add strict mode that errors if all members were not accessed
        obj._strict = False

        # parse our own element
        try:
            obj._required_fields(obj._get_required_fields)
            obj._parse_data()
        except SpecError as e:
            if obj._root._validation_mode:
                obj._root.log_spec_error(e)
            else:
                raise

        # TODO - this may not be appropriate in all cases
        obj._parse_spec_extensions()

        # TODO - assert that all keys of raw_element were accessed

        return obj

#    def __repr__(self):
#        """
#        Returns a string representation of the parsed object
#        """
#        # TODO - why?
#        return "<{} {}>".format(type(self), self._path)

    def __getstate__(self):
        """
        Returns this object as a dict, removing all empty keys.  This can be used
        to serialize a spec.

        Allows pickling objects by returning a dict of all slotted values.
        """
        return _asdict({
            k: getattr(self, k) for k in type(self).__slots__ if hasattr(self, k)
        })

    def __setstate__(self, state):
        """
        Allows unpickling objects
        """
        for k, v in state.items():
            setattr(self, k, v)

    def _required_fields(self, fields: Set):
        """
        Given a list of require fields for this object, raises a SpecError if any
        of the fields do not exist.

        :param *fields: A list of fields to ensure exist in this object
        :type *fields: str

        :raises SpecError: if any of the required fields are not present.
        """
        missing_fields = fields - set(self._raw_element)

        if missing_fields:
            raise SpecError('Missing required fields: {}'.format(
                ', '.join(missing_fields)),
                path=self._path,
                element=self)

    def _parse_data(self):
        """
        Parses the raw_element into this object.  This is not implemented here,
        but is called in the constructor and _must_ be implemented in all
        subclasses.

        An implementation of this method should use :any:`_get` to retrieve
        values from the raw_element, which has the side-effect of noting that
        those members were accessed.  After this is executed, spec extensions
        are parsed and then an assertion is made that all keys in the
        raw_element were accessed - if not, the schema is considered invalid.
        """
        self.__class__.parse_obj(self._raw_element)

    def _get(self, field, object_type):
        """
        Retrieves a value from this object's raw element, and returns None if
        it is not present.  Use :any:`_required_fields` to ensure all required
        fields are present before depending on the output of this method.

        :param field: The field name to retrieve
        :type field: str
        :param object_type: The type
        :type object_type: typing
        :returns: object_type if given, otherwise the type parsed from the spec
                  file
        """
        self._accessed_members.append(field)
        c = object_type
        ret = self._raw_element.get(field, None)
        if ret is None:
            return None

        try:
            types = self.types_of(object_type)
            origin = typing.get_origin(object_type) or object_type

            # decapsule Optional
            if origin == typing.Union:
                args = typing.get_args(object_type)
                if len(args) == 2 and args[1] == None.__class__:
                    object_type = args[0]
                    origin = typing.get_origin(args[0]) or origin


            if origin == list:
                if not isinstance(ret, list):
                    raise SpecError('Expected {}.{} to be a list of {}, got {}'.format(
                        self.get_path, field, object_type,
                        type(ret)),
                        path=self._path,
                        element=self)
                ret = self.parse_list(ret, object_type, field)
            elif origin == Map:
                if not isinstance(ret, dict):
                    raise SpecError('Expected {}.{} to be a Map of string: [{}], got {}'.format(
                        self.get_path, field, object_type,
                        type(ret)),
                        path=self._path,
                        element=self)
                ret = Map(self._path + [field], ret, object_type, self._root)
            else:
                accepts_string = False
                for t in types:
                    if t == typing.Any:
                        break

                    if t == str:
                        accepts_string = True
                        continue

                    if issubclass(t, ObjectBase):
                        # we were given the name of a subclass of ObjectBase,
                        # attempt to parse ret as that type
                        python_type = t #ObjectBase.get_object_type(t)

                        if python_type.can_parse(ret):
                            ret = python_type.create(self._path + [field], ret, self._root)
                            break

                    elif isinstance(ret, t):
                        # it's already the type we need
                        break
                else:
                    if accepts_string and isinstance(ret, str):
                        pass
                    else:
                        raise_on_unknown_type(self, field, types, ret)
        except SpecError as e:
            if self._root._validation_mode:
                self._root.log_spec_error(e)
                ret = None
            else:
                raise

        return ret

    @classmethod
    def key_contained(cls, key, target_list):
        """
        Returns whether the key is contained in the given list or not.
        We use this specific function as to prevent usage of keywords we add "_"
        to several parameters, and we still want to validate those parameters
        """
        if key.endswith("_"):
            extra_key = key[:-1]
        else:
            extra_key = key + "_"
        return key in target_list or extra_key in target_list

    @classmethod
    def can_parse(cls, dct):
        """
        Returns True if this class can parse the given dict.  This is based on
        the __slots__ and required_fields of the class, and the keys of the dict.
        This is intended to be used when an element may be one of a number of
        allowed Object types - each type should independently consider if it
        can parse the given element, and the first to report that it can should
        be used.

        :param dct: The dict to consider.
        :type dct: dict

        :returns: True if this class can parse dct into an instance of itself,
                  otherwise False
        :rtype: bool
        """
        # if this isn't a dict, the spec is dreadfully wrong (and since no type
        # will be able to parse this value, an appropriate error is returned)
        if not isinstance(dct, dict):
            return False
        fields = set(map(lambda x: x.name.rstrip("_"), dataclasses.fields(cls)))
        # ensure that the dict's keys are valid in our slots

        keys = [key for key in filter(lambda x: not x.startswith("x-"), dct.keys())]
        keys = set(keys)

        if keys - fields:
            return False

        if cls._get_required_fields - keys:
            return False

        return True

    def _parse_spec_extensions(self):
        """
        Examines the keys of this Object's raw_element and collects any `Specification
        Extensions`_ into the extensions attribute of this Object.

        .. _Specification Extensions: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#specificationExtensions
        """
        for k, v in self._raw_element.items():
            if k.startswith('x-'):
                self.extensions[k[2:]] = v
                self._accessed_members.append(k)

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


    @staticmethod
    def _resolve_type(root, obj, value):
        # we found a reference - attempt to resolve it
        reference_path = value.ref
        if not reference_path.startswith('#/'):
            raise ReferenceResolutionError('Invalid reference path {}'.format(
                reference_path),
                path=obj._path,
                element=obj)

        reference_path = reference_path.split('/')[1:]

        try:
            resolved_value = root.resolve_path(reference_path)
        except ReferenceResolutionError as e:
            # add metadata to the error
#            e.path = obj._path
            e.element = obj
            raise

        # FIXME - will break if multiple things reference the same
        # node
#        resolved_value._original_ref = value
        return resolved_value

    def _resolve_references(self, root):
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
                        resolved_value = ObjectBase._resolve_type(root, obj, value)
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
                                resolved_value = ObjectBase._resolve_type(root, obj, item)
                                resolved_list.append(resolved_value)
                            elif isinstance(item, (ObjectBase, dict, list)):
                                resolve(item)
                                resolved_list.append(item)
                            else:
                                resolved_list.append(item)
                        setattr(obj, slot, resolved_list)
                    elif isinstance(value, (str, int, float)):
                        continue
                    else:
                        raise TypeError(type(value))
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, reference_type):
                        if v.ref:
                            obj[k] = ObjectBase._resolve_type(root, obj, v)
                    elif isinstance(v, (ObjectBase, dict, list)):
                        resolve(v)

        resolve(self)

