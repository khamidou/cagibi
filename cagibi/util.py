import os

def secure_path(folder_path, file):
    """Make sure that a file/path is located in the folder "folder" """
    #FIXME: make it work for directories.
    return folder_path + os.path.sep + os.path.basename(file)
