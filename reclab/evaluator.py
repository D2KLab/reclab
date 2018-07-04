import numpy as np


class Evaluator:

    def __init__(self, exp, test_set, user_set, predictions, recommendations):
        self.k = exp['k']
        self.test_set = test_set
        self.user_set = user_set
        self.predictions = predictions
        self.recommendations = recommendations

    def rmse(self):
        total = 0

        for i, rating in enumerate(self.test_set):
            total += np.power(rating[2] - self.predictions[i], 2)

        total /= len(self.test_set)

        return np.sqrt(total)

    def mae(self):
        total = 0

        for i, rating in enumerate(self.test_set):
            total += np.abs(rating[2] - self.predictions[i])

        total /= len(self.test_set)

        return total

    @staticmethod
    def _get_top_k(ratings, k):
        ratings.sort(key=lambda x: x[1], reverse=True)
        return list(map(lambda x: x[0], ratings))[0: k]

    def precision(self):
        reference_ratings = {}

        for i, rating in enumerate(self.test_set):
            user = rating[0]

            if user not in reference_ratings:
                reference_ratings[user] = []

            reference_ratings[user].append((rating[1], rating[2]))

        values = np.full(len(self.user_set), 0.0, dtype=float)

        # For each user
        for user_index, user in enumerate(self.user_set):
            predicted_list = self.recommendations[user_index]
            reference_list = self._get_top_k(reference_ratings[user], self.k)

            hit = 0

            for item in predicted_list:
                if item in reference_list:
                    hit += 1

            values[user_index] = hit / len(reference_list)

        return values.mean()
