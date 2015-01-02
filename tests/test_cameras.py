from unittest import TestCase
from gevent import queue
from src.camera import CameraReader, CameraProcessor
from mock import Mock, patch
import numpy as np

class TestCameras(TestCase):

    def setUp(self):
        self.left_queue = queue.Queue()
        self.right_queue = queue.Queue()
        def callerback():
            print("Caller back, now.")

        self.camera_processor = CameraProcessor(
            self.left_queue,
            self.right_queue,
        )


    def test_camera_reader(self):
        camera_reader = CameraReader(Mock(), self.left_queue)

        frame = np.random.rand(100, 100, 3)

        returns = [(None, frame), IOError]
        camera_reader.camera.read = Mock(side_effect=returns)

        with self.assertRaises(IOError):
            camera_reader._run()

        self.assertFalse(self.left_queue.empty())
        result = self.left_queue.get()
        self.assertIsInstance(
            result,
            np.ndarray,
        )

    def test_camera_processor_initialize(self):
        self.assertFalse(self.camera_processor.video_out)

    @patch('cv2.imshow')
    def test_camera_processor_iterate(self, imshow_mock):

        left_frame = np.random.rand(100, 100, 3)
        right_frame = np.random.rand(100, 100, 3)
        self.left_queue.put(left_frame)
        self.right_queue.put(right_frame)

        self.camera_processor.iterate()

        imshow_mock.assert_called_once
