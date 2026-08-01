# python
# This file is part of the NspanelMqttBridge distribution
# (https://github.com/olialb/NspanelMqttBridge).
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
Module implements an observer of the card.yaml files to dynamilly update the configuration of the NspanelMqttBridge.
It uses the watchdog library to monitor changes in the specified directory and triggers actions when files are created or deleted.
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#project specific imports
from file_logger import file_logger as FLOGGER

#global variables
STABLE_TICKS = 3 #number of ticks to wait for stable state after a change in the yaml files before resyncing the card configuration. This can be used to avoid multiple resyncs when multiple changes are made in a short time.

class CardConfigFileObserver(FileSystemEventHandler):
    """
    Observer class based on the watchdog library to monitor changes in the specified directory.
    """
    #create global log handler for the file observer
    log =  FLOGGER.create_log_handler("FileObserver:")

    def __init__(self, path, call_resync):
        """
        Initialize the FileObserver with a specific path to monitor.
        :param path: The directory path to monitor for changes.
        """
        super().__init__()
        self.observer = Observer()
        self.path = path
        self.call_resync = call_resync
        self.ext = ".yaml"
        self.observer.schedule(self, path=path, recursive=False)
        self.stable_counter = 0

    def time_tick(self):
        """
        Method to be called periodically to check for stable state of the files.
        It can be used to trigger actions after a certain number of ticks without changes.
        """
        if self.stable_counter > 0:
            self.stable_counter -= 1
            if self.stable_counter == 0:
                self.resync_card_config()

    def start(self):
        """
        Start the observer to begin monitoring the directory.
        """
        self.observer.start()
        self.log.info("File observer runs on folder: '%s'", self.path)

    def stop(self):
        """
        Stop the observer from monitoring the directory.
        """
        self.observer.stop()
        self.observer.join()

    def resync_card_config(self):
        """
        Resync all card data with yaml files
        """
        self.log.info("Resyncing card configuration...")
        self.call_resync() #call resync at start to load existing yaml files


    def on_created(self, event):
        """
        Triggered when a new file is created in the monitored directory.
        """
        if not event.is_directory and event.src_path.endswith(self.ext):
            self.log.debug("New card file detected: %s", event.src_path)
            self.stable_counter = STABLE_TICKS  # Set counter to wait for stable state before resyncing


    def on_deleted(self, event):
        """
        Triggered when a file is deleted from the monitored directory.
        """
        if not event.is_directory and event.src_path.endswith(self.ext):
            self.log.debug("Card file deleted: %s", event.src_path)
            self.stable_counter = STABLE_TICKS  # Set counter to wait for stable state before resyncing

    def on_modified(self, event):
        """
        Triggered when a file is modified in the monitored directory.
        """
        if not event.is_directory and event.src_path.endswith(self.ext):
            self.log.debug("Card file modified: %s", event.src_path)
            self.stable_counter = STABLE_TICKS  # Set counter to wait for stable state before resyncing

    def on_moved(self, event):
        """
        Triggered when a file is moved or renamed in the monitored directory.
        """
        if not event.is_directory:
            self.log.debug("Card file moved: %s", event.src_path)
            self.stable_counter = STABLE_TICKS  # Set counter to wait for stable state before resyncing
