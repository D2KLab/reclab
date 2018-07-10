import inspect
import itertools

import numpy as np

from .similarity import CosineSimilarity


def evaluator_list():
    evaluators = {}
    for name, obj in inspect.getmembers(Evaluator):
        if hasattr(obj, 'name') and hasattr(obj, 'sort'):
            evaluators[name] = {'name': obj.name,
                                'sort': obj.sort}
    sorted_evaluators = {}
    for key in sorted(evaluators, key=lambda x: evaluators[x]['sort']):
        sorted_evaluators[key] = evaluators[key]
    return sorted_evaluators


class Evaluator:

    def __init__(self, exp, training_set, test_set, user_set, recommendations):
        self.k = exp['k']
        self.user_set = user_set
        self.recommendations = recommendations
        self.model_items, self.model_top_k = self._count_items(training_set)
        self.reference_sorted = self._reference_sorted(test_set, exp['threshold'])
        self.metric = CosineSimilarity(training_set, exp['threshold'])

    @staticmethod
    def _reference_sorted(test_set, threshold):
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

    @staticmethod
    def _count_items(training_set):
        model_items = {}
        model_top_k = []

        for rating in training_set:
            item = rating[1]

            if item not in model_items:
                model_items[item] = 1
            else:
                model_items[item] += 1

        # Sort items by the number of ratings
        for item in sorted(model_items, key=model_items.get, reverse=True):
            model_top_k.append(item)

        for item in model_items:
            model_items[item] /= len(training_set)

        return model_items, model_top_k

    def coverage(self):
        recommended_items = set()

        # For each user
        for user_index, user in enumerate(self.user_set):
            predicted_list = self.recommendations[user_index]

            # For each item
            for item in predicted_list:
                recommended_items.add(item)

        return len(recommended_items) / len(self.model_items)

    coverage.name = "Coverage"
    coverage.sort = 0

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

    precision.name = "Precision"
    precision.sort = 1

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

    recall.name = "Recall"
    recall.sort = 2

    def ndcg(self):
        dcg = np.full(len(self.user_set), 0.0, dtype=float)
        idcg = np.full(len(self.user_set), 0.0, dtype=float)

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

    ndcg.name = "NDCG"
    ndcg.sort = 3

    def novelty(self):
        values = np.full(len(self.user_set), 0.0, dtype=float)

        # For each user
        for user_index, user in enumerate(self.user_set):
            predicted_list = self.recommendations[user_index]
            metric = 0

            # For each item
            for item in predicted_list:
                item_distribution = self.model_items[item]

                # log(0) = 0 by definition
                if item_distribution != 0:
                    metric += np.log2(item_distribution)

            metric *= -1 * (1 / self.k)
            values[user_index] = metric

        return values.mean()

    novelty.name = "Novelty"
    novelty.sort = 4

    def diversity(self):
        values = np.full(len(self.user_set), 0.0, dtype=float)

        # For each user
        for user_index, user in enumerate(self.user_set):
            predicted_list = self.recommendations[user_index]

            for items in itertools.combinations(predicted_list, 2):
                values[user_index] += (1 - self.metric.similarity(items[0], items[1]))

            values[user_index] /= self.k * (self.k - 1) * 0.5

        return values.mean()

    diversity.name = "Diversity"
    diversity.sort = 5

    def serendipity(self):
        values = np.full(len(self.user_set), 0.0, dtype=float)
        primitive_list = self.model_top_k[:self.k]

        # For each user
        for user_index, user in enumerate(self.user_set):
            predicted_list = self.recommendations[user_index]
            reference_list = self.reference_sorted[user]

            hit = 0

            # For each item
            for item in predicted_list:
                if item in primitive_list:
                    continue

                if item in reference_list:
                    hit += 1

            values[user_index] = hit / self.k

        return values.mean()

    serendipity.name = "Serendipity"
    serendipity.sort = 6
