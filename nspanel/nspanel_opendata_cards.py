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
Module implements a MQTT client as bridge to openhab for NsPanels with lovelace ui
This file contain the differnt cards shown in the panel.
"""

#general imports
import datetime
import threading
import time

# project specific imports:
from nspanel.nspanel_globals import name_to_16bit_color
from nspanel.nspanel_base_cards import NSPanelCard, NSPanelCardWithNav
from opendata_oepnv.oepnv import OpendataOEPNV, OpendataOEPNVStation, OpendataOEPNVTrips
from skin import skin

#
# global constants
#

#
# Class definitions
#
class NSPanelCardOEPNVBase(NSPanelCardWithNav):
    """
    Represent an card of type CardSchedule in lovelace ui for NSPanels.
    It shows the departures of a ÖPNV station
    """
    MY_TYPE = NSPanelCard.CARD_DEPARTURES
    #Server object
    openDataServer = None

    def __init__(self, name, group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, group )

        if self.openDataServer is None:
            #No Server object exists. Create an Server object
            NSPanelCardOEPNVBase.openDataServer = OpendataOEPNV()

class NSPanelCardOEPNVDepartures(NSPanelCardOEPNVBase):
    """
    Represent an card of type CardSchedule in lovelace ui for NSPanels.
    It shows the departures of a ÖPNV station
    """
    MY_TYPE = NSPanelCard.CARD_SCHEDULE
    SCHEDULE_UPDATE_INTERVAL = 60  # seconds
    MAX_SLOTS = 6

    def __init__(self, name, group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, group )
        self.station = None
        self.place = "F"  # default place
        self.station_name = "Konstablerwache"  # default station name
        self.trip_requests = []
        self.thread_running = False
        self.thread_semaphore = threading.Semaphore()
        self.payload_semaphore = threading.Semaphore()
        self.schedule_payload = "~text~slotName~\uF16F~65535~Waiting for data~..."


    def create_slot_payload(self, icon, icon_color, dep_time, product, destination):
        """
        create a payload for a single slot
        """
        return f"~text~slotName~{icon}~{icon_color}~{product}-{destination}~{dep_time}"

    def create_schedule_payload(self):
        """
        create upstate payload for all slots
        """
        payload = ""
        schedule = {}

        for trip_request in self.trip_requests:
            for trip in trip_request.trips:
                if len(trip.legs) > 0:
                    dep_time = trip.legs[0].get_departure_time()
                    dep_time_str = dep_time.strftime("%Y%m%d%H%M")
                    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M")
                    if dep_time_str < now_str:
                        continue
                    if trip.legs[0].transportation.product_id in [-1, None]:
                        self.log.debug("Trip with unknown product id found for trip %s", trip.legs[0].transportation.name)
                        continue
                    while dep_time in schedule:
                        #make dep_time unique
                        dep_time += datetime.timedelta(milliseconds=1)
                    schedule[dep_time] = {}
                    schedule[dep_time]["icon"] = skin.key( "opendataProductIcons", str(trip.legs[0].transportation.product_icon_id) )
                    schedule[dep_time]["iconColor"] = str(name_to_16bit_color(skin.key( "opendataProductIconColors", str(trip.legs[0].transportation.product_icon_id) )))
                    schedule[dep_time]["name"] = trip.legs[0].transportation.short_name
                    schedule[dep_time]["destination"] = trip.legs[-1].transportation.destination_name

        # sort the schedule by departure time
        schedule = dict(sorted(schedule.items()))

        # create the payload string
        slot_num = 0
        for dep_time in schedule:
            #calculate in how many minutes the departure is
            dep_time_seconds = dep_time.hour * 60 * 60 + dep_time.minute * 60 + dep_time.second
            now = datetime.datetime.now()
            now_seconds = now.hour * 60 * 60 + now.minute * 60 + now.second
            if dep_time_seconds < now_seconds and now_seconds - dep_time_seconds > 60:
                # departure is on next day
                dep_time_seconds += 24 * 60 * 60
            minutes_until_departure = (dep_time_seconds - now_seconds) / 60
            if int(minutes_until_departure) <= 0:
                #do not show entries with 0 minutes until departure
                continue
            payload += self.create_slot_payload( schedule[dep_time]["icon"], schedule[dep_time]["iconColor"], f"{int(minutes_until_departure)} min", schedule[dep_time]["name"], schedule[dep_time]["destination"] )
            slot_num += 1
            if slot_num >= self.MAX_SLOTS:
                break

        self.log.debug("Schedule payload created: %s", payload)
        with self.payload_semaphore:
            self.schedule_payload = payload

    def thread_create_schedule(self):
        """
        Thread to request cyclicly the schedule from the open data server
        """
        self.log.debug("NSPanelCardOEPNVDepartures: Thread to request schedule started")
        self.thread_running = True
        self.thread_semaphore.release()
        timer = 0
        data_created = False
        #main loop of the thread
        while self.thread_running:
            if timer <= 0:
                #create schedule data for the station
                with self.thread_semaphore:
                    self.station = OpendataOEPNVStation( self.openDataServer, self.place, self.station_name)
                    if self.station.location is not None:
                        self.log.debug("Station for place '%s' and station '%s' found!", self.place, self.station_name)
                        if len(self.station.stop_events) > 0:
                            #now find the trips to each destination in the station
                            destination_list = []
                            self.trip_requests = []
                            for stop_event in self.station.stop_events:
                                if stop_event.transportation.destination_name not in destination_list:
                                    destination_list.append(stop_event.transportation.destination_name)
                                    self.trip_requests.append( OpendataOEPNVTrips( self.openDataServer, stop_event.location_id, stop_event.transportation.destination_id) )
                            #update card contend if card is active
                            data_created = True
                        else:
                            self.schedule_payload = "~text~slotName~\uF16F~65535~No data for this station~..."
                    else:
                        self.log.error("Station for place '%s' and station '%s' not found!", self.place, self.station_name)
                        self.schedule_payload = "~text~slotName~\uF16F~65535~No station found~..."
                if data_created:
                    self.create_schedule_payload()
                #inform all panels that the content has been updated
                for panel in self.all_panels.values():
                    panel.content_update_info(self.name)
                timer = self.SCHEDULE_UPDATE_INTERVAL
            time.sleep(1)
            timer -= 1

        self.log.debug("NSPanelCardOEPNVDepartures: Thread to request schedule will be stopped")


    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        ret = super().load_card_yaml( card_yaml )

        if "station" in card_yaml and card_yaml["station"] is not None:
            station_def = card_yaml["station"].split(",")
            if len(station_def) >= 2:
                self.place = station_def[0]
                self.station_name = station_def[1]
                #start the thread to request the schedule
                thread = threading.Thread(target=self.thread_create_schedule)
                self.thread_semaphore.acquire() #pylint: disable=consider-using-with
                thread.start()
            else:
                self.log.error("Wrong station definition: '%s'. Must be 'place,station_name'!", card_yaml["station"])
                ret = False
        return ret

    def destroy(self):
        """
        Stop the thread to request the schedule when the destructor is called
        """
        with self.thread_semaphore:
            self.log.debug("NSPanelCardOEPNVDepartures: Stopping thread to request schedule")
            self.thread_running = False
        #call base class
        super().destroy()

    def create_update_payload(self, compatibility=NSPanelCard.COMPATIBILITY_MODE_DEFAULT):
        """
        Create nav card payload
        """
        with self.payload_semaphore:
            payload = super().create_update_payload(compatibility) + self.schedule_payload
        return payload


#add this card class type to the factory
NSPanelCard.card_types[NSPanelCard.CARD_DEPARTURES] = NSPanelCardOEPNVDepartures

class NSPanelCardOEPNVDepartures2(NSPanelCardOEPNVDepartures):
    """
    Represent an card of type CardEntities with a departure Schedule in lovelace ui for NSPanels.
    It shows the departures of a ÖPNV station
    """
    MY_TYPE = NSPanelCard.CARD_ENTITIES
    MAX_SLOTS = 6

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCard.CARD_DEPARTURES2] = NSPanelCardOEPNVDepartures2

