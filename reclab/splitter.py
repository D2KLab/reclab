import inspect
import random
import sys
from abc import ABC
from abc import abstractmethod


def splitter_instance(config):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id') and obj.id == config['splitter']:
            return obj(config['seed'], config['test_size'])
    raise RuntimeError('No splitter ' + config['splitter'])


def splitter_list():
    splitters = {}
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id') and isinstance(obj.id, str):
            splitters[obj.id] = {'name': obj.name,
                                 'desc': obj.desc}
    return splitters


class Splitter(ABC):

    def __init__(self, seed, test_size):
        self.seed = seed
        if test_size < 0 or test_size > 1:
            raise ValueError('Test size must be a number between 0 and 1')
        self.test_size = test_size

    @property
    @abstractmethod
    def id(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def desc(self):
        pass

    @abstractmethod
    def split(self, ratings):
        pass


class RandomSplitter(Splitter):
    id = "random"
    name = "Random"
    desc = "Split all the ratings at random."

    def split(self, ratings):
        training_set = []
        test_set = []

        # Randomize the ratings
        random_ratings = list(ratings)
        random.seed(self.seed)
        random.shuffle(random_ratings)

        # Target number of ratings in the training set
        target_training = len(random_ratings) * (1 - self.test_size)

        # Put the ratings in the test or training sets
        for counter, rating in enumerate(random_ratings):
            if counter < target_training:
                training_set.append(rating)
            else:
                test_set.append(rating)

        return training_set, test_set


class TimestampSplitter(Splitter):
    id = "timestamp"
    name = "Timestamp"
    desc = "Split all the ratings according to their timestamp."

    def split(self, ratings):
        training_set = []
        test_set = []

        # The ratings must be ordered by timestamp
        ordered_ratings = sorted(ratings, key=lambda item: item[3])

        # Target number of ratings in the training set
        target_training = len(ordered_ratings) * (1 - self.test_size)

        # Put the ratings in the test or training sets
        for counter, rating in enumerate(ordered_ratings):
            if counter < target_training:
                training_set.append(rating)
            else:
                test_set.append(rating)

        return training_set, test_set
