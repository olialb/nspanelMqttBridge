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
config_file = "nspanelMqttBridge.ini"  # name of the ini file

# import from the configuration file only the feature configuraion
logging_cfg = configparser.ConfigParser()
#set logging default values
log_file_path = "log"
log_file_name = None
log_file_backup =  5
log_file_rotate = "midnight"
log_level_console = "WARNING"  # this would be default basicConfig() setting
log_format = "[%(asctime)s] %(levelname)7s %(name)-20s %(message)s"

log_file_handler = None  # We only need ONE file-handler instance! After creating it once, we set it to ALL the loggers.

# try to open ini file
try:
    if os.path.exists(config_file) is True:
        logging_cfg.read(config_file)
except OSError:
    print(f"Error while reading ini file: {config_file}")
    sys.exit()

# read logging config
log_level = logging_cfg["logging"]["level"]
if log_level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    raise KeyError(log_level)
log_level = log_level.upper()

if "consoleLevel" in logging_cfg["logging"]:
    log_level_console = logging_cfg["logging"]["consoleLevel"]
    if log_level_console.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise KeyError(log_level_console)
    log_level_console = log_level_console.upper()

if "path" in logging_cfg["logging"]:
    log_file_path = logging_cfg["logging"]["path"]
if "file" in logging_cfg["logging"]:
    log_file_name = logging_cfg["logging"]["file"]
if "format" in logging_cfg["logging"]:
    log_format = logging_cfg["logging"]["format"]
if "backup" in logging_cfg["logging"]:
    log_file_backup = int(logging_cfg["logging"]["backup"])
if "rotate" in logging_cfg["logging"]:
    log_file_rotate =logging_cfg["logging"]["rotate"]

root_logger = logging.getLogger() #get root logger
#root_logger.setLevel(LOG_LEVEL)

if log_file_name is not None and log_file_name != "":
    #create log file path and file logger
    try:
        os.makedirs(log_file_path)
        root_logger.debug("Logging directory created: ./%s", log_file_path)
    except FileExistsError:
        #logger.debug("Logging directory exist already: ./%s", LOG_FILE_PATH)
        pass
    except OSError:
        root_logger.error("Can not create Logging directory: ./%s", log_file_path)

    # create time rotating logger for log files
    log_file_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(log_file_path, log_file_name),
        when=log_file_rotate,
        backupCount=log_file_backup
    )
    # Set the formatter for the logging handler
    log_file_handler.setFormatter(
        logging.Formatter(log_format)
    )
    log_file_handler.setLevel(log_level)

    #create a stream handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter( logging.Formatter(log_format) )
    console_handler.setLevel(log_level_console)

    #add the file handler to the root logger
    root_logger.addHandler(log_file_handler)
    root_logger.addHandler(console_handler)

#logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
# after basicConfig, there is a root logger with exactly ONE handler (console output)
#logging.root.handlers[0].setLevel(LOG_LEVEL_CONSOLE)  # allows further reduction of console output

def create_log_handler(name):
    """
    Create a new log handler for the given global log configuration
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    #if log_file_handler is not None:
    #    logger.addHandler(log_file_handler)

    root_logger.debug("Created new logger (%s)", name)
    return logger

def global_logger():
    """
    Return the global logger instance
    """
    return root_logger