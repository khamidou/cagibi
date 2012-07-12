from bottle import Bottle, route, run, post, get, put, delete, request, abort
import os, time
import json
from config import load_config, save_config

cagibi_folder = "."
files_info = {}

@route('/folder')
def filelist():
    """return a list of files with some metadata"""
    dir = {}

    for file in os.listdir(cagibi_folder):
       dir[file] = {}
       dir[file]["mtime"] = os.path.getmtime(os.path.join(cagibi_folder, file))
       if file in files_info:
           dir[file]["rev"] = files_info[file]["rev"]

    return json.dumps(dir)

@put('/files/<filename>')
def create_file(filename):
    """Create a file on the server. The method receives two POST parameters:
        - filename : the filename
        - contents : the contents
    """
    filename = os.path.basename(filename)
    contents = request.forms.get('contents')
    
    # FIXME: possible race condition
    if not os.path.exists(filename) and filename not in files_info:
        fd = open(filename, "wb")
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
    if os.path.exists(filename) and filename in files_info:
        os.remove(filename)
        del files_info[filename]
        save_config(files_info, filename="files.json")
        return "Ok."
    else:
        abort(501, "File doesn't exist or is not in database.")

@get('/files/<filename>')
def file_info(filename):
    return json.dumps(files_info[filename])

@post('/files/<filename>/deltas')
def return_deltas(filename):
    """return the deltas corresponding to the file. The client must send in its request the hashes of the file"""  
    hashes = json.load(request.forms.get("hashes"))
    patchedfile = open(filename, "rb")
    deltas = rsyncdelta(patchedfile, hashes)
    patchedfile.close()

    return json.dumps(deltas)

if __name__ == "__main__":
    files_info = load_config(filename="files.json")
    run(host='localhost', port=8080)
