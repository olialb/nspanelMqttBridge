# python
#
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
This file implements the nspanel main classes to interact with different panels
"""

#general imports
from datetime import datetime
import json
import os
import sys
import yaml

# project specific imports:
from nspanel.nspanel_globals import name_to_16bit_color, int2ordinal
from nspanel.nspanel_base_cards import NSPanelCard
from nspanel.nspanel_cards import NSPanelCardScreenSaver
from nspanel.nspanel_card_slots import NsPanelCardSlotOhItem, NSPanelCardSlot
from skin import skin
from file_logger import file_logger as FLOGGER
from lang import translate

#
# global constants
#
SEND_COMMAND_TOPIC = "/cmnd/CustomSend"
SEND_RESTART_TOPIC = "/cmnd/Restart"
RESULT_CUSTOM_RECV="CustomRecv"
RESULT_CUSTOM_SEND="CustomSend"
PAGES_FILE_EXT = '.yaml'
SCREENSAVER_NAME = ".screensaver"


def nspanel_create_oh_connector(host, port, timeout, api_key):
    """
    create on openhab connector
    """
    NSPanelCard.all_connected_panels = {}
    NsPanelCardSlotOhItem.create_openhab_connector(host, port, timeout, api_key)

def nspanel_set_language( path ):
    """
    set the translator for the panels
    """
    translate.set_language_file( path )
    NSPanelCard.set_translator_db( translate.get_translator_db() )
    NSPanelCardSlot.set_translator_db ( translate.get_translator_db() )

def nspanel_set_skin( path ):
    """
    set the skin for the panels
    """
    skin.set_skin_file( path )
    NSPanelCard.set_skin_db( skin.get_skin_db() )
    NSPanelCardSlot.set_skin_db ( skin.get_skin_db() )
#
# Class wich represent one NSPanel instance
#
class NSPanel(): #pylint: disable=too-many-instance-attributes, too-many-public-methods
    """
    NS Panel instance
    """
    CMD_TIME="time~"
    CMD_DATE="date~"
    CMD_DIMMODE="dimmode~"
    CMD_TIMEOUT="timeout~"
    CMD_PAGETYPE="pageType~"

    LOG = FLOGGER.create_log_handler("NSPanel")

    def __init__(self, client, name, topic ):
        #nspanel root topic
        self.topic = topic
        #nspanel name
        self.name = name
        #mqtt client instance
        self.mqtt = client
        #topics unpublished flag
        self.unpublished = True
        #last time and date strings send to panel
        self.last_time = None
        self.last_date = None
        #current visible card
        self.current_card = None
        self.current_group = NSPanelCard.CARDS_HOME
        #command handling
        self._cmd_queue = []
        self._cmd_timeout_counter = 0
        self._time_tick = client.publish_delay
        self._time_cmd_timeout_value = client.cmd_timeout_value
        #cyclic processing scennsaver update
        self.saver_tick_counter = client.saver_update
        #curently active notification card. 0 for none, 1 for first is active
        self.active_notification = 0
        #compatibility mode for ioBroker.nspanel-lovelace-ui fork
        self.compatibility_mode = NSPanelCard.COMPATIBILITY_MODE_DEFAULT

        #logger for this class
        self.log = FLOGGER.create_log_handler(f"NSPanel:{name.upper()}" )

        self.log.debug("NSPanel with name '%s' created.", name)

    def restart(self):
        """
        restart the panel by sending a reset command. This will set the panel in the initial state and trigger a startup event
        """
        self.send_panel_cmd("1", SEND_RESTART_TOPIC)

    def get_status_card( self ):
        """
        returns active status card for screensaver
        """
        return self.mqtt.get_status_card( self.name )

    def get_status_left( self ):
        """
        returns true or false for left status in screensaver
        """
        return self.mqtt.get_status_left( self.name )

    def get_status_right( self ):
        """
        returns true or false for left status in screensaver
        """
        return self.mqtt.get_status_right( self.name )

    def publish_card( self ):
        """
        publish current "group/card" in mqtt broker
        """
        card_path = self.current_group.lower() + '/' + self.current_card.name.lower()
        self.mqtt.set_card(self.name, card_path)

    def publish_version( self, hmi_version, panel_version ):
        """
        publish hmi and panel in mqtt broker
        """
        json_data = {}
        json_data["hmi"] = hmi_version
        json_data["panel"] = panel_version

        self.mqtt.set_version(self.name, json.dumps( json_data))

    def send_mqtt_msg(self, topic, msg):
        """
        sends an mqtt message
        """
        result = self.mqtt.client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            self.log.debug("Send '%s' to topic %s", msg, topic )
            return True
        self.log.error("Failed to send message to topic %s", topic)
        return False

    def set_brightness_mqtt(self, my_config, msg):
        """
        mqtt command to set the brightness
        """
        # Synax OK we can call the command to set the brightness
        msg = msg.strip()

        try:
            value = int(msg)
            value = min(100, max( 0, value ))
        except ValueError as error:
            self.log.warning("Error in '%s' payload %s: %s", my_config["topic"], msg, error)
            return

        #publish the new value
        self.mqtt.set_brightness( self.name, str(value))

        #set new values in panel
        self.send_dimmode()
        self.log.info("Set screen brightness to '%s' for panel '%s'.", str(value), self.name)

    def set_brightness_saver_mqtt(self, my_config, msg):
        """
        mqtt command to set the screensaver brightness
        """
        # Synax OK we can call the command to set the brightness
        msg = msg.strip()

        try:
            value = int(msg)
            value = min(100, max( 0, value ))
        except ValueError as error:
            self.log.warning("Error in '%s' payload %s: %s", my_config["topic"], msg, error)
            return

        #publish the new value
        self.mqtt.set_brightness_saver( self.name, str(value))

        #set new values in panel
        self.send_dimmode()
        self.log.info("Set screensaver brightness to '%s' for panel '%s'.", str(value), self.name)

    def set_timeout_mqtt(self, my_config, msg):
        """
        mqtt command to set the screensaver timeout
        """
        # Synax OK we can call the command to set the brightness
        msg = msg.strip()

        try:
            value = int(msg)
        except ValueError as error:
            self.log.warning("Error in '%s' payload %s: %s", my_config["topic"], msg, error)
            return

        #publish the new value
        self.mqtt.set_timeout( self.name, str(value))

        #set new value in panel
        self.send_timeout()
        self.log.info("Set screensaver timeout to '%s' for panel '%s'.", str(value), self.name)

    def set_card_mqtt(self, my_config, msg):
        """
        mqtt command to set the card in the ns panel
        """
        # Synax OK we can call the command to set the brightness
        msg = msg.strip().lower()

        #set new value in panel
        card = NSPanelCard.card_by_path(msg, self)
        if card is None:
            self.log.warning("Unknown card path '%s' in command payload for '%s'.", msg, my_config["topic"])
        else:
            self.navigate(card)
            #publish the new value
            path = card.group.lower() + '/' + card.name.lower()
            self.mqtt.set_card( self.name, path )
            self.log.info("Navigate to '%s' for panel '%s'.", path, self.name)


    def set_status_left_mqtt(self, my_config, msg):
        """
        mqtt command to set the alarm indicator left on/off
        """
        # Synax OK we can call the command to set the brightness
        msg = msg.strip().upper()

        if msg not in ["ON", "OFF"]:
            self.log.warning("Unknown command payload '%s' in mqtt message for '%s'", msg, my_config["topic"])
            return

        #set new value in panel
        self.mqtt.set_status_left( self.name, msg)

        self.update_status()
        self.log.info("Switch alarm left '%s' for panel '%s'.", msg, self.name)

    def set_status_right_mqtt(self, my_config, msg):
        """
        mqtt command to set the alarm indicator right on/off
        """
        # Synax OK we can call the command to set the brightness
        msg = msg.strip().upper()

        if msg not in ["ON", "OFF"]:
            self.log.warning("Unknown command payload '%s' in mqtt message for '%s'", msg, my_config["topic"])
            return

        #set new value in panel
        self.mqtt.set_status_right( self.name, msg)

        self.update_status()
        self.log.info("Switch alarm right '%s' for panel '%s'.", msg, self.name)

    def set_status_card_mqtt(self, my_config, msg):
        """
        mqtt command to set the current status catd
        """
        msg = msg.strip().lower()

        if msg not in NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP]:
            if msg != NSPanelCard.CARD_DEFAULT_STATUS:
                self.log.warning("Unknown card in command payload '%s' in mqtt message for '%s'", msg, my_config["topic"])
                return
        else:
            if NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP][msg].type != NSPanelCard.CARD_STATUS:
                self.log.warning("Status card '%s' in mqtt message for '%s' should be of type stausCard", msg, my_config["topic"])
                return


        #disconnect old status card:
        if self.get_status_card() in NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP]:
            NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP][self.get_status_card()].disconnect(self)

        #set new value in panel
        self.mqtt.set_status_card( self.name, msg )

        #connect the status card
        if self.get_status_card() in NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP]:
            NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP][self.get_status_card()].connect(self)

        self.update_status()
        self.log.info("Status card changed to '%s' for panel '%s'.", msg, self.name)

    def send_notification(self, heading, notify_text):
        """send a notification to the panel"""
        payload = "notify~"+heading+"~"+notify_text
        self.send_panel_cmd(payload)
        self.log.info("Send notification with heading '%s' and text '%s' to panel '%s'.", heading, notify_text, self.name)


    def set_notification_mqtt(self, my_config, msg):
        """
        mqtt command to set a notification in panel or in the notification queue
        """
        # Synax OK we can call the command to set the brightness
        notify_text = msg.strip().split("|")

        if len(notify_text) < 2:
            self.log.warning("Wrong command payload in mqtt message '%s' for notifications: '%s'",my_config["topic"], msg)
            return
        heading = notify_text[0]
        notify_text = notify_text[1]

        self.send_notification(heading, notify_text)

        #publish the new value
        msg = heading+"|"+notify_text
        self.mqtt.set_notification(self.name, msg )

    def compatibility_check(self, hmi_version, panel_version):
        """
        check the compatibility of the panel and hmi version with this bridge version
        """
        self.log.debug("Panel version: %s, HMI version: %s", panel_version, hmi_version)

        try:
            panel_himi_version = float(hmi_version)
        except ValueError:
            self.log.error("No valid HMI version '%s'", hmi_version)
            return

        if panel_himi_version >= 60:
            self.log.info("HMI version '%s' seams to be from ioBroker.nspanel-lovelace-ui fork. Set compatibility mode to this fork.", hmi_version)
            self.compatibility_mode = NSPanelCard.COMPATIBILITY_MODE_FORK1
        else:
            self.log.info("HMI version '%s' seams to be from original nspanel-lovelace-ui. Set compatibility mode to default.", hmi_version)
            self.compatibility_mode = NSPanelCard.COMPATIBILITY_MODE_DEFAULT

    def panel_callback(self, my_config, msg): #pylint: disable=too-many-return-statements, too-many-branches, too-many-statements
        """
        mqtt messages received from the panel
        """
        # Synax OK we can call the command to set the brightness
        msg = msg.strip()
        try:
            js_payload = json.loads(msg)
        except ValueError:
            self.log.warning("Error parsing json payload: %s", msg)
            return
        #event examples:
        #"event,buttonPress2,Switch_Flurdecke,OnOff,1"
        #"event,buttonPress2,navigate.next,button"
        #"event,buttonPress2,Switch_Esszimmerspots,button"
        #"event,buttonPress2,Switch_Esszimmerspots,brightnessSlider,34"
        #"event,buttonPress2,navigate.prev,button"
        #"event,buttonPress2,screensaver,bExit,2"
        #"event,buttonPress2,screensaver,swipeRight"
        #"event,buttonPress2,slot_0,button"
        #"event,pageOpenDetail,popupShutter,slot_1
        #"event,buttonPress2,popupShutter,bExit"
        #event,buttonPress2,slot_1,down
        #event,buttonPress2,slot_1,tiltOpen
        #event,buttonPress2,slot_2,mode-Test,1
        #event,buttonPress2,popupNotify,notifyAction,yes
        #"event,buttonPress2,slot_0,volumeSlider,28"}
        #event,buttonPress2,CardThermo,tempUpd,55

        if RESULT_CUSTOM_RECV in js_payload: #pylint: disable=too-many-nested-blocks
            #seams to be a relavalnt message
            self.log.debug("Message received from Panel: %s topic: %s", js_payload[RESULT_CUSTOM_RECV], my_config["topic"])
            params = js_payload[RESULT_CUSTOM_RECV].split(',')

            #process events
            if params[0] == "event":
                if params[1] == "startup":
                    #panel made reset. Reinit the panel
                    self.log.debug("'startup' event received from panel. Panel made reset. Reinit it now.")
                    self.compatibility_check(params[2], params[3])
                    self.publish_version( params[2], params[3])
                    self.init_panel()
                    return
                if params[1] == "renderCurrentPage":
                    self.log.debug("'renderCurrentPage' event received from panel. Nothing to do.")
                    return
                #all button Press 2 events
                if params[1] == "buttonPress2":
                    #check for swipe events
                    if len(params) >=4 and params[2] == "screensaver" and params[3] == "swipeRight":
                        self.log.info("Screensaver swipe right event received.")
                        return
                    if len(params) >=4 and params[2] == "screensaver" and params[3] == "swipeLeft":
                        self.log.info("Screensaver swipe left event received.")
                        return
                    if len(params) >=4 and params[2] == "screensaver" and params[3] == "swipeUp":
                        self.log.info("Screensaver swipe up event received.")
                        return
                    if len(params) >=4 and params[2] == "screensaver" and params[3] == "swipeDown":
                        self.log.info("Screensaver swipe down event received.")
                        return
                    #check for screensaver leave event
                    if len(params) >=5 and params[2] == "screensaver" and params[3] == "bExit":
                        if params[4] >= "2":
                            #user want to leave the screensaver screen. Navigate to default page
                            self.log.debug("Leave Screensaver card.")
                            #check if any notification card is active.
                            for card in NSPanelCard.cards_by_group[NSPanelCard.NOTIFY_CARD_GROUP].values():
                                if card.is_active():
                                    #navigate to the notification card
                                    self.navigate(card)
                                    self.active_notification=1
                                    return
                            #navigate to home card for this panel in current group
                            card = NSPanelCard.get_card(self.current_group, self.name)
                            if card is None:
                                card = NSPanelCard.get_first_card(self, self.current_group)
                            self.navigate(card)
                            return
                        #do nothing
                        self.log.debug("Screensaver card event: %s.", params[4])
                        return
                    #check for popup card leave event
                    if len(params) >= 4 and params[2] in ['popupLight','popupShutter','popupInSel','popupThermo','popupTimer'] and params[3] == 'bExit':
                        self.log.debug("Leave popup card '%s.", params[2])
                        self.navigate( self.current_card )
                        return
                    if len(params) >= 4 and params[2] in ['popupNotify']:
                        card = self.current_card.event_popup(params[3:], self.active_notification)
                        if card is not None:
                            self.navigate( card )
                            self.active_notification += 1
                            return
                        #navigate to home card for this panel in current group
                        card = NSPanelCard.get_card(self.current_group, self.name)
                        if card is None:
                            card = NSPanelCard.get_first_card(self, self.current_group)
                        self.navigate(card)
                        return
                    #check for all other card events
                    if len(params) >= 3:
                        #send the now state over rest api
                        new_card = self.current_card.event_button_press( params[2:], self )
                        if new_card is not None:
                            if new_card == self.current_card:
                                #just update content
                                self.update()
                                return
                            #vavigate to new card
                            self.navigate(new_card)
                            return

                #all pop up detail events
                if params[1] == 'pageOpenDetail':
                    #create matching popupcard for this slot
                    if len(params) >= 4 and self.current_card is not None:
                        if self.current_card.popup is None or self.current_card.popup.slot_obj.name != params[3].strip() or self.current_card.popup.MY_TYPE != params[2].strip():
                            #create matching popup card
                            self.current_card.popup_card(params[2], params[3])
                            #check for alternative popups
                            self.popup_select()
                            self.update()
                            self.publish_card()
                            return

                if params[1] == "sleepReached":
                    #switch back to screensaver
                    self.log.debug("Sleep of display reached. Activate Screensaver.")
                    self.navigate(self.get_screensaver_card())
                    return

        if RESULT_CUSTOM_SEND in js_payload:
            if  js_payload[RESULT_CUSTOM_SEND] == "Done":
                self.log.debug("'Done' received from panel. Last command is processed.")
                #command processed. pop next one from queue
                self.pop_cmd()

    def publish_mqtt(self, topic, my_config):
        """
        publish the brightness topic
        """
        msg = my_config["value"]
        # send message to broker
        if self.mqtt.unpublished is True and msg is not None:
            #publish the value
            if self.send_mqtt_msg(topic, msg):
                my_config["value"] = msg

    def send_panel_cmd(self, cmd, cmd_topic=SEND_COMMAND_TOPIC):
        """
        send a command to the nspanel or put it in the queue if timeout is running
        """
        if cmd is None or cmd == "":
            return False

        if self._cmd_timeout_counter > 0:
            #there is currently a command running. Put cmd in the qeueu
            self._cmd_queue.append(cmd)
            return True
        if self.send_mqtt_msg( self.topic+cmd_topic, cmd ):
            self._cmd_timeout_counter = self._time_cmd_timeout_value
            return True
        #something went wrong
        return False

    def pop_cmd(self):
        """
        pops the next command from the command queue
        """
        self._cmd_timeout_counter = 0
        if len(self._cmd_queue) > 0:
            #other commands are pending. Send next one from queue
            self.log.debug("Pop next command from queue: %s", self._cmd_queue[0])
            return self.send_panel_cmd( self._cmd_queue.pop(0))
        return False


    def time_tick(self):
        """
        time tick to supervise command timeouts and other cyclic things
        """
        #check date and time changes
        self.check_time()
        self.check_date()

        #command qeueue processing
        if self._cmd_timeout_counter > self._time_tick:
            self._cmd_timeout_counter = self._cmd_timeout_counter - self._time_tick
        else:
            if self._cmd_timeout_counter != 0:
                self.log.warning("Panel command timeout!")
                self.pop_cmd()
            else:
                self._cmd_timeout_counter = 0

        #waether content update handling
        self.saver_tick_counter = self.saver_tick_counter - self.mqtt.publish_delay
        if self.saver_tick_counter <= 0:
            #update screensaver
            if isinstance(self.current_card, NSPanelCardScreenSaver):
                self.send_panel_cmd( self.current_card.create_update_payload(self.compatibility_mode))
            self.saver_tick_counter = self.mqtt.saver_update

    def check_time(self):
        """
        check if the current time string is different to last published time
        """
        #Cmd format: "time~XX:XX?am" (12h) or "time~XX:XX" (24h)
        now = datetime.now()
        current_time = NSPanel.CMD_TIME+now.strftime(translate.time_templ())
        #current_time = NSPanel.CMD_TIME+"9:00"+ "?am"
        if current_time != self.last_time:
            if self.send_panel_cmd( current_time):
                self.last_time=current_time

    def check_date(self):
        """
        check if the current time string is different to last published time
        """
        now = datetime.now()
        try:
            #try to build date
            weekday= translate.weekdays(now.weekday())
            month = translate.months_short(now.month)
            day = now.day
            ordinal =  int2ordinal(day)
            current_date = "date~" + translate.date_templ().format(weekday=weekday, month=month, day=day, ordinal=ordinal)
        except (KeyError, RuntimeError, ValueError) as error:
            self.log.warning("Error building date string for screensaver: %s. Fallback to default format.", error)
            current_date = "date~" + f"Day {now.day}, Weekday {now.weekday()}, Month {now.month}"

        if current_date != self.last_date:
            if self.send_panel_cmd( current_date):
                self.last_date=current_date

    def update_status(self):
        """
        send status update command to panel
        """
        if self.get_status_card() in NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP]:
            status_card = NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP][self.get_status_card()]
            payload = status_card.create_status_payload(self.get_status_left(), self.get_status_right())
        else:
            #Format: "statusUpdate~iconLeft~iconCOlorLeft~iconRight~iconColorRight")

            payload = "statusUpdate"
            if self.get_status_left() is True:
                icon=skin.key("default", "stateIconLeft")
                color=str(name_to_16bit_color(skin.key("default", "stateIconLeftColor")))
                payload = payload + "~" + icon + '~' + color
            else:
                payload = payload + "~~"
            if self.get_status_right() is True:
                icon=skin.key("default", "stateIconRight")
                color=str(name_to_16bit_color(skin.key("default", "stateIconRightColor")))
                payload = payload + "~" + icon + '~' + color
            else:
                payload = payload + "~~"

        self.send_panel_cmd(payload)

    def navigate(self,card):
        """
        navigate to a specific page type
        """
        self.log.debug("Navigate to card '%s'.", card.name )

        #disconnect current card from openhab
        if self.current_card is not None and not isinstance(self.current_card,NSPanelCardScreenSaver):
            if self.current_card.popup is not None:
                self.current_card.popup.disconnect(self)
                self.current_card.popup = None
            self.current_card.disconnect(self)

        self.send_panel_cmd( card.create_cmd_payload() )
        if not isinstance(card,NSPanelCardScreenSaver):
            #only for other cards as screnn saver is somthing to do
            card.connect(self)

        #fill card with content
        self.send_panel_cmd( card.create_color_payload() )
        self.send_panel_cmd( card.create_update_payload(self.compatibility_mode) )
        self.current_card = card
        if card.group not in [NSPanelCard.NOTIFY_CARD_GROUP, NSPanelCard.STATUS_CARD_GROUP]:
            self.current_group = card.group
        if isinstance(card,NSPanelCardScreenSaver):
            self.update_status()
        self.publish_card()

    def popup_select(self):
        """
        checks if an alternative popup is selected for this slot
        """
        if self.current_card is not None:
            #check if there is no popup card active
            if self.current_card.popup is not None:
                self.send_panel_cmd(self.current_card.popup.create_select_payload(self.compatibility_mode))
                return
        self.log.error("Something went wrong in popup select method.")

    def update(self):
        """
        update current card content
        """
        self.log.debug("Update to card '%s'.", self.current_card.name )

        if self.current_card is not None:
            #check if there is no popup card active
            if self.current_card.popup is None:
                if self.current_card.MY_TYPE in [NSPanelCard.CARD_CHARD]:
                    #some cards need to be cleaned up before content can be updated.
                    self.send_panel_cmd( self.current_card.create_cmd_payload() )
                self.send_panel_cmd( self.current_card.create_update_payload(self.compatibility_mode) )
            else:
                self.send_panel_cmd( self.current_card.popup.create_update_payload(self.compatibility_mode) )


    def send_dimmode(self,addon=""):
        """
        send dimmmode message to nspanel
        """
        msg = self.CMD_DIMMODE + self.mqtt.get_brightness_saver(self.name) \
              + "~" + self.mqtt.get_brightness(self.name) \
              + addon
        self.send_panel_cmd( msg)

    def send_timeout(self):
        """
        send timeout message to nspanel
        """
        msg = self.CMD_TIMEOUT + self.mqtt.get_timeout(self.name)
        self.send_panel_cmd(msg)

    @classmethod
    def get_home_screensaver_card(cls):
        """
        get the screensaver for the home group
        """
        #no default sceensaver in current group. Do the same for home group:
        screensaver_card = NSPanelCard.get_card( NSPanelCard.CARDS_HOME, SCREENSAVER_NAME )
        return screensaver_card

    def get_screensaver_card(self):
        """
        Try to get the best screensaver card object for this panel
        """
        screensaver_card = NSPanelCard.get_card( self.current_group, self.name+SCREENSAVER_NAME )
        if screensaver_card is None:
            #no screensaver for this panel and current group defined. Look for a default one
            screensaver_card = NSPanelCard.get_card( self.current_group, SCREENSAVER_NAME )
            if screensaver_card is None:
                #no sceensaver found in current group: fall back to home
                self.current_group = NSPanelCard.CARDS_HOME
                screensaver_card = NSPanelCard.get_card( self.current_group, self.name+SCREENSAVER_NAME )
                if screensaver_card is None:
                    screensaver_card = self.get_screensaver_card()
        return screensaver_card

    def init_panel(self):
        """
        send all needed messages to initialize the panel
        """
        self.last_date = ""
        self.last_time = ""
        self.check_time()
        self.check_date()
        self.send_timeout()
        self.send_dimmode("~6371") #not shure for whot this ~637 is added in the init sequence documentation
        if self.get_screensaver_card() is None:
            #Fatal error no screensaver card defined for this panel
            self.log.fatal("No Screensaver defined for the panel: %s", self.name )
            sys.exit()
        self.navigate(self.get_screensaver_card())
        #self.send_panel_cmd("pageType~cardPower")
        #self.send_panel_cmd("pageType~popupNotify")
        #self.send_panel_cmd("entityUpdateDetail~*internalName*~*tHeading*~65535~*b1*~65535~*b2*~65535~Dies ist\r\nein sehr\r\nlanger text~65535~10~4~A~65535")

    @classmethod
    def load_cards( cls, path ):
        """
        Load all page definitions in the given path
        """
        #clean up existing cards
        NSPanelCard.cards_by_group = {}
        NSPanelCard.time_tick_callbacks =[]
        cls.LOG.debug("Load cards from path '%s'", path )
        for root, dirs, files in os.walk(path):
            for filename in files:
                cls.LOG.debug("Load cards from file '%s'", filename )
                #check for yaml file extention
                if os.path.splitext(filename)[1] == PAGES_FILE_EXT:
                    with open(os.path.join( root, filename ), encoding='utf-8') as stream:
                        try:
                            cards_yaml = yaml.safe_load(stream)
                            if "cards" in cards_yaml:
                                for card_yaml in cards_yaml["cards"]:
                                    if "name" in card_yaml:
                                        if NSPanelCard.factory_yaml_file(filename, card_yaml) is True:
                                            cls.LOG.error("Card '%s' in file '%s' could not be created.", card_yaml["name"], filename)
                                    else:
                                        cls.LOG.error("Attribute 'name' not defined in file %s.", filename)
                        except yaml.YAMLError:
                            cls.LOG.error("Yaml syntak error in %s.", filename)
            for d in dirs:
                cls.LOG.info("Ignoring directory '%s' in card config folder", os.path.join(root, d))


        #check if a sreensaver is defined in the yaml file. If not create a default one for the panels
        if cls.get_home_screensaver_card() is None:
            if NSPanelCard.CARDS_HOME not in NSPanelCard.cards_by_group:
                NSPanelCard.cards_by_group[NSPanelCard.CARDS_HOME] = {}
            NSPanelCard.cards_by_group[NSPanelCard.CARDS_HOME][SCREENSAVER_NAME] = NSPanelCardScreenSaver(SCREENSAVER_NAME)
            cls.LOG.info("No default screensaver '%s' defined in yaml files. Created a default one for group '%s'", SCREENSAVER_NAME, NSPanelCard.CARDS_HOME)

        #check if status card group exist
        if NSPanelCard.STATUS_CARD_GROUP not in NSPanelCard.cards_by_group:
            #create an empty status card group
            NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP] = {}
