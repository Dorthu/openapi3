from .errors import SpecError

class ObjectBase:
    """
    The base class for all schema objects.  Includes helpers for common schema-
    related functions.
    """
    __slots__ = ['path','raw_element','_accessed_members','strict','extensions']
    required_fields = []

    def __init__(self, path, raw_element):
        """
        Creates a new Object for a OpenAPI schema with a reference to its own
        path in the schema.
        """
        self.path = path
        self.raw_element = raw_element

        self._accessed_members = []
        self.strict = False # TODO - add a strict mode that errors if all members were not accessed
        self.extensions = {}

        # parse our own element
        self._required_fields(*type(self).required_fields)
        self._parse_data()

        self._parse_spec_extensions() # TODO - this may not be appropriate in all cases

        # TODO - assert that all keys of raw_element were accessed

    def _required_fields(self, *fields):
        """
        Given a list of require fields for this object, raises a SpecError if any
        of the fields do not exist.

        :param *fields: A list of fields to ensure exist in this object
        :type *fields: str

        :raises SpecError: if any of the required fields are not present.
        """
        missing_fields = []
        for field in fields:
            if field not in self.raw_element:
                missing_fields.append(field)

        if missing_fields:
            raise SpecError("Missing required fields: {}".format(
                ', '.join(missing_fields)))

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
        raise NotImplemented("You must implement this method in subclasses!")

    def _get(self, field, object_types, list_type=None):
        """
        Retrieves a value from this object's raw element, and returns None if
        it is not present.  Use :any:`_required_fields` to ensure all required
        fields are present before depending on the output of this method.

        :param field: The field name to retrieve
        :type field: str
        :param object_types: The types of Objects that are accepted.  One of
                             these types will be returned, or the spec will be
                             considered invalid.
        :type object_types: list[str or Type]
        :param list_type: The type of elements that should be in this list.  If
                          object_type is not `list`, this is ignored.
        :type list_type: Type

        :returns: object_type if given, otherwise the type parsed from the spec
                  file
        """
        self._accessed_members.append(field)

        ret =  self.raw_element.get(field, None)

        if ret is not None:
            if not isinstance(object_types, list):
                object_types = [object_types] # maybe don't accept not-lists

            accepts_string = str in object_types
            found_type = False

            for t in object_types:
                if t == str:
                    continue # try to parse everything else first

                if isinstance(t, str):
                    # we were given the name of a subclass of ObjectBase,
                    # attempt to parse ret as that type
                    python_type = ObjectBase.get_object_type(t)

                    if python_type.can_parse(ret):
                        ret = python_type(self.path+[field], ret)
                        found_type = True
                        break
                elif isinstance(ret, t):
                    # it's already the type we need
                    found_type = True
                    break

            if not found_type:
                if accepts_string and isinstance(ret, str):
                    found_type = True

            if not found_type:
                raise SpecError('Expected {}.{} to be one of [{}], got {}'.format(
                    self.get_path(), field, ','.join(object_types), type(ret)))

            # TODO - this should support multiple types too
            if isinstance(ret, list) and list_type is not None:
                # validate that list elements are of the correct type
                for v in ret:
                    if not isinstance(v, list_type):
                        raise SpecError('Elements of {}.{} must be of type {}, '
                                        'but found {} of type {}'.format(
                                            self.get_path(), field, list_type,
                                            v, type(ret)))

        return ret

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
        # first, ensure that the dict's keys are valid in our slots
        for key in dct.keys():
            if key.startswith('x-'):
                # ignore spec extensions
                continue

            if key not in cls.__slots__:
                # it has something we don't - probably not a match
                return False

        # then, ensure that all required fields are present
        for key in cls.required_fields:
            if key not in dct:
                # it doesn't have everything we need - probably not a match
                return False

        return True

    def _parse_spec_extensions(self):
        """
        Examines the keys of this Object's raw_element and collects any `Specification
        Extensions`_ into the extensions attribute of this Object.

        .. _Specification Extensions: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#specificationExtensions
        """
        for k, v in self.raw_element.items():
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
            # generate subclass map on first call
            setattr(cls, '_subclass_map', {t.__name__: t for t in cls.__subclasses__()})

        if typename not in cls._subclass_map:
            raise ValueError('ObjectBase has no subclass {}'.format(typename))

        return cls._subclass_map[typename]

    def get_path(self):
        """
        Get the full path for this element in the spec

        :returns: The path in the spec for this element
        :rtype: str
        """
        return '.'.join(self.path)

    def parse_list(self, raw_list, object_types, field=None):
        """
        Given a list of Objects, iterates over the list and creates the relevant
        Objects, returning the resulting list.

        :param raw_list: The list to parse
        :type raw_list: list[dict]
        :param object_types: A list of subclass names to attempt to parse the
                             objects to.  The list does not need to consist of
                             only one of these types.
        :type object_type: list[str]
        :param field: The field to append to self.get_path() when determining path
                      for created objects.
        :type field: str

        :returns: A list of parsed objects
        :rtype: list[object_type]
        """
        if raw_list is None:
            return None

        if not isinstance(object_types, list):
            object_types = [object_types]

        real_path = self.path
        if field:
            real_path += [field]

        python_types = [ObjectBase.get_object_type(t) for t in object_types]

        result = []
        for i, cur in enumerate(raw_list):
            found_type = False

            for cur_type in python_types:
                if cur_type.can_parse(cur):
                    result.append(cur_type(real_path+[str(i)], cur))
                    found_type = True
                    continue

            if not found_type:
                raise SpecError("Could not parse {}.{}, expected to be one of [{}]".format(
                    '.'.join(real_path), i, object_types))

        return result


class Map(dict):
    """
    The Map object wraps a python dict and parses its values into the chosen
    type or types.
    """
    __slots__ = ['dct','path','raw_element']

    def __init__(self, path, raw_element, object_types):
        """
        Creates a dict containing the parsed objects from the raw element

        :param path: The path to this Map in the spec.
        :type path: list
        :param raw_element: The raw spec data for this map.  The keys must all
                            be strings.
        :type raw_element: dict
        :param object_types: A list of strings accepted by
                             :any:`ObjectBase.get_object_type`, or the python
                             types to parse.
        :type object_types: list[str or Type]
        """
        self.path = path
        self.raw_element = raw_element

        python_types = []
        dct = {}

        for t in object_types:
            if isinstance(t, str):
                python_types.append(ObjectBase.get_object_type(t))
            else:
                python_types.append(t)

        for k, v in self.raw_element.items():
            for t in python_types:
                if issubclass(t, ObjectBase) and t.can_parse(v):
                    dct[k] = t(path+[k], v)
                elif isinstance(v, t):
                    dct[k] = v
                else:
                    raise SpecError("Expected {}.{} to be one of [{}], but found {}".format(
                        '.'.join(path), k, object_types, v))

        self.update(dct)
