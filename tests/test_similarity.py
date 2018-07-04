import unittest

import numpy as np

import reclab

training_set = [[1, 1, 5],
                [1, 2, 4],
                [1, 3, 3],
                [1, 4, 3],
                [2, 2, 3],
                [2, 3, 1],
                [2, 1, 4]]


class SimilarityTestSuite(unittest.TestCase):

    def test_cosine_similarity(self):
        cosine = reclab.CosineSimilarity(training_set, 1)
        self.assertAlmostEqual(1, cosine.similarity(1, 2))
        self.assertAlmostEqual(1 / np.sqrt(2), cosine.similarity(1, 3))
        self.assertAlmostEqual(1, cosine.similarity(3, 3))
        self.assertAlmostEqual(0, cosine.similarity(3, 5))


if __name__ == '__main__':
    unittest.main()
