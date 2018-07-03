import math
import unittest

import reclab

test_set = [[1, 1, 5],
            [1, 2, 3],
            [1, 3, 5],
            [1, 4, 2],
            [2, 1, 3],
            [2, 2, 5],
            [2, 3, 3]]
predictions = [4, 5, 3, 1, 2, 4, 4]


class EvaluatorTestSuite(unittest.TestCase):

    def test_rmse(self):
        evaluator = reclab.Evaluator(test_set, predictions)
        rmse = evaluator.rmse()
        self.assertAlmostEqual(math.sqrt(13 / 7), rmse)

    def test_mae(self):
        evaluator = reclab.Evaluator(test_set, predictions)
        mae = evaluator.mae()
        self.assertAlmostEqual(9 / 7, mae)
