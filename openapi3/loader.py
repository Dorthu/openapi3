import abc
import pathlib
from pathlib import Path
import yaml
import json


class Loader(abc.ABC):
    @abc.abstractmethod
    def load(self, name:str):
        raise NotImplementedError("load")


class FileSystemLoader(Loader):
    def __init__(self, base:Path):
        assert isinstance(base, Path)
        self.base = base

    def load(self, file:str, codec=None):
        path = self.base / file
        assert path.is_relative_to(self.base)
        data = path.open("rb").read()
        if codec is not None:
            codecs = [codec]
        else:
            codecs = ["ascii","utf-8"]
        for c in codecs:
            try:
                r = data.decode(c)
                break
            except UnicodeError:
                continue
        else:
            raise ValueError("encoding")
        if path.suffix == ".yaml":
            data = yaml.safe_load(data)
        elif path.suffix == ".json":
            data = json.loads(data)
        else:
            raise ValueError(file.name)
        return data
