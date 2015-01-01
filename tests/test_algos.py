from unittest import TestCase

from src.algos import *

class TestAlgos(TestCase):

    def setUp(self):
        pass

    def test_crop(self):
        self.assertTrue(False)

    def test_create_distortion_matrix(self):
        self.assertTrue(False)

    def test_transfomr(self):
        self.assertTrue(False)

    def test_join_images(self):
        l_part = [1, 2]
        r_part = [3, 4]
        left = np.array([l_part, l_part])
        right = np.array([r_part, r_part])

        result = join_images(left, right)

        l_part.extend(r_part)
        self.assertEqual(
            result.tolist(),
            [l_part, l_part],
        )

    def test_translate(self):
        self.assertTrue(False)

    def test_print_params(self):
        self.assertTrue(False)

    def test_parameters(self):
        for parameter in [
                'width',
                'height',
                'fps',
                'key_mappings',
            ]:
            self.assertTrue(
                getattr(Parameters, parameter)
            )
