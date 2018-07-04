import numpy as np


class Evaluator:

    def __init__(self, exp, test_set, user_set, predictions, recommendations):
        self.k = exp['k']
        self.test_set = test_set
        self.user_set = user_set
        self.predictions = predictions
        self.recommendations = recommendations
        self.reference_sorted = self._get_reference_sorted(test_set, exp['threshold'])

    @staticmethod
    def _get_reference_sorted(test_set, threshold):
        reference = {}

        for i, rating in enumerate(test_set):
            user = rating[0]

            if user not in reference:
                reference[user] = []

            reference[user].append([rating[1], rating[2]])

        for user in reference:
            reference[user].sort(key=lambda x: x[1], reverse=True)
            reference[user] = list(filter(lambda x: x[1] > threshold, reference[user]))
            reference[user] = list(map(lambda x: x[0], reference[user]))

        return reference

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

    def precision(self):
        values = np.full(len(self.user_set), 0.0, dtype=float)

        # For each user
        for user_index, user in enumerate(self.user_set):
            predicted_list = self.recommendations[user_index]
            reference_list = self.reference_sorted[user]

            hit = 0

            # For each item
            for item in predicted_list:
                if item in reference_list:
                    hit += 1

            values[user_index] = hit / self.k

        return values.mean()

    def recall(self):
        values = np.full(len(self.user_set), 0.0, dtype=float)

        # For each user
        for user_index, user in enumerate(self.user_set):
            predicted_list = self.recommendations[user_index]
            reference_list = self.reference_sorted[user]

            hit = 0

            # For each item
            for item in predicted_list:
                if item in reference_list:
                    hit += 1

            try:
                values[user_index] = hit / len(reference_list)
            except ZeroDivisionError:
                pass

        return values.mean()

    def ndcg(self):
        dcg = np.full(len(self.test_set), 0.0, dtype=float)
        idcg = np.full(len(self.test_set), 0.0, dtype=float)

        # For each user
        for user_index, user in enumerate(self.user_set):
            predicted_list = self.recommendations[user_index]
            reference_list = self.reference_sorted[user]

            # For each item
            for i, item in enumerate(predicted_list):
                idcg[user_index] += 1 / np.log2(i + 2)

                if item in reference_list:
                    dcg[user_index] += 1 / np.log2(i + 2)

        return dcg.mean() / idcg.mean()
