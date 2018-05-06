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

    def _get(self, field, object_type, list_type=None):
        """
        Retrieves a value from this object's raw element, and returns None if
        it is not present.  Use :any:`_required_fields` to ensure all required
        fields are present before depending on the output of this method.

        :param field: The field name to retrieve
        :type field: str
        :param object_type: The type of Object that is expected.  This type will
                            be returned if specified.
        :type object_type: str or Type
        :param list_type: The type of elements that should be in this list.  If
                          object_type is not `list`, this is ignored.
        :type list_type: Type

        :returns: object_type if given, otherwise the type parsed from the spec
                  file
        """
        # TODO - accept object_types as a list
        self._accessed_members.append(field)

        ret =  self.raw_element.get(field, None)

        if ret is not None and object_type:
            if isinstance(object_type, str):
                # we're looking up a subclass and returning that
                python_type = ObjectBase.get_object_type(object_type)
                ret = python_type(self.path+[field], ret)
            else:
                # we're validating the datatype of the value in the spec
                if not isinstance(ret, object_type):
                    raise SpecError('Expected {}.{} to be of type {}, got {}'.format(
                        self.get_path(), field, object_type, type(ret)))
                if object_type == list and list_type is not None:
                    # validate that list elements are of the correct type
                    for v in ret:
                        if not isinstance(v, list_type):
                            raise SpecError('Elements of {}.{} must be of type {}, '
                                            'but found {} of type {}'.format(
                                                self.get_path(), field, list_type,
                                                v, type(ret)))

        return ret

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

    def parse_list(self, raw_list, object_type):
        """
        Given a list of Objects, iterates over the list and creates the relevant
        Objects, returning the resulting list.

        :param raw_list: The list to parse
        :type raw_list: list[dict]
        :param object_type: The name of a subclass of ObjectBase to parse the list
                            items to.
        :type object_type: str

        :returns: A list of parsed objects
        :rtype: list[object_type]
        """
        if raw_list is None:
            return None

        result = []
        for i, cur in enumerate(raw_list):
            result.append(ObjectBase.get_object_type(object_type)(
                self.path+[i], cur))

        return result


class Map:
    """
    The Map object wraps a python dict and parses its values into the chosen
    type or types.
    """
    # TODO 
