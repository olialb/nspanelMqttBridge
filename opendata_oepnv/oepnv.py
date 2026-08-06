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
Module implements a class to connect with opendata-oepnv to get station depature list
"""

import json
import datetime
import time
import requests

#project specific imports
from file_logger import file_logger as FLOGGER

#
# globals
#
URL = "https://openservice-test.vrr.de/openservice"
OUTPUT_FORMAT="rapidJSON"
JSON_VERSION="10.4.18.18"
MAX_DEPARTURES=20
MAX_TRIPS=4

#global logger
LOG = FLOGGER.create_log_handler( "OpendataOEPNV:" )

class OpendataOEPNVObject(): #pylint: disable=too-few-public-methods
    """
    Base class for all open data Json objects
    """
    #evalute time delta between local time and server time (utc)
    serverTimeDelta =  time.timezone if (time.localtime().tm_isdst == 0) else time.altzone

    @classmethod
    def get_json(cls, json_data, attribute, default=None):
        """
        returns an value for an json attribute or the default value if it does not exist
        """
        if attribute in json_data:
            return json_data[attribute]
        #LOG.debug("Attribute '%s' does not exist in json data", attribute)
        return default

    def __init__(self, json_data):
        self.id = self.get_json(json_data, "id")
        self.name = self.get_json(json_data, "name")

class OpendataOEPNVPlace(OpendataOEPNVObject): #pylint: disable=too-few-public-methods
    """
    Represent a Place in the OPNV network
    """
    def __init__(self, json_data):
        super().__init__(json_data)
        self.type = self.get_json(json_data, "type")


class OpendataOEPNVLocation(OpendataOEPNVObject): #pylint: disable=too-few-public-methods
    """
    Represent a location in the OPNV network
    """
    def __init__(self, json_data):
        super().__init__(json_data)
        self.short_name = self.get_json(json_data, "disassembledName")
        self.type = self.get_json(json_data, "type")
        self.coord = self.get_json(json_data, "coord")
        self.id = self.get_json(json_data, "id")
        if "parent" in json_data:
            self.parent = OpendataOEPNVPlace(json_data["parent"])
        else:
            self.parent = None

class OpendataOEPNVTransportation(OpendataOEPNVObject): #pylint: disable=too-few-public-methods
    """
    Represent a transportation in the OPNV network
    """
    def __init__(self, json_data):
        super().__init__(json_data)
        self.product_name = "Unkown" #Example: "S-Bahn"
        self.product_icon_id = -1
        self.product_id = -1
        self.destination_name = "Unknown" #Example: "Duisburg Hbf"
        self.destination_id = -1
        self.name = self.get_json(json_data, "name") #Example: "U-Bahn U7"
        self.short_name = self.get_json(json_data, "disassembledName")  #Example: "U7"
        if "product" in json_data:
            self.product_name = self.get_json(json_data["product"], "name",self.product_name)
            self.product_id = self.get_json(json_data["product"], "id", self.product_id)
            self.product_icon_id = self.get_json(json_data["product"], "iconId", self.product_icon_id)
        if "destination" in json_data:
            self.destination_name = self.get_json(json_data["destination"], "name", self.destination_name)
            self.destination_id = self.get_json(json_data["destination"], "id", self.destination_id)

class OpendataOEPNVStopEvent(OpendataOEPNVObject):
    """
    Represent a StopEvent in the OPNV network
    """
    def __init__(self, json_data):
        #this json opject has no name or id
        super().__init__({"name": "Stop", "id": -1})
        if "departureTimePlanned" in json_data:
            self.departure_time_planned = datetime.datetime.fromisoformat(json_data["departureTimePlanned"])
        else:
            self.departure_time_planned = None
        if "departureTimeEstimated" in json_data:
            self.departure_time_estimated = datetime.datetime.fromisoformat(json_data["departureTimeEstimated"])
        else:
            self.departure_time_estimated = self.departure_time_planned
        self.location_id = -1
        if "location" in json_data:
            self.location_id = self.get_json(json_data["location"], "id")
        if "transportation" in json_data:
            self.transportation = OpendataOEPNVTransportation(json_data["transportation"])

    def __lt__(self, other):
        """
        Sort the class by estimated depatrure time
        """
        return self.departure_time_estimated < other.departure_time_estimated

class OpendataOEPNVLeg(OpendataOEPNVObject):
    """
    Represent a Leg in the OPNV network
    """
    def __init__(self, json_data):
        #this json opject has no name or id
        super().__init__({"name": "Leg", "id": -1})
        if "origin" in json_data:
            origin_json = json_data["origin"]
            if "departureTimePlanned" in origin_json:
                self.departure_time_planned = datetime.datetime.fromisoformat(origin_json["departureTimePlanned"])
            else:
                self.departure_time_planned = None
            if "departureTimeEstimated" in origin_json:
                self.departure_time_estimated = datetime.datetime.fromisoformat(origin_json["departureTimeEstimated"])
            else:
                self.departure_time_estimated = self.departure_time_planned
        self.transportation = None
        if "transportation" in json_data:
            self.transportation = OpendataOEPNVTransportation(json_data["transportation"])
        self.stops = []
        if "stopSequence" in json_data:
            self.stops = json_data["stopSequence"]

    def get_departure_time(self):
        """
        returns the departure time of the leg. If estimated time is available, it is used, otherwise the planned time is used.
        time is corrected by the server time delta to get local time
        """
        departure = self.departure_time_planned
        if self.departure_time_estimated is not None:
            departure = self.departure_time_estimated
        return departure - datetime.timedelta(seconds=self.serverTimeDelta)

    def __lt__(self, other):
        """
        Sort the class by estimated depatrure time
        """
        return self.departure_time_estimated < other.departure_time_estimated

class OpendataOEPNVJourney(OpendataOEPNVObject): #pylint: disable=too-few-public-methods
    """
    Represent a Journey in the OPNV network
    """
    def __init__(self, json_data):
        #this json opject has no name or id
        super().__init__({"name": "Journey", "id": -1})
        if "legs" not in json_data:
            LOG.warning("OpendataOEPNVJourney: JSON data contains no legs")
            return
        self.legs = []
        self.interchanges = self.get_json(json_data, "interchanges", 0)
        self.rating = self.get_json(json_data, "rating", 0)
        self.is_additional = self.get_json(json_data, "isAdditional", False)

        for leg_json in json_data["legs"]:
            self.legs.append( OpendataOEPNVLeg(leg_json) )

#server class
class OpendataOEPNV():
    """
    represent a connection to opendata oepnv
    """

    def __init__(self, timeout: int = 5):
        """
        Contruct all data for a connection
        """

        #create all attributes
        self.url = URL
        self.port = 443 #Use HTTPS
        self.timeout = timeout
        self.session = requests.Session()

        LOG.debug( "OpendataOEPNV class created.")

    def get_dm_request(self, place: str, name: str, max_dep: int =MAX_DEPARTURES)-> dict:
        """
        get the departures json from the opendata server
        """
        #html parameters to get the deparure data for a stop
        params = {
            "outputFormat": OUTPUT_FORMAT,
            "version": JSON_VERSION,
            "place_dm": place,
            "type_dm" : "stop",
            "name_dm" : name,
            "mode" : "direct",
            "limit" : max_dep,
            "useRealtime": 1
        }
        #get the data from server
        try:
            response =  self.session.get( self.url+"/XML_DM_REQUEST", timeout=self.timeout,
                                headers={},
                                params=params,
                                #verify=False
                                )
            return response.json()
        except requests.RequestException as error:
            LOG.error( "Exception while getting item data: %s", error)
            return json.loads( '{ "error": {"message": "Connection error!"} }' )

    def get_trip_request(self, origin: str, destination: str, time_origin:str = None, max_trips: int =MAX_TRIPS)-> dict:
        """
        get trip data. Maximal 4 trips are
        """
        #html parameters to get the deparure data for a stop
        params = {
            "outputFormat": OUTPUT_FORMAT,
            "version": JSON_VERSION,
            "tripReductionMacro" : 1,
            "type_origin": "any",
            "name_origin": origin,
            "type_destination": "any",
            "name_destination": destination,
            "calcNumberOfTrips": max_trips,
            "useRealtime": 1
        }
        if time_origin is not None:
            params["itdTime_origin"]=time_origin
        #get the data from server
        try:
            response =  self.session.get( self.url+"/XML_TRIP_REQUEST2", timeout=self.timeout,
                                headers={},
                                params=params,
                                #verify=False
                                )
            return response.json()
        except requests.RequestException as error:
            LOG.error( "Exception while getting item data: %s", error)
            return json.loads( '{ "error": {"message": "Connection error!"} }' )

class OpendataOEPNVStation(): #pylint: disable=too-few-public-methods
    """
    Represent a station in the OPNV network
    """
    def __init__(self, server: OpendataOEPNV, place: str, name:str, max_departures: int = MAX_DEPARTURES):
        self.server = server
        self.place = place
        self.name = name
        self.max_departures = max_departures
        self.location = None
        self.stop_events = []
        self.update()

    def update(self):
        """
        update station information from open data server
        """
        json_data = self.server.get_dm_request( self.place, self.name, self.max_departures )

        if not "error" in json_data:
            if "locations" in json_data:
                self.location = OpendataOEPNVLocation(json_data["locations"][0])
                if len(json_data["locations"]) > 1:
                    LOG.warning("OpendataOEPNVStation: JSON data contains more than one location")
            self.stop_events = []
            if "stopEvents" in json_data:
                for stop_json in json_data["stopEvents"]:
                    stop_event = OpendataOEPNVStopEvent(stop_json)
                    self.stop_events.append( stop_event )
                #sort the list by estimated departure time
                self.stop_events.sort()
        else:
            LOG.error("Could not update departure list")

class OpendataOEPNVTrips(): #pylint: disable=too-few-public-methods
    """
    Represent a trip in the OPNV network
    """
    def __init__(self, server: OpendataOEPNV,
                 origin: str, destination:str,
                 time_origin: None = None):
        self.server = server
        self.origin = origin
        self.destination = destination
        self.time_origin = time_origin
        self.max_trips = MAX_TRIPS
        self.trips = []
        self.update()

    def update(self):
        """
        update trip information from open data server
        """
        json_data = self.server.get_trip_request( self.origin, self.destination, self.time_origin, self.max_trips )

        if not "error" in json_data:
            if "journeys" in json_data:
                for journey_json in json_data["journeys"]:
                    self.trips.append( OpendataOEPNVJourney(journey_json))
        else:
            LOG.error("Could not update trip list.")
