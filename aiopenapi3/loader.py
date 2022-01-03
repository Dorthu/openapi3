import abc
import json
from pathlib import Path

import yaml


class Loader(abc.ABC):
    @abc.abstractmethod
    def load(self, name: str):
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
    def dict(cls, file, data):
        if file.suffix == ".yaml":
            data = yaml.safe_load(data)
        elif file.suffix == ".json":
            data = json.loads(data)
        else:
            raise ValueError(file.name)
        return data


class FileSystemLoader(Loader):
    def __init__(self, base: Path):
        assert isinstance(base, Path)
        self.base = base

    def load(self, file: str, codec=None):
        path = self.base / file
        assert path.is_relative_to(self.base)
        data = path.open("rb").read()
        data = self.decode(data, codec)
        data = self.dict(path, data)
        return data
