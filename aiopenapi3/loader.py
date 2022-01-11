import abc
import json
from pathlib import Path

from .plugin import Plugins

import yaml

from yaml import SafeLoader

"""
https://stackoverflow.com/questions/34667108/ignore-dates-and-times-while-parsing-yaml
"""


class NoDatesSafeLoader(SafeLoader):
    @classmethod
    def remove_implicit_resolver(cls, tag_to_remove):
        """
        Remove implicit resolvers for a particular tag

        Takes care not to modify resolvers in super classes.

        We want to load datetimes as strings, not dates, because we
        go on to serialise as json which doesn't have the advanced types
        of yaml, and leads to incompatibilities down the track.
        """
        if not "yaml_implicit_resolvers" in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

        for first_letter, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[first_letter] = [
                (tag, regexp) for tag, regexp in mappings if tag != tag_to_remove
            ]


NoDatesSafeLoader.remove_implicit_resolver("tag:yaml.org,2002:timestamp")


class Loader(abc.ABC):
    @abc.abstractmethod
    def load(self, plugins, file: Path, codec=None):
        raise NotImplementedError("load")

    @classmethod
    def decode(cls, data, codec):
        if codec is not None:
            codecs = [codec]
        else:
            codecs = ["ascii", "utf-8"]
        for c in codecs:
            try:
                data = data.decode(c)
                break
            except UnicodeError:
                continue
        else:
            raise ValueError("encoding")
        return data

    @classmethod
    def parse(cls, plugins, file, data):
        if file.suffix == ".yaml":
            data = yaml.load(data, Loader=NoDatesSafeLoader)
        elif file.suffix == ".json":
            data = json.loads(data)
        else:
            raise ValueError(f"{file.name} is not yaml/json")
        return data

    def get(self, plugins, file):
        data = self.load(plugins, file)
        return self.parse(plugins, file, data)


class FileSystemLoader(Loader):
    def __init__(self, base: Path):
        assert isinstance(base, Path)
        self.base = base

    def load(self, plugins: Plugins, file: Path, codec=None):
        assert plugins
        assert isinstance(file, Path)
        path = self.base / file
        assert path.is_relative_to(self.base)
        data = path.open("rb").read()
        data = self.decode(data, codec)
        data = plugins.document.loaded(url=str(file), document=data).document
        return data

    @classmethod
    def parse(cls, plugins, file, data):
        data = Loader.parse(plugins, file, data)
        data = plugins.document.parsed(url=str(file), document=data).document
        return data
