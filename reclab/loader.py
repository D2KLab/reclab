import inspect
import sys
from abc import ABC
from abc import abstractmethod

import pandas


def loader_instance(loader_id, *args, **kwargs):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id') and obj.id == loader_id:
            return obj(*args, **kwargs)
    raise RuntimeError('No loader ' + loader_id)


def loader_list():
    loaders = []
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id'):
            loaders.append(obj.id)
    return loaders


class Loader(ABC):

    @abstractmethod
    def id(self):
        pass

    @abstractmethod
    def load(self, file):
        pass


class UIRTLoader(Loader):
    id = "uirt"

    def __init__(self, skip=1):
        self.skip = skip

    def load(self, file):
        # Read the input file
        df_input = pandas.read_csv(file, names=['userId', 'itemId', 'rating', 'timestamp'], skiprows=self.skip)

        # Create a list of ratings
        ratings = []
        for row in df_input.itertuples():
            ratings.append([row[1], row[2], row[3], row[4]])

        return ratings
