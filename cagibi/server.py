# -*- coding: utf-8 -*-
from bottle import Bottle, route, run, post, get, put, delete, request, abort, static_file
import os, time
import json
import base64
from config import load_config, save_config
from rsync import rsyncdelta, blockchecksums, patchstream, encode_deltas, decode_deltas
from util import secure_path

cagibi_folder = "."
server_config = {}
files_info = {}

@route('/folder')
def filelist():
    """return a list of files with some metadata"""
    folder = {}
    files_info = load_config(filename="files.json")

    for file in os.listdir(cagibi_folder):
        folder[file] = {}
        folder[file]["mtime"] = os.path.getmtime(secure_path(cagibi_folder, file))

        if file not in files_info:
            # Automatically add new files
            files_info[file] = {}
            files_info[file]["rev"] = 1
            # FIXME: don't save the data for every new file.
            save_config(files_info, filename="files.json")
        
        folder[file]["rev"] = files_info[file]["rev"]


    return json.dumps(folder)

@put('/files/<filename>')
def create_file(filename):
    """Create a file on the server. The method receives two POST parameters:
        - filename : the filename
        - contents : the contents
    """
    #FIXME: handle directories
    filename = os.path.basename(filename)
    contents = request.forms.get('contents')
    
    # FIXME: possible race condition
    if not os.path.exists(filename) and filename not in files_info:
        fd = open(secure_path(cagibi_folder, filename), "wb")
        fd.write(contents)
        fd.close()
        files_info[filename] = {"rev": 1}
        save_config(files_info, filename="files.json")
        return "Ok."
    else:
        abort(501, "File already exists")

@delete('/files/<filename>')
def delete_file(filename):
    """Remove a file"""
    filename = os.path.basename(filename)
    
    # FIXME: possible race condition
    if os.path.exists(secure_path(cagibi_folder, filename)) and filename in files_info:
        os.remove(secure_path(cagibi_folder, filename))
        del files_info[filename]
        save_config(files_info, filename="files.json")
        return "Ok."
    else:
        abort(500, "File doesn't exist or is not in database.")

@get('/files/<filename>')
def file_info(filename):
    return json.dumps(files_info[filename])

@get('/files/<filename>/data')
def file_data(filename):
    """Return the contents of the file"""
    return static_file(filename, root=cagibi_folder)

@get('/files/<filename>/hashes')
def file_hashes(filename):
    """Return the hashes of a file"""
    unpatched = open(secure_path(cagibi_folder, filename), "rb")
    hashes = list(blockchecksums(unpatched))
    unpatched.close()
    return json.dumps(hashes)

@post('/files/<filename>/hashes')
def update_file_hashes(filename):
    """Updates a file using the deltas received by a client"""
    deltas = decode_deltas(json.loads(request.forms.get("deltas")))
    print deltas

    unpatched = open(secure_path(cagibi_folder, filename), "rb")
    save_to = os.tmpfile()
    patchstream(unpatched, save_to, deltas)
    unpatched.close()
    os.unlink(secure_path(cagibi_folder, filename))
    save_to.seek(0)

    # FIXME: rename instead of copying ?
    file_copy = open(secure_path(cagibi_folder, filename), "w+b")
    file_copy.write(save_to.read())
    file_copy.close()
    save_to.close()
    
    files_info[filename] = {"rev": files_info[filename]["rev"] + 1}
    save_config(files_info, filename="files.json")

    return files_info[filename]

@post('/files/<filename>/deltas')
def return_deltas(filename):
    """return the deltas corresponding to the file. The client must send in its request the hashes of the file"""  
    hashes = json.loads(request.forms.get("hashes"))
    patchedfile = open(secure_path(cagibi_folder, filename), "rb")
    deltas = encode_deltas(rsyncdelta(patchedfile, hashes))
    patchedfile.close()

    return json.dumps(deltas)

if __name__ == "__main__":
    server_config = load_config("cagibi_server.json")
    if "folder" in server_config:
        cagibi_folder = server_config["folder"]

    files_info = load_config(filename="files.json")
    run(host='localhost', port=8080)
