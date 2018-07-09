import unittest

import reclab

ratings = [[1, 1, 5, 2],
           [1, 2, 4, 1],
           [2, 4, 3, 4],
           [2, 3, 5, 3],
           [1, 5, 3, 6],
           [1, 6, 2, 7]]


class SplitterTestSuite(unittest.TestCase):

    def test_random_splitter(self):
        splitter = reclab.splitter_instance({'splitter': 'random', 'seed': 0.5, 'test_size': 0.2})
        training_set, test_set = splitter.split(ratings)
        self.assertEqual([[1, 5, 3, 6], [1, 6, 2, 7], [1, 1, 5, 2], [1, 2, 4, 1], [2, 3, 5, 3]], training_set)
        self.assertEqual([[2, 4, 3, 4]], test_set)

    def test_timestamp_splitter(self):
        splitter = reclab.splitter_instance({'splitter': 'timestamp', 'seed': 0.5, 'test_size': 0.2})
        training_set, test_set = splitter.split(ratings)
        self.assertEqual([[1, 2, 4, 1], [1, 1, 5, 2], [2, 3, 5, 3], [2, 4, 3, 4], [1, 5, 3, 6]], training_set)
        self.assertEqual([[1, 6, 2, 7]], test_set)


if __name__ == '__main__':
    unittest.main()
