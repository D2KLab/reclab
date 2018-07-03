import numpy as np


class Evaluator:

    def __init__(self, test_set, predictions):
        self.test_set = test_set
        self.predictions = predictions

    def rmse(self):
        total = 0

        for i, rating in enumerate(self.test_set):
            total += np.power(rating[2] - self.predictions[i], 2)

        total /= len(self.test_set)

        return np.sqrt(total)
