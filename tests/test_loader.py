import unittest

import reclab


class LoaderTestSuite(unittest.TestCase):

    def test_ml_100k(self):
        loader = reclab.loader_instance({"format": "uirt", "path": "../datasets/ml-100k/ratings.csv",
                                         "sep": "\t", "skip": 0})
        ratings = loader.load()
        self.assertEqual(100000, len(ratings))
        self.assertEqual([0, 0, 3, 881250949], ratings[0])
        self.assertEqual([304, 506, 3, 879959583], ratings[99999])

    def test_ml_1m(self):
        loader = reclab.loader_instance({"format": "uirt", "path": "../datasets/ml-1m/ratings.csv",
                                         "sep": "::", "skip": 0})
        ratings = loader.load()
        self.assertEqual(1000209, len(ratings))
        self.assertEqual([0, 0, 5, 978300760], ratings[0])
        self.assertEqual([6039, 26, 4, 956715569], ratings[1000208])

    def test_lastfm(self):
        loader = reclab.loader_instance({"format": "uir", "path": "../datasets/lastfm/ratings.csv",
                                         "sep": "\t", "skip": 1})
        ratings = loader.load()
        self.assertEqual(92834, len(ratings))
        self.assertEqual([0, 0, 13883, 1], ratings[0])
        self.assertEqual([1891, 17631, 263, 92834], ratings[92833])


if __name__ == '__main__':
    unittest.main()
