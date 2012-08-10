# -*- coding: utf-8 -*-
import sys
import json
import os

def load_config(filename="config.json"):
    """load a configuration file in json"""
    return json.load(open(filename))

def save_config(config, filename="config.json"):
    """save a configuration file"""
    json.dump(config, open(filename, 'w'))

def get_config_path():
    if os.name != "posix":
        from win32com.shell import shellcon, shell
        confpath = "{}\\cagibi\\cagibi.conf".format(shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0))
    else:
        confpath = "{}/.cagibi/cagibi.conf".format(os.path.expanduser("~"))

    return confpath

