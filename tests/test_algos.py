from unittest import TestCase
import numpy as np
from StringIO import StringIO
import sys

from src.algos import *

class TestAlgos(TestCase):

    def setUp(self):
        pass

    def test_crop(self):
        shape = 100, 100, 3
        Parameters.width, Parameters.height, _ = shape
        input = np.zeros(shape)

        result = crop(input, 3, 5, 7, 9)
        res_width, res_height = shape[0] - 5 - 3, shape[1] - 9 - 7

        self.assertEqual(
            result.shape,
            (res_width, res_height, shape[2])
        )

    def test_create_distortion_matrix(self):
        result = create_distortion_matrix(
            1, 3, 5, 7
        )

        expected = np.array([[1, 0, 3], [0, 5, 7], [0, 0, 1]])

        self.assertTrue(np.array_equal(
            result,
            expected
        ))

    def test_transform(self):
        input = np.random.rand(100, 100)
        mat = create_distortion_matrix(
            1, 3, 5, 7
        )


        result = transform(input, mat)
        self.assertEqual(
            input.shape,
            result.shape
        )

        result = transform( input, mat, k1=0.1, k2=0.1)
        self.assertEqual(
            input.shape,
            result.shape
        )


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
        shape = 100, 100
        input = np.zeros(shape)
        sentinel = 7
        input[0,0] = sentinel

        deltax, deltay = 30, 50
        result = translate(input, deltax, deltay)

        self.assertTrue(
            result.shape,
            (Parameters.height, Parameters.width),
        )
        self.assertEqual(
            result[deltay, deltax],
            sentinel,
        )

    def test_print_params(self):
        real_stdout = sys.stdout
        fake_out = StringIO()
        sys.stdout = fake_out

        print_params()
        output = fake_out.getvalue().strip()

        expected = [par for par in dir(Parameters) if par.isalnum()]

        for item in expected:
            self.assertTrue(
                item in output
            )
        sys.stdout = real_stdout

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
