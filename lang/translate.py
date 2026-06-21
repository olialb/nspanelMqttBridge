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

#
# global definitions
#
TRANSLATE_DB = None
LOGGER = FLOGGER.create_log_handler("Translate")

def weekdays(day):
    """
    return the day name as string
    """
    return TRANSLATE_DB["weekdays"][day]

def weekdays_short(day):
    """
    return the short day name as string
    """
    return TRANSLATE_DB["weekdays_short"][day]

def months_short(month):
    """
    return the short month name as string
    """
    return TRANSLATE_DB["months"][month]

def time_templ():
    """
    return time template
    """
    return TRANSLATE_DB["time"]

def temperture_unit():
    """
    return temperature unit
    """
    return TRANSLATE_DB["temperature"]

def weather_time_templ():
    """
    return time template
    """
    return TRANSLATE_DB["weatherTime"]

def date_templ():
    """
    return date template
    """
    return TRANSLATE_DB["date"]

def key(section, entry):
    """
    Returns one entry form the data base
    """
    if section in TRANSLATE_DB and entry in TRANSLATE_DB[section]:
        return TRANSLATE_DB[section][entry]
    #can not translate
    LOGGER.debug( "Can not translate '%s' in section '%s'", entry, section)
    return entry

def set_language_file(path):
    """
    read json file and
    """
    with open(path, encoding='utf-8') as file:
        global TRANSLATE_DB #pylint: disable=global-statement
        TRANSLATE_DB = json.load(file)

def get_translator_db():
    """
    returns the whole translator database
    """
    return TRANSLATE_DB

def set_translator_db( db ):
    """
    sets the translator database
    """
    global TRANSLATE_DB #pylint: disable=global-statement
    TRANSLATE_DB = db
