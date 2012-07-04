from bottle import Bottle, route, run
import os, time
import json

cagibi_folder = "."
@route('/folder')
def filelist():
    """return a list of files with some metadata"""
    dir = {}
    for file in os.listdir(cagibi_folder):
       dir[file] = {}
       dir[file]["mtime"] = os.path.getmtime(os.path.join(cagibi_folder, file))

    return json.dumps(dir)

run(host='localhost', port=8080)
