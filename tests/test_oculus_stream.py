from unittest import TestCase
from mock import Mock, patch
from src.oculus_stream import run

class TestOculusStream(TestCase):

    def setUp(self):
        pass

    @patch('src.oculus_stream.gevent')
    @patch('src.oculus_stream.InputHandler')
    @patch('src.oculus_stream.args')
    @patch('src.oculus_stream.CameraProcessor')
    @patch('src.oculus_stream.CameraReader')
    @patch('src.oculus_stream.cv2')
    def test_run(self, opencv, camera, processor, parser, handler, gevent):
        camera.isOpened.return_value = True
        parser.oculus = False
        gevent.joinall.side_effect = IOError
        with self.assertRaises(IOError):
            run()
