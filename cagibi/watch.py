# -*- coding: utf-8 -*-
import os, time

class FileWatcher:
    def __init__(self, path = '.'):
        self.path = path
        self.handlers = []
        self.paused = False

    def addHandler(self, fn):
        """add an handler which is called everytime a change is detected. 
        This function takes three parameters : a list of files modified, a list of files added and a list of files removed."""
        self.handlers.append(fn)

    def watch(self):
        before = dict ([(f, None) for f in os.listdir (self.path)])
        
        while not self.paused:
            elapsed_time = time.time()
            time.sleep (10)
            after = dict ([(f, None) for f in os.listdir (self.path)])
            added = [f for f in after if not f in before]
            removed = [f for f in before if not f in after]
            modified = [f for f in after if os.path.getmtime(os.path.join(self.path, f)) > elapsed_time and f not in added]
            
            for handler in self.handlers:
                handler(modified, added, removed)

            before = after

    def stop(self):
        self.paused = True

if __name__ == "__main__":
    def handler(m, a, r):
        print "added: %s, modified: %s, removed: %s" % (a, m, r)

    fw = FileWatcher()
    fw.addHandler(handler)
    fw.watch()
