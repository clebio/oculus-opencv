#!/usr/bin/env python

if __name__ == '__main__':
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner().run(tests)
