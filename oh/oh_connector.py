# python
#
# This file is part of the nspanelMqttBridge distribution:
# (https://github.com/olialb/nspanelMqttBridge).
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
Module implements a class to connect with openhab items
"""

import json
import datetime
import threading
import requests

#project specific imports
from file_logger import file_logger as FLOGGER

#
# globals
#

#
# helper functions
#
def oh_options_to_dict( options ):
    """
    builds a simpe dictionary from value and labels in oh options list
    """
    try:
        d = {}
        for entry in options:
            d[entry["value"]] = entry["label"]
    except KeyError:
        return None
    return d


#rest api session class
class OHConnection():
    """
    represent a connection to openhab
    """

    def __init__(self, host, port, timeout=5, api_key=None ):
        """
        Contruct all data for a connection
        """
        self.host = host
        self.port = port
        self.url = self.host +':' + str(self.port)
        self.timeout = timeout
        self.session = requests.Session()
        #configure authentication if needed
        if api_key is not None and api_key != "":
            self.session.auth = ( api_key, "" )

    def post_item( self, name, state ):
        """
        post an item state
        """
        #In case of https the certificate from openHAB should not be checked
        return self.session.post( self.url + "/rest/items/"+ name,
                                          headers={ "Content-Type": "text/plain"},
                                          data=state, timeout=self.timeout, verify=False)
    def get_item(self, name):
        """
        get item json for given item
        """
        #In case of https the certificate from openHAB should not be checked
        return self.session.get( self.url + "/rest/items/" + name, timeout=self.timeout, verify=False)

    def get_persistance(self, name, start, end):
        """
        get persistance json for the given item and period
        """
        params = { "starttime": start.isoformat(), "endtime": end.isoformat()}
        #In case of https the certificate from openHAB should not be checked
        return self.session.get( self.url + "/rest/persistence/items/" + name, timeout=self.timeout,
                                headers={ "Content-Type": "application/json"},
                                params=params,
                                verify=False)
#
# class implementation
#
class OHItem: #pylint: disable=too-many-instance-attributes
    """
    Class represent one item in openhab
    """
    OHConnection=None
    #create global item logger
    log = FLOGGER.create_log_handler( "OHItem:" )

    def __init__(self, name, update_callback=None):
        """
        Create an new item
        """
        self.name = name
        #list of all update callbacks which should be triggered whan state of item change
        self.update_callbacks = []
        if update_callback is not None:
            self.update_callbacks.append(update_callback)
        self.state = "None"
        self.state_int = "None"
        self.state_formated = "None"
        self.type = "None"
        self.group_type = None
        self.label = "No OH Label"
        self.unit = ""
        self.pattern = None
        self.last_state_change = None
        self.options = {}

        self.log.debug("OHItem '%s' constructed!", name)

    def get_item_json( self ):
        """
        makes an rest api request for an item state to openhab and returns the json response
        """
        self.log.debug("Get item_json for '%s'", self.name)
        try:
            response = self.OHConnection.get_item( self.name )
            return response.json()
        except requests.RequestException as error:
            self.log.error( "Exception while getting item data: %s", error)
            return json.loads( '{ "error": {"message": "OH connection error!"} }' )

    def toggle_oh_state( self,options=None ): #pylint: disable=too-many-branches, too-many-return-statements
        """
        toggles the state of an openhab item if possible
        """
        if self.type == "Switch" or self.group_type == "Switch":
            if self.state == 'ON':
                return 'OFF'
            return 'ON'
        if options is not None:
            state = str(state) #be shure that state is a string
            if state in options:
                #toggle threw the option list
                index = options.index(state)
                if index+1 < len(options):
                    return options[index+1]
                return options[0]
            if len(options) > 0:
                return options[0]
            return None
        if self.type == "Dimmer" or self.group_type == "Dimmer":
            if float(self.state) == 0:
                return '100'
            return '0'
        return None

    def toggle_item_state(self, local_options=None):
        """
        toggle the state of the item if possible
        """
        self.log.debug("Toggle state of item %s", self.name)
        if local_options is not None:
            new_state = self.toggle_oh_state(list(local_options.keys()))
        else:
            new_state = self.toggle_oh_state(list(self.options.keys()))
        if new_state is not None and new_state != self.state:
            return self.set_item_state( new_state )
        self.log.warning("Item state %s of item %s can not be toggled", self.state, self.name)
        return False

    def set_item_state(self, state):
        """
        updates the state of an in openhab
        """
        self.log.debug("Send %s to item %s", state, self.name)
        try:
            self.OHConnection.post_item( self.name, state)
        except requests.RequestException as error:
            self.log.error( "Exception while setting item state: %s", error)
            return False
        return True

    def update_item(self, local_options=None): #pylint: disable=too-many-branches
        """
        update the item if needed and request update from openhab
        """
        item_json = self.get_item_json()
        self.log.debug("New Item state of '%s': %s", self.name, str(item_json))
        if "error" not in item_json:
            #valid item data receiver
            self.state = item_json["state"]
            self.type = item_json["type"].split(":")[0] #take only the type name without unit of measurements
            if "unitSymbol" in item_json:
                self.unit = item_json["unitSymbol"]
            if "pattern" in item_json:
                self.pattern = item_json["pattern"]
            if "label" in item_json and item_json["label"] != "":
                self.label = item_json["label"]
            if "groupType" in item_json and item_json["groupType"] != "":
                self.group_type = item_json["groupType"]
            if "lastStateChange" in item_json and item_json["lastStateChange"] is not None:
                self.last_state_change = datetime.datetime.fromtimestamp(item_json["lastStateChange"]/1e3)
            #evaluate options in this item:
            if local_options is not None:
                self.options = local_options
            else:
                if "stateDescription" in item_json and "options" in item_json["stateDescription"]:
                    #we have options defined take them in the item attributes
                    self.options = oh_options_to_dict(item_json["stateDescription"]["options"])
                    if self.options is None:
                        self.log.warning("Openhab options not in known format. Can not use them.")
            #Evaluate if state can/must be formated further
            try:
                #check for opehab number value types. Split the dimension from the type
                if item_json["type"].split(":")[0] in ["Number", "Dimmer", "Rollershutter" ]:
                    self.state_int = self.state.split('.')[0]
                    self.state = float(self.state.split(" ")[0]) #use only first part of state in case there is a dimension
                    value = self.state
                else:
                    if self.state in self.options:
                        #take the value from options dictionary
                        value = self.options[self.state]
                    else:
                        value = self.state
                if "stateDescription" in item_json and "pattern" in item_json["stateDescription"]:
                    self.state_formated = item_json["stateDescription"]["pattern"] % value
                else:
                    self.state_formated = self.state
            except (ValueError,KeyError,TypeError) as error:
                self.log.debug("Could not format item data for item '%s'. Got error: %s", self.name, error)
                self.state_formated = "format error"
                return "None"
            return self.state
        self.log.error("Could not get item data for item '%s'. Got error: %s", self.name, item_json["error"]["message"])
        return "None"

    def persistance_data_string(self, start_time, end_time):
        """
        returns the persitance data for this item in the last period in min
        """
        values = []

        persist_json = self.OHConnection.get_persistance( self.name, start_time, end_time ).json()

        if "error" not in persist_json:
            for value_json in persist_json["data"]:
                try:
                    entry = {}
                    entry["time"] = datetime.datetime.fromtimestamp(value_json["time"]/1e3)
                    if value_json["state"] in self.options:
                        #take the value from options dictionary
                        entry["state"] = self.options[value_json["state"]]
                    else:
                        entry["state"] = value_json["state"]
                    values.append(entry)
                except (ValueError,TypeError):
                    self.log.error("Could interpret persistance data for item '%s'. Got error: %s", self.name, str(value_json))
                    return None
        else:
            self.log.error("Could not get persistance data for item '%s'. Got error: %s", self.name, persist_json["error"]["message"])
            return None
        return values

    def persistance_data_float(self, start_time, end_time):
        """
        returns the persitance data for this item in the last period in min
        """
        values = []

        persist_json = self.OHConnection.get_persistance( self.name, start_time, end_time ).json()

        if "error" not in persist_json:
            for value_json in persist_json["data"]:
                try:
                    entry = {}
                    entry["time"] = datetime.datetime.fromtimestamp(value_json["time"]/1e3)
                    entry["state"] = float(value_json["state"])
                    values.append(entry)
                except (ValueError,TypeError):
                    self.log.error("Could interpret persistance data for item '%s'. Got error: %s", self.name, str(value_json))
                    return None
        else:
            self.log.error("Could not get persistance data for item '%s'. Got error: %s", self.name, persist_json["error"]["message"])
            return None
        return values

class OHItemDB:
    """
    Database for managing OpenHAB items
    """
    #type for items which could ne be found in oh
    OH_ERROR_TYPE = "_error_"

    #global OH ItemDB log handler
    log = FLOGGER.create_log_handler( "OHItemDB" )

    def __init__(self, host, port, timeout=5, api_key=None ):
        """
        creates a data base with all items in the referenced openhab instance
        """
        #create global connection object
        self.oh_connection = OHConnection(host, port, timeout=timeout, api_key=api_key)

        OHItem.OHConnection = self.oh_connection
        self.listner_active = False
        self.listener_count = 0
        self.listner = threading.Semaphore()
        #global list of all item objects
        self.oh_items = {}

        #create logger
        self.log.debug("OHItemDB Constructed!")

    def item_exits(self, name):
        """
        returns true when the item exist in this DB
        """
        return name in self.oh_items

    def thread_item_listener( self ):
        """
        listen on state changes for the items in the list

        """
        #create a new session for this thread
        self.listener_count = self.listener_count + 1
        self.listner.release()
        session = requests.Session()
        self.log.debug("Item listner thread started: %d.",self.listener_count)
        result = session.get(self.oh_connection.url + "/rest/events?topics=openhab/items/*/statechanged", stream=True, verify=False)
        #te following for loop runs until the connection is established to openhab
        for line in result.iter_lines(): #pylint: disable=too-many-nested-blocks
            # filter out keep-alive new lines
            if line:
                decoded_line = line.decode('utf-8')
                #check for data lines:
                if decoded_line.startswith("data:"):
                    #seams to be an item state change event
                    json_data = json.loads(decoded_line[len("data:"):])
                    if "topic" in json_data:
                        topic_data = json_data["topic"].split('/')
                        if len(topic_data) >= 4 and topic_data[0] == "openhab" and topic_data[1] == "items" and topic_data[-1] == "statechanged":
                            #its an openhab state change for an item!
                            #self.log.debug("Listener thread Item event: %s", topic_data[2])
                            if topic_data[2] in self.oh_items:
                                item = self.oh_items[topic_data[2]]
                                self.log.debug("Listener thread Item event for item in card definition: %s", topic_data[2])
                                for callback in item.update_callbacks:
                                    #inform listners about something has changed
                                    callback()
                with self.listner:
                    if self.listner_active is False:
                        #stop listening
                        break
        self.listener_count = self.listener_count - 1
        self.listner.release()
        self.log.debug("Stop item listner thread: %d.",self.listener_count)

    def connect(self):
        """
        connect to openhab and listen on the items
        """
        self.log.debug("connect")
        self.listner.acquire() #pylint: disable=consider-using-with
        self.listner_active = True
        if self.listener_count <= 0:
            self.log.debug("Create item listner thread")
            #no thread running start a thread
            thread = threading.Thread(target=self.thread_item_listener)
            thread.start()
        else:
            self.listner.release()

    def disconnect( self ):
        """
        disconnect from openhab disconnect item listening
        """
        self.listner_active = False
        self.log.debug("Stop the listner thread")

    def item_factory( self, item_name, update_callback=None ):
        """
        returns an ohItem object for the openhab item with given name
        """
        if item_name in self.oh_items:
            #item with this name exist already
            item = self.oh_items[item_name]
            if update_callback is not None and update_callback not in item.update_callbacks:
                item.update_callbacks.append(update_callback)
            return item
        #for this openhab item exsit no item obeject create one
        item = OHItem( item_name, update_callback )
        self.oh_items[item_name] = item
        return item
