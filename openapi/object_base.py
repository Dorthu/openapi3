from .errors import SpecError

class ObjectBase:
    """
    The base class for all schema objects.  Includes helpers for common schema-
    related functions.
    """
    __slots__ = ['path','raw_element','_accessed_members','strict']

    def __init__(self, path, raw_element):
        """
        Creates a new Object for a OpenAPI schema with a reference to its own
        path in the schema.
        """
        self.path = path
        self.raw_element = raw_element

        self._accessed_members = []
        self.strict = False # TODO

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

    def _get(self, field, object_type=None):
        """
        Retrieves a value from this object's raw element, and returns None if
        it is not present.  Use :any:`_required_fields` to ensure all required
        fields are present before depending on the output of this method.

        :param field: The field name to retrieve
        :type field: str
        :param object_type: The type of Object that is expected.  This type will
                            be returned if specified.
        :type object_type: str or Type

        :returns: object_type if given, otherwise the type parsed from the spec
                  file
        """
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

        return ret

    def _parse_spec_extensions(self):
        """
        TODO - parse vendor extensions
        """


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
            raise ValueError('ObjectBase has not subclass {}'.format(typename))

        return cls._subclass_map[typename]

    def get_path(self):
        """
        Get the full path for this element in the spec

        :returns: The path in the spec for this element
        :rtype: str
        """
        return '.'.join(self.path)
