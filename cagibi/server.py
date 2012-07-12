from bottle import Bottle, route, run
import os, time
import json

cagibi_folder = "."
files_info = {}

@route('/folder')
def filelist():
    """return a list of files with some metadata"""
    dir = {}

    for file in os.listdir(cagibi_folder):
       dir[file] = {}
       dir[file]["mtime"] = os.path.getmtime(os.path.join(cagibi_folder, file))

    return json.dumps(dir)

@post('/create/')
def create_file():
    """Create a file on the server. The method receives two POST parameters:
        - filename : the filename
        - contents : the contents
    """
    filename = os.path.basename(request.forms.get('filename'))
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
        abort(500, "File already exists")

@post('/update/<filename>')
def update_filename(filename):
    """return the deltas corresponding to the file. The client must send in its request the hashes of the file"""  
    return filename

if __name__ == "__main__":
    files_info = load_config(filename="files.json")
    run(host='localhost', port=8080)
