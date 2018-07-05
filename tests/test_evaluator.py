import unittest

import numpy as np

import reclab

exp = {'k': 3,
       'threshold': 1}

training_set = [[1, 1, 5],
                [1, 2, 4],
                [1, 3, 3],
                [1, 4, 3],
                [2, 2, 3],
                [2, 3, 1],
                [2, 1, 4]]

test_set = [[1, 1, 5],
            [1, 2, 3],
            [1, 3, 5],
            [1, 4, 2],
            [2, 1, 3],
            [2, 2, 5],
            [2, 3, 3]]

user_set = [1, 2]

recommendations = [[3, 1, 4],
                   [2, 3, 4]]


class EvaluatorTestSuite(unittest.TestCase):

    def test_precision(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, recommendations)
        precision = evaluator.precision()
        self.assertAlmostEqual(5 / 6, precision)

    def test_recall(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, recommendations)
        recall = evaluator.recall()
        self.assertAlmostEqual(17 / 24, recall)

    def test_ndcg(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, recommendations)
        ndcg = evaluator.ndcg()
        self.assertAlmostEqual(np.log(3888) / np.log(11664), ndcg)

    def test_novelty(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, recommendations)
        novelty = evaluator.novelty()
        self.assertAlmostEqual(np.log(7) / np.log(2) - 2 / 3, novelty)

    def test_diversity(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, recommendations)
        diversity = evaluator.diversity()
        self.assertAlmostEqual((2 - np.sqrt(2)) / 3, diversity)
