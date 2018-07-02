import inspect
import random
import sys
from abc import ABC
from abc import abstractmethod


def splitter_instance(splitter_id, *args, **kwargs):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id') and obj.id == splitter_id:
            return obj(*args, **kwargs)
    raise RuntimeError('No splitter ' + splitter_id)


def splitter_list():
    splitters = []
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if hasattr(obj, 'id'):
            splitters.append(obj.id)
    return splitters


class Splitter(ABC):

    def __init__(self, test_size, seed):
        if test_size < 0 or test_size > 1:
            raise ValueError('Test size must be a number between 0 and 1')
        self.test_size = test_size
        self.seed = seed

    @abstractmethod
    def id(self):
        pass

    @abstractmethod
    def split(self, ratings):
        pass


class RandomSplitter(Splitter):
    id = "random"

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

    def split(self, ratings):
        training_set = []
        test_set = []

        # The ratings must be ordered by timestamp
        ordered_ratings = list(ratings)
        sorted(ordered_ratings, key=lambda item: item[3])

        # Target number of ratings in the training set
        target_training = len(ordered_ratings) * (1 - self.test_size)

        # Put the ratings in the test or training sets
        for counter, rating in enumerate(ordered_ratings):
            if counter < target_training:
                training_set.append(rating)
            else:
                test_set.append(rating)

        return training_set, test_set
