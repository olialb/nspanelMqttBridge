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
Module implements a file logger for the different classes in the project
"""

import configparser
import logging
import logging.handlers
import os
import sys

#
# global constants
#
CONFIG_FILE = "nspanelMqttBridge.ini"  # name of the ini file

# import from the configuration file only the feature configuraion
LOGGING_CFG = configparser.ConfigParser()
#set logging default values
LOG_FILE_PATH = "log"
LOG_FILE_NAME = None
LOG_FILE_BACKUP =  5
LOG_FILE_ROTATE = "midnight"
LOG_LEVEL_CONSOLE = "WARNING"  # this would be default basicConfig() setting
LOG_FORMAT = "[%(asctime)s] %(levelname)7s %(name)-20s %(message)s"

LOG_FILE_HANDLER = None  # We only need ONE file-handler instance! After creating it once, we set it to ALL the loggers.

# try to open ini file
try:
    if os.path.exists(CONFIG_FILE) is True:
        LOGGING_CFG.read(CONFIG_FILE)
except OSError:
    print(f"Error while reading ini file: {CONFIG_FILE}")
    sys.exit()

# read logging config
LOG_LEVEL = LOGGING_CFG["logging"]["level"]
if LOG_LEVEL.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    raise KeyError(LOG_LEVEL)
LOG_LEVEL = LOG_LEVEL.upper()

if "console_level" in LOGGING_CFG["logging"]:
    LOG_LEVEL_CONSOLE = LOGGING_CFG["logging"]["console_level"]
    if LOG_LEVEL_CONSOLE.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise KeyError(LOG_LEVEL_CONSOLE)
    LOG_LEVEL_CONSOLE = LOG_LEVEL_CONSOLE.upper()

if "path" in LOGGING_CFG["logging"]:
    LOG_FILE_PATH = LOGGING_CFG["logging"]["path"]
if "file" in LOGGING_CFG["logging"]:
    LOG_FILE_NAME = LOGGING_CFG["logging"]["file"]
if "format" in LOGGING_CFG["logging"]:
    LOG_FORMAT = LOGGING_CFG["logging"]["format"]
if "backup" in LOGGING_CFG["logging"]:
    LOG_FILE_BACKUP = LOGGING_CFG["logging"]["backup"]
if "rotate" in LOGGING_CFG["logging"]:
    LOG_FILE_ROTATE =LOGGING_CFG["logging"]["rotate"]

logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
# after basicConfig, there is a root logger with exactly ONE handler (console output)
logging.root.handlers[0].setLevel(LOG_LEVEL_CONSOLE)  # allows further reduction of console output

def create_log_handler(name):
    """
    Create a new log handler for the given global log configuration
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    global LOG_FILE_HANDLER #pylint: disable=global-statement
    if LOG_FILE_HANDLER is None and LOG_FILE_NAME is not None and LOG_FILE_NAME != "":
        #create log file path and file logger
        try:
            os.makedirs(LOG_FILE_PATH)
            logger.debug("Logging directory created: ./%s", LOG_FILE_PATH)
        except FileExistsError:
            #logger.debug("Logging directory exist already: ./%s", LOG_FILE_PATH)
            pass
        except OSError:
            logger.error("Can not create Logging directory: ./%s", LOG_FILE_PATH)

        # create time rotating logger for log files
        LOG_FILE_HANDLER = logging.handlers.TimedRotatingFileHandler(
            os.path.join(LOG_FILE_PATH, LOG_FILE_NAME),
            when=LOG_FILE_ROTATE,
            backupCount=LOG_FILE_BACKUP
        )
        # Set the formatter for the logging handler
        LOG_FILE_HANDLER.setFormatter(
            logging.Formatter(LOG_FORMAT)
        )
        LOG_FILE_HANDLER.setLevel(LOG_LEVEL)
        logger.debug("Created new file handler (%s)", LOG_FILE_HANDLER)

    if LOG_FILE_HANDLER is not None:
        logger.addHandler(LOG_FILE_HANDLER)

    return logger
