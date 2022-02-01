import urllib.parse

from yarl import URL


class JSONPointer:
    """
    JavaScript Object Notation (JSON) Pointer

    https://datatracker.ietf.org/doc/html/rfc6901
    """

    @staticmethod
    def decode(part):
        """

        https://swagger.io/docs/specification/using-ref/
        :param part:
        """
        part = urllib.parse.unquote(part)
        part = part.replace("~1", "/")
        return part.replace("~0", "~")


class JSONReference:
    @staticmethod
    def split(url):
        u = URL(url)
        return str(u.with_fragment("")), u.raw_fragment
