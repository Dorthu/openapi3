from .errors import SpecError, ReferenceResolutionError

class ObjectBase:
    """
    The base class for all schema objects.  Includes helpers for common schema-
    related functions.
    """
    __slots__ = ['path','raw_element','_accessed_members','strict','extensions',
                 '_root', '_original_ref']
    required_fields = []

    def __init__(self, path, raw_element, root):
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
        for k in type(self).__slots__:
            if k in ('_spec_errors', 'validation_mode'):
                # allow these two fields to keep their values
                continue
            setattr(self, k, None)

        self.path = path
        self.raw_element = raw_element
        self._root = root

        self._accessed_members = []
        self.strict = False # TODO - add a strict mode that errors if all members were not accessed
        self.extensions = {}

        # parse our own element
        try:
            self._required_fields(*type(self).required_fields)
            self._parse_data()
        except SpecError as e:
            if self._root.validation_mode:
                self._root.log_spec_error(e)
            else:
                raise

        self._parse_spec_extensions() # TODO - this may not be appropriate in all cases

        # TODO - assert that all keys of raw_element were accessed

    def __repr__(self):
        """
        Returns a string representation of the parsed object
        """
        # TODO - why?
        return str(self.__dict__()) # pylint: disable=not-callable

    def __dict__(self):
        """
        Returns this object as a dict, removing all empty keys.  This can be used
        to serialize a spec.
        """
        return {k: getattr(self, k) for k in type(self).__slots__
                if getattr(self, k) is not None}

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
                ', '.join(missing_fields)),
                path=self.path,
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
        raise NotImplementedError("You must implement this method in subclasses!")

    def _get(self, field, object_types, is_list=False, is_map=False):
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
        :param is_list: If true, this should return a List of object of the give
                        types.
        :param is_list: bool
        :param is_map: If true, this must return a :any:`Map` of object of the given
                       types
        :type is_map: bool

        :returns: object_type if given, otherwise the type parsed from the spec
                  file
        """
        self._accessed_members.append(field)

        ret =  self.raw_element.get(field, None)

        try:
            if ret is not None:
                if not isinstance(object_types, list):
                    object_types = [object_types] # maybe don't accept not-lists

                if is_list:
                    if not isinstance(ret, list):
                        raise SpecError('Expected {}.{} to be a list of [{}], got {}'.format(
                            self.get_path, field, ','.join([str(c) for c in object_types]),
                            type(ret)),
                            path=self.path,
                            element=self)
                    ret = self.parse_list(ret, object_types, field)
                elif is_map:
                    if not isinstance(ret, dict):
                        raise SpecError('Expected {}.{} to be a Map of string: [{}], got {}'.format(
                            self.get_path, field, ','.join([str(c) for c in object_types]),
                            type(ret)),
                            path=self.path,
                            element=self)
                    ret = Map(self.path+[field], ret, object_types, self._root)
                else:
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
                                ret = python_type(self.path+[field], ret, self._root)
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
                            self.get_path(), field, ','.join([str(c) for c in object_types]),
                            type(ret)),
                            path=self.path,
                            element=self)
        except SpecError as e:
            if self._root.validation_mode:
                self._root.log_spec_error(e)
                ret = None
            else:
                raise

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

        # TODO - why?
        if typename not in cls._subclass_map: # pylint: disable=no-member
            raise ValueError('ObjectBase has no subclass {}'.format(typename))

        return cls._subclass_map[typename] # pylint: disable=no-member

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

        real_path = self.path[:]
        if field:
            real_path += [field]

        python_types = [ObjectBase.get_object_type(t) if isinstance(t, str) else t
                        for t in object_types]

        result = []
        for i, cur in enumerate(raw_list):
            found_type = False

            for cur_type in python_types:
                if issubclass(cur_type, ObjectBase) and cur_type.can_parse(cur):
                    result.append(cur_type(real_path+[str(i)], cur, self._root))
                    found_type = True
                    continue
                elif isinstance(cur, cur_type):
                    result.append(cur)
                    found_type = True
                    continue

            if not found_type:
                raise SpecError("Could not parse {}.{}, expected to be one of [{}]".format(
                    '.'.join(real_path), i, object_types),
                    path=self.path,
                    element=self)

        return result

    def _resolve_references(self):
        """
        Resolves all reference objects below this object and notes their original
        value was a reference.
        """
        reference_type = ObjectBase.get_object_type('Reference') # don't circular import

        for slot in self.__slots__:
            if slot.startswith('_'):
                # don't parse private members
                continue
            value = getattr(self, slot)

            if isinstance(value, reference_type):
                # we found a reference - attempt to resolve it
                reference_path = value.ref
                if not reference_path.startswith('#/'):
                    raise ReferenceResolutionError('Invalid reference path {}'.format(
                        reference_path),
                        path=self.path,
                        element=self)

                reference_path = reference_path.split('/')[1:]

                try:
                    resolved_value = self._root.resolve_path(reference_path)
                except ReferenceResolutionError as e:
                    # add metadata to the error
                    e.path = self.path
                    e.element = self
                    raise

                resolved_value._original_ref = value # TODO - this will break if
                                                     # multiple things reference
                                                     # the same node.

                setattr(self, slot, resolved_value) # resolved
            elif issubclass(type(value), ObjectBase) or isinstance(value, Map):
                # otherwise, continue resolving down the tree
                value._resolve_references()
            elif isinstance(value, list):
                # if it's a list, resolve its item's references
                resolved_list = []
                for item in value:
                    if isinstance(item, reference_type):
                        # TODO - this is duplicated code
                        reference_path = item.ref.split('/')[1:]

                        try:
                            resolved_value = self._root.resolve_path(reference_path)
                        except ReferenceResolutionError as e:
                            # add metadata to the error
                            e.path = self.path
                            e.element = self
                            raise

                        resolved_value._original_ref = value
                        resolved_list.append(resolved_value)
                    else:
                        if issubclass(type(value), ObjectBase) or isinstance(value, Map):
                            item._resolve_references()
                        resolved_list.append(item)

                setattr(self, slot, resolved_list)


class Map(dict):
    """
    The Map object wraps a python dict and parses its values into the chosen
    type or types.
    """
    __slots__ = ['dct','path','raw_element','_root']

    def __init__(self, path, raw_element, object_types, root):
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
        self._root = root

        python_types = []
        dct = {}

        for t in object_types:
            if isinstance(t, str):
                python_types.append(ObjectBase.get_object_type(t))
            else:
                python_types.append(t)

        for k, v in self.raw_element.items():
            found_type = False

            for t in python_types:
                if issubclass(t, ObjectBase) and t.can_parse(v):
                    dct[k] = t(path+[k], v, self._root)
                    found_type = True
                elif isinstance(v, t):
                    dct[k] = v
                    found_type = True

            if not found_type:
                raise SpecError("Expected {}.{} to be one of [{}], but found {}".format(
                    '.'.join(path), k, object_types, v),
                    path=self.path,
                    element=self)

        self.update(dct)

    def _resolve_references(self):
        """
        This has been added to allow propagation of reference resolution as defined
        in :any:`ObjectBase._resolve_references`.  This implementation simply
        calls the same on all values in this Map.
        """
        reference_type = ObjectBase.get_object_type('Reference')

        for key, value in self.items():
            if isinstance(value, reference_type):
                # TODO - this is repeated code
                # we found a reference - attempt to resolve it
                reference_path = value.ref
                if not reference_path.startswith('#/'):
                    raise ReferenceResolutionError('Invalid reference path {}'.format(
                        reference_path),
                        path=self.path,
                        element=self)

                reference_path = reference_path.split('/')[1:]

                try:
                    resolved_value = self._root.resolve_path(reference_path)
                except ReferenceResolutionError as e:
                    # add metadata to the error
                    e.path = self.path
                    e.element = self
                    raise

                resolved_value._original_ref = value # TODO - this will break if
                                                     # multiple things reference
                                                     # the same node.

                self[key] = resolved_value # resolved
            else:
                value._resolve_references()
