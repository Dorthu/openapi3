import abc
import pathlib
import yaml
import json


class Loader(abc.ABC):
    @abc.abstractmethod
    def load(self, name:str):
        raise NotImplementedError("load")


class FileSystemLoader(Loader):
    def __init__(self, base:str):
        self.base = pathlib.Path(base)

    def load(self, file:str, codec=None):
        file = pathlib.Path(file)
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
        if file.suffix == ".yaml":
            data = yaml.safe_load(data)
        elif file.suffix == ".json":
            data = json.loads(data)
        else:
            raise ValueError(file.name)
        return data
