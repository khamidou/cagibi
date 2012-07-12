#!/usr/bin/env python

from watch import FileWatcher
from rsync import *
from config import load_config

client_config = {}

def changesHandler(modified, added, removed):
    for file in modified:
        fd = open(file, "rb")
        hashes = blockchecksums(fd)
        print hashes

if __name__ == "__main__":
    client_config = load_config("cagibi.json")
    fw = FileWatcher()
    fw.addHandler(changesHandler)
    fw.watch()
