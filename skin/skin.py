# python
# because of smbus usage:
# pylint: disable=c-extension-no-member
#
# This file is part of the mqttDisplayClient distribution
# (https://github.com/olialb/nsPanelMqttBridge).
# Copyright (c) 2026 Oliver Albold.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
Module implements a simple translator based on json files
"""

import json

#project imports
from file_logger import file_logger as FLOGGER
from nspanel.nspanel_globals import interpret_icon

#
# global definitions
#
SKIN_DB = None

#idetify an iconname in the entries
ICON_KEY = "icon="

LOGGER = FLOGGER.create_log_handler("Skin")

def key(section, entry=None):
    """
    Returns one entry form the data base
    """
    if entry is None:
        return SKIN_DB[section]
    if section not in SKIN_DB:
        section = "default"
    if entry in SKIN_DB[section]:
        val = SKIN_DB[section][entry]
        if isinstance(val,str) and val.startswith(ICON_KEY):
            return icon((val[len(ICON_KEY):]))
        return val
    if isinstance(entry,str):
        if entry.startswith(ICON_KEY):  # 'icon=<name>' :: assume arbitrary named icon
            return icon((entry[len(ICON_KEY):]))
        if len(entry) == 1:  # single character :: assume direct icon-ID
            return entry
    LOGGER.error( "DB: No entry for section '%s' with entry '%s'.", section, entry)
    return None

def exists(section, entry=None):
    """
    check if entry exists
    """
    if entry is None:
        if section in SKIN_DB:
            return True
        return False
    if section not in SKIN_DB:
        section = "default"
    if entry in SKIN_DB[section]:
        return True
    return False

def icon( icon_name ):
    """
    Returns the unicode for the given icon name
    """
    if "icons" in SKIN_DB and icon_name in SKIN_DB["icons"]:
        return SKIN_DB["icons"][icon_name]
    return interpret_icon(icon_name)

def set_skin_file(path):
    """
    read json file and
    """
    global SKIN_DB #pylint: disable=global-statement
    with open(path, encoding='utf-8') as file:
        SKIN_DB = json.load(file)
    with open("./skin/icons.json", encoding='utf-8') as file:
        icons = json.load(file)
        SKIN_DB["icons"] = icons

def get_skin_db():
    """
    returns the whole skin database
    """
    return SKIN_DB

def set_skin_db( db ):
    """
    sets the skin database
    """
    global SKIN_DB #pylint: disable=global-statement
    SKIN_DB = db
