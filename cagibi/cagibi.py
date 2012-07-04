#!/usr/bin/env python

from watch import FileWatcher
from rsync import *

def changesHandler(modified, added, removed):
    for file in modified:
        fd = open(file, "rb")
        hashes = blockchecksums(fd)
        print hashes

if __name__ == "__main__":
    fw = FileWatcher()
    fw.addHandler(changesHandler)
    fw.watch()
