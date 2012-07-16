# -*- coding: utf-8 -*-
import json

def load_config(filename="config.json"):
    """load a configuration file in json"""
    return json.load(open(filename))

def save_config(config, filename="config.json"):
    """save a configuration file"""
    json.dump(config, open(filename, 'w'))
