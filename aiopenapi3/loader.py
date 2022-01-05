import abc
import json
from pathlib import Path

from .plugin import Plugins

import yaml


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
            data = yaml.safe_load(data)
        elif file.suffix == ".json":
            data = json.loads(data)
        else:
            raise ValueError(file.name)
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
