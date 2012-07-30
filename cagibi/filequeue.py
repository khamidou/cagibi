from Queue import Queue

class FileQueue(object):
    """A convenience class representing which files have been modified at a given time"""
    def __init__(self):
        super(FileQueue, self).__init__()
        self.added = Queue()
        self.removed = Queue()
        self.modified = Queue()

        # The list of modified files is used when a file has been
        # modified by the client itself, so that it doesn't try to
        # upload it again to the server in a never-ending loop.
        # No need for a mutex as it's thread-local
        self.client_modified = []
