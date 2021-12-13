import unittest
from tabledans import TabledANS
import numpy as np


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        np.random.seed(0)

    def test_sanity(self):
        inp = np.round(np.random.normal(size=100)).astype(np.int32)
        tans = TabledANS.from_data(inp)
        bitStream = tans.encodeData(inp)
        output = np.array(tans.decodeData(bitStream))
        self.assertTrue(np.array_equal(inp, output))

        cmp_ratio = 32*inp.size/len(bitStream)
        self.assertGreater(cmp_ratio, 1.)

    def test_random_cover(self):
        for i in range(100):
            inp = np.round(np.random.normal(size=100)).astype(np.int32)
            tans = TabledANS.from_data(inp)
            bitStream = tans.encodeData(inp)
            output = np.array(tans.decodeData(bitStream))
            self.assertTrue(np.array_equal(inp, output))

            cmp_ratio = 32*inp.size/len(bitStream)
            self.assertGreater(cmp_ratio, 1.)

    def test_sizes(self):
        for i in range(1, 100):
            inp = np.round(np.random.normal(size=i*10)).astype(np.int32)
            tans = TabledANS.from_data(inp)
            bitStream = tans.encodeData(inp)
            output = np.array(tans.decodeData(bitStream))
            self.assertTrue(np.array_equal(inp, output))

            cmp_ratio = 32*inp.size/len(bitStream)
            self.assertGreater(cmp_ratio, 1.)

    def test_uniform(self):
        inp = np.round(10*np.random.normal(size=1000)).astype(np.int32)
        tans = TabledANS.from_data(inp)
        bitStream = tans.encodeData(inp)
        output = np.array(tans.decodeData(bitStream))
        self.assertTrue(np.array_equal(inp, output))

        cmp_ratio = 32*inp.size/len(bitStream)
        self.assertGreater(cmp_ratio, 1.)

if __name__ == '__main__':
    unittest.main(verbosity=2)
