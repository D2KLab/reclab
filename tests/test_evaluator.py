import math
import unittest

import reclab

exp = {'k': 3,
       'threshold': 1}
training_set = [[1, 1, 5],
                [1, 2, 4],
                [1, 3, 3],
                [1, 4, 3]]
test_set = [[1, 1, 5],
            [1, 2, 3],
            [1, 3, 5],
            [1, 4, 2],
            [2, 1, 3],
            [2, 2, 5],
            [2, 3, 3]]
user_set = [1, 2]
predictions = [4, 5, 3, 1, 2, 4, 4]
recommendations = [[3, 1, 4],
                   [2, 3, 4]]


class EvaluatorTestSuite(unittest.TestCase):

    def test_rmse(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, predictions, recommendations)
        rmse = evaluator.rmse()
        self.assertAlmostEqual(math.sqrt(13 / 7), rmse)

    def test_mae(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, predictions, recommendations)
        mae = evaluator.mae()
        self.assertAlmostEqual(9 / 7, mae)

    def test_precision(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, predictions, recommendations)
        precision = evaluator.precision()
        self.assertAlmostEqual(5 / 6, precision)

    def test_recall(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, predictions, recommendations)
        recall = evaluator.recall()
        self.assertAlmostEqual(17 / 24, recall)

    def test_ndcg(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, predictions, recommendations)
        ndcg = evaluator.ndcg()
        self.assertAlmostEqual(0.8826803184, ndcg)

    def test_novelty(self):
        evaluator = reclab.Evaluator(exp, training_set, test_set, user_set, predictions, recommendations)
        novelty = evaluator.novelty()
        self.assertAlmostEqual(2, novelty)
