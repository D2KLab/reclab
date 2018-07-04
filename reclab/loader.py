import inspect
import sys
from abc import ABC
from abc import abstractmethod

import pandas


def loader_instance(config):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id') and obj.id == config['format']:
            return obj(config['path'], config['sep'], config['skip'])
    raise RuntimeError('No loader ' + config['format'])


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
    def load(self):
        pass


class UIRTLoader(Loader):
    id = "uirt"

    def __init__(self, path, sep, skip):
        self.path = path
        self.sep = sep
        self.skip = skip

    def load(self):
        # Read the input file
        df_input = pandas.read_csv(self.path, names=['userId', 'itemId', 'rating', 'timestamp'],
                                   sep=self.sep, skiprows=self.skip, engine='python')

        # Create a list of ratings
        ratings = []
        for row in df_input.itertuples():
            ratings.append([row[1], row[2], row[3], row[4]])

        return ratings
