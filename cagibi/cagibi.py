#!/usr/bin/env python
# -*- coding: utf-8 -*-
# A note about how this file is organized:
# The cagibi client uses to separate python threads
# - the first one is used to detect file changes 
# - the second one reacts to these changes and discusses with the server
#
# They communicate by using a shared message queue, mqueue, which is a dictionnary
# containing three lists: added, modified, removed.

from watch import FileWatcher
from rsync import *
from config import load_config, save_config
from util import secure_path
from Queue import Queue
import urllib, urllib2
from urllib2 import HTTPError
import json
import time
import os
import threading
import base64


client_config = {}
server_url = "http://localhost:8080/"
cagibi_folder = "."

mqueue = {}
mqueue["added"] = Queue()
mqueue["modified"] = Queue()
mqueue["removed"] = Queue()

# The list of modified files is used when a file has been
# modified by the client itself, so that it doesn't try to
# upload it again to the server in a never-ending loop.
# No need for a mutex as it's thread-local
mqueue["client_modified"] = []


def setup_filewatcher_thread():
    fw = FileWatcher(path=cagibi_folder)
    fw.addHandler(push_filewatcher_changes)
    fw.watch()

def push_filewatcher_changes(modified, added, removed):
    for file in added:
        mqueue["added"].put(file)

    for file in modified:
        mqueue["modified"].put(file)

    for file in removed:
        mqueue["removed"].put(file)

def upload_local_changes():
    """Upload on the server the changes detected by the filewatcher thread"""

    while not mqueue["modified"].empty():
        file = mqueue["modified"].get()
        
        if file in mqueue["client_modified"]:
            continue

        print "Detect %s modified" % file
    
        url = "%s/files/%s/hashes" % (server_url, file)
        try:
            fd = urllib2.urlopen(url)
        except HTTPError:
            # The server may return us an error if things have gone south during
            # the file creation process.
            # If so, mark the file as added instead of modified.
            print "mark as added instead"
            mqueue["added"].put(file)
            continue

        hashes = json.load(fd)
        try:
            print "%f" % os.path.getmtime(secure_path(cagibi_folder, file))
            patchedfile = open(secure_path(cagibi_folder, file), "rb")
            deltas = encode_deltas(rsyncdelta(patchedfile, hashes))
            patchedfile.close()
            print "%f" % os.path.getmtime(secure_path(cagibi_folder, file))
        except IOError:
            "IOError - continuing"
            continue

        # Send the deltas to the server.
        post_data = {}
        post_data["deltas"] = json.dumps(deltas)
        post_string = urllib.urlencode(post_data)
        fd = urllib2.urlopen(url, post_string)
        results = json.load(fd)
        
        local_files = load_config("files.json")
        local_files[file]["rev"] = results["rev"]
        save_config(local_files, filename="files.json") 
        print "%f" % os.path.getmtime(secure_path(cagibi_folder, file))

    opener = urllib2.build_opener(urllib2.HTTPHandler)

    while not mqueue["added"].empty():
        file = mqueue["added"].get()
        print "Detected %s added" % file

        put_data = {}
        try:
            fd = open(secure_path(cagibi_folder, file), "r")
            put_data["contents"] = fd.read()
            put_string = urllib.urlencode(put_data)
            fd.close()
        except IOError, e:
            print e
            continue

        url = "%s/files/%s" % (server_url, file)
        request = urllib2.Request(url, data=put_string)
        request.add_header('Content-Type', 'application/json')
        request.get_method = lambda: 'PUT'
        url = opener.open(request)

    while not mqueue["removed"].empty():
        file = mqueue["removed"].get()
        print "Detect %s removed" % file

        url = "%s/files/%s" % (server_url, file)
        request = urllib2.Request(url)
        request.get_method = lambda: 'DELETE'
        url = opener.open(request)

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
            urllib.urlretrieve(url, secure_path(cagibi_folder, file))
            print "Retrieved %s" % file
            modified = True

        else:
            if server_files[file]["rev"] > local_files[file]["rev"]:
                # Get it too, but using the rsync algo
                print "Retrieving file, using the rsync algorithm"

                try:
                    unpatched = open(secure_path(cagibi_folder, file), "rb")
                    hashes = list(blockchecksums(unpatched))
                except IOError:
                    continue

                json_hashes = json.dumps(hashes)
                post_data = {}
                post_data["hashes"] = json_hashes
                post_string = urllib.urlencode(post_data)

                url = "%s/files/%s/deltas" % (server_url, file) 
                fd = urllib2.urlopen(url, post_string)
                json_response = decode_deltas(json.load(fd))

                unpatched.seek(0)
                save_to = os.tmpfile()
                patchstream(unpatched, save_to, json_response)
                unpatched.close()
                os.unlink(secure_path(cagibi_folder, file))
                save_to.seek(0)
                
                # FIXME: rename instead of copying ?
                try:
                    file_copy = open(secure_path(cagibi_folder, file), "w+b")
                    file_copy.write(save_to.read())
                    file_copy.close()
                    local_files[file]["rev"] = server_files[file]["rev"] 
                    modified = True
                    mqueue["client_modified"].append(file)
                except IOError:
                    continue

                save_to.close()


    if modified == True:
        save_config(local_files, filename="files.json") 

def sync_changes():
    while True:
        checkout_upstream_changes()
        mqueue["client_modified"] = []
        time.sleep(10)
        upload_local_changes()

if __name__ == "__main__":
    client_config = load_config("cagibi.json")
    if "server" in client_config:
        server_url = client_config["server"]
        if server_url[-1] == '/':
            server_url = server_url[0:-1]

    if "folder" in client_config:
        cagibi_folder = client_config["folder"]

    syncThread = threading.Thread(name="sync", target=sync_changes)
    syncThread.start()
    filewatcherThread = threading.Thread(name="filewatcher", target=setup_filewatcher_thread)
    filewatcherThread.start()

