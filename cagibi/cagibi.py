#!/usr/bin/env python
# -*- coding: utf-8 -*-

from watch import FileWatcher
from rsync import *
from config import load_config, save_config
from util import secure_path
import urllib, urllib2
import json
import os

client_config = {}
server_url = "http://localhost:8080/"
cagibi_folder = "."


def upload_local_changes(modified, added, removed):

    for file in modified:
        print "Detect %s modified" % file
        url = "%s/files/%s/hashes" % (server_url, file)
        fd = urllib2.urlopen(url)
        hashes = json.load(fd)
        patchedfile = open(secure_path(cagibi_folder, file), "rb")
        deltas = list(rsyncdelta(patchedfile, hashes))
        patchedfile.close()

        # Send the deltas to the server.
        post_data = {}
        post_data["deltas"] = json.dumps(deltas)
        post_string = urllib.urlencode(post_data)
        fd = urllib2.urlopen(url, post_string)
        results = json.load(fd)
        
        local_files = load_config("files.json")
        local_files[file]["rev"] = results["rev"]
        save_config("files.json")

    opener = urllib2.build_opener(urllib2.HTTPHandler)

    for file in added:
        put_data = {}
        fd = open(secure_path(cagibi_folder, file), "r")
        put_data["contents"] = fd.read()
        put_string = urllib.urlencode(put_data)
        fd.close()

        url = "%s/files/%s" % (server_url, file)
        request = urllib2.Request(url, data=put_string)
        request.add_header('Content-Type', 'application/json')
        request.get_method = lambda: 'PUT'
        url = opener.open(request)

    for file in removed:
        url = "%s/files/%s" % (server_url, file)
        request = urllib2.Request(url, data=put_string)
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

                unpatched = open(secure_path(cagibi_folder, file).encode('ascii', 'ignore'), "rb")
                hashes = list(blockchecksums(unpatched))
                json_hashes = json.dumps(hashes)
                post_data = {}
                post_data["hashes"] = json_hashes
                post_string = urllib.urlencode(post_data)

                url = "%s/files/%s/deltas" % (server_url, file) 
                fd = urllib2.urlopen(url, post_string)
                json_response = json.load(fd)

                unpatched.seek(0)
                save_to = os.tmpfile()
                patchstream(unpatched, save_to, json_response)
                unpatched.close()
                os.unlink(secure_path(cagibi_folder, file))
                save_to.seek(0)
                
                # FIXME: rename instead of copying ?
                file_copy = open(secure_path(cagibi_folder, file).encode('ascii', 'ignore'), "w+b")
                file_copy.write(save_to.read())
                file_copy.close()
                save_to.close()
                
                local_files[file]["rev"] = server_files[file]["rev"] 

    if modified == True:
        save_config(local_files, filename="files.json") 

if __name__ == "__main__":
    client_config = load_config("cagibi.json")
    if "server" in client_config:
        server_url = client_config["server"]
        if server_url[-1] == '/':
            server_url = server_url[0:-1]

    if "folder" in client_config:
        cagibi_folder = client_config["folder"]

    fw = FileWatcher(path=cagibi_folder)
    fw.addHandler(upload_local_changes)
    checkout_upstream_changes()
    fw.watch()
