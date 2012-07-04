import unittest
import watch

class FileWatcherTestCase(unittest.TestCase):
        def setUp(self):
            self.watcher = watch.FileWatcher()
            self.counter = 0

        def test_hop(self):
            self.assertTrue(True)

        def handler(self):
            count += 1

