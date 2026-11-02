import importlib.util
import inspect
import sys
import unittest
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('ratio_under_review', sys.argv.pop(1))
ratio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ratio)

class RatioContract(unittest.TestCase):
    def test_positive_readings(self):
        self.assertEqual(ratio.normalise([2, 4, 0]), [0.5, 1.0, 0.0])
    def test_singleton(self):
        self.assertEqual(ratio.normalise([7]), [1.0])
    def test_signature(self):
        self.assertEqual(str(inspect.signature(ratio.normalise)), '(values)')
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            ratio.normalise([])
    def test_all_zero(self):
        self.assertEqual(ratio.normalise([0, 0]), [0, 0])
    def test_mixed_negative_rejected(self):
        with self.assertRaises(ValueError):
            ratio.normalise([-1, 2])
    def test_all_negative_rejected(self):
        with self.assertRaises(ValueError):
            ratio.normalise([-2, -1])

if __name__ == '__main__':
    unittest.main(verbosity=2)
