from abc import ABC
from abc import abstractmethod

import numpy as np
import scipy.spatial.distance as distance


class Similarity(ABC):

    @abstractmethod
    def similarity(self, item_i, item_j):
        """
        Compute a similarity metric between two items.

        :param item_i: The first item.
        :param item_j: The second item.
        :return: A similarity value.
        """
        pass


class CosineSimilarity(Similarity):

    def __init__(self, training_set, threshold):
        items = set()
        users = set()

        for rating in training_set:
            items.add(rating[1])
            users.add(rating[0])

        items = list(items)
        users = list(users)

        self.items_index = {}
        for index, item in enumerate(items):
            self.items_index[item] = index

        self.users_index = {}
        for index, user in enumerate(users):
            self.users_index[user] = index

        # Create an item user matrix
        self.matrix = np.full((len(items), len(users)), 0)

        for rating in training_set:
            if rating[2] > threshold:
                item_index = self.items_index[rating[1]]
                user_index = self.users_index[rating[0]]

                self.matrix[item_index, user_index] += 1

    def similarity(self, item_i, item_j):
        """
        Compute the cosine similarity between two items.

        :param item_i: The first item.
        :param item_j: The second item.
        :return: A cosine similarity value.
        """
        if item_i not in self.items_index or item_j not in self.items_index:
            return 0

        index_i = self.items_index[item_i]
        index_j = self.items_index[item_j]

        array_i = self.matrix[index_i]
        array_j = self.matrix[index_j]

        if array_i.sum() == 0 or array_j.sum() == 0:
            return 0
        else:
            return 1 - distance.cosine(array_i, array_j)
