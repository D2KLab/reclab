import inspect
import sys
from abc import ABC
from abc import abstractmethod


def loader_instance(config):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id') and obj.id == config['format']:
            return obj(config['path'], config['sep'], config['skip'])
    raise RuntimeError('No loader ' + config['format'])


def loader_list():
    loaders = []
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id') and isinstance(obj.id, str):
            loaders.append(obj.id)
    return loaders


class Loader(ABC):

    @property
    @abstractmethod
    def id(self):
        pass

    @abstractmethod
    def load(self):
        pass


class UIRLoader(Loader):
    id = "uir"

    def __init__(self, path, sep, skip):
        self.path = path
        self.sep = sep
        self.skip = skip

    def load(self):
        ratings = []
        users = {}
        user_counter = 0
        items = {}
        item_counter = 0

        # Read the input file
        with open(self.path) as fp:
            for counter, line in enumerate(fp.readlines()):
                # Ignore the first lines
                if counter < self.skip:
                    continue

                row = line.replace("\"", "").split(self.sep)

                if row[0] not in users:
                    users[row[0]] = user_counter
                    user_counter += 1

                user = users[row[0]]

                if row[1] not in items:
                    items[row[1]] = item_counter
                    item_counter += 1

                item = items[row[1]]

                if row[2].find(".") >= 0:
                    value = float(row[2])
                else:
                    value = int(row[2])

                ratings.append([user, item, value, counter])

        return ratings


class UIRTLoader(Loader):
    id = "uirt"

    def __init__(self, path, sep, skip):
        self.path = path
        self.sep = sep
        self.skip = skip

    def load(self):
        ratings = []
        users = {}
        user_counter = 0
        items = {}
        item_counter = 0

        # Read the input file
        with open(self.path) as fp:
            for counter, line in enumerate(fp.readlines()):
                # Ignore the first lines
                if counter < self.skip:
                    continue

                row = line.replace("\"", "").split(self.sep)

                if row[0] not in users:
                    users[row[0]] = user_counter
                    user_counter += 1

                user = users[row[0]]

                if row[1] not in items:
                    items[row[1]] = item_counter
                    item_counter += 1

                item = items[row[1]]

                if row[2].find(".") >= 0:
                    value = float(row[2])
                else:
                    value = int(row[2])

                timestamp = int(row[3])

                ratings.append([user, item, value, timestamp])

        return ratings
