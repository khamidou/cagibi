#!/usr/bin/env python

from watch import FileWatcher
from rsync import *
from config import load_config
import urllib, urllib2
import json
import os

client_config = {}
server_url = "http://localhost:8080/"
cagibi_folder = "."

def changesHandler(modified, added, removed):
    for file in modified:
        fd = open(file, "rb")
        hashes = blockchecksums(fd)
        print hashes

def checkout_upstream_changes():
    """Checkout changes on the server"""
    fd = urllib2.urlopen(server_url + "/folder")
    server_files = json.load(fd)
    fd.close()

    local_files = load_config("files.json")

    modified = False

    for file in server_files:
        if file not in local_files:
            # Get it
            local_files[file] = {}
            local_files[file]["rev"] = server_files[file]["rev"]
            url = "%s/files/%s/data" % (server_url, file) 
            urllib.urlretrieve(url, os.path.join(cagibi_folder, file))
            print "Retrieved %s" % file
        else:
            if server_files[file]["rev"] > local_files[file]["rev"]:
                # Get it too, but using the rsync algo
                pass

if __name__ == "__main__":
    client_config = load_config("cagibi.json")
    if "server" in client_config:
        server_url = client_config["server"]
        if server_url[-1] == '/':
            server_url = server_url[0:-1]

    if "folder" in client_config:
        cagibi_folder = client_config["folder"]

    fw = FileWatcher()
    fw.addHandler(changesHandler)
    checkout_upstream_changes()
    fw.watch()
