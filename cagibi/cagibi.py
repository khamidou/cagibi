#!/usr/bin/env python

from watch import FileWatcher
from rsync import *
from config import load_config
import urllib2
import json

client_config = {}
server_url = "http://localhost:8080/"

def changesHandler(modified, added, removed):
    for file in modified:
        fd = open(file, "rb")
        hashes = blockchecksums(fd)
        print hashes

def checkout_changes():
    """Checkout changes on the server"""
    fd = urllib2.urlopen(server_url + "/folder")
    data = json.load(fd)
    print data

if __name__ == "__main__":
    client_config = load_config("cagibi.json")
    if "server" in client_config:
        server_url = client_config["server"]
        if server_url[-1] == '/':
            server_url = server_url[0:-1]

    fw = FileWatcher()
    fw.addHandler(changesHandler)
    checkout_changes()
    fw.watch()
