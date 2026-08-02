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
"""

#general imports
import signal
import sys
import os
import traceback

# project specific imports:
from base_mqtt_client import base_mqtt_client as BMC
from nspanel.nspanels import NSPanelCard, NSPanel, nspanel_create_oh_connector, nspanel_set_skin, nspanel_set_language
from nspanel.nspanel_config_observer import CardConfigFileObserver
from oh.oh_connector import oh

#
# global constants
#
CONFIG_FILE = "nspanelMqttBridge.ini"  # name of the ini file

#
# define main class
#
class NspanelMqttBridge(BMC.BaseMqttClient): # pylint: disable=too-many-instance-attributes
    """
    Main class of MQTT client for Nspanels with lovelace UI
    """

    def __init__(self, config_file):
        """
        Constructor takes config file as parameter (ini file) and defines global atrributes
        """
        # other global attributes
        self.panel_config = {}
        self.card_files = "./pages"
        self.oh_port = 8080
        self.oh_api_key = ""
        self.oh_timeout=5
        self.brighness_screensaver = None
        self.brighness_standard = None
        self.brighness_timeout = None
        self.saver_update = None
        self.cmd_timeout_value = None
        self.oh_host = None
        self.lang = None
        self.skin_file = None
        self.panels = {}
        self.topic_config = {}
        self.config_files = "./cards"
        self.observe_yaml_files = "enabled"

        # Global config:
        super().__init__(config_file)

        #give the cards a list of all panels
        NSPanelCard.all_panels = self.panels
        #load card definition yaml files
        NSPanel.load_cards( self.card_files )

        print("Card yaml files loaded. Bridge is active now!")
        self.log.info("Card yaml files loaded. Bridge is active now!")
        for panel_name, panel in self.panels.items():
            if panel.name.lower() in NSPanelCard.cards_by_group:
                panel.current_group = panel.name.lower()
            print("Panel '",panel.name, "' connected.' Topic root :'",panel.topic,"'", "Active group: ", panel.current_group)
            self.log.info("Panel '%s' connected.' Topic root :'%s' Active group: %s", panel_name, panel.topic, panel.current_group)

        #create card file observer if active
        self.file_observer = None
        if self.observe_yaml_files == "enabled":
            self.file_observer = CardConfigFileObserver(self.card_files, self.resync_card_yaml_files)

    def run(self):
        """
        Start all listening/observing threads and run main application loop
        """
        self.connect()
        #init panels
        for panel in self.panels.values():
            panel.restart()
            panel.init_panel()

        #start file observer for card configuration files
        if self.file_observer is not None:
            self.file_observer.start()

        #start mqtt publish loop
        self.publish_loop()
        if self.file_observer is not None:
            self.file_observer.stop()

    def stop(self):
        """
        Stop all listening/observing threads to allow graceful shutdown
        """
        if self.file_observer is not None:
            self.file_observer.stop()
        if self.client is not None:
            self.client.loop_stop()
        _oh = oh()
        if _oh is not None:
            _oh.disconnect()

    def new_oh_connector(self):
        """
        creates a new openhab connector with the given parameters and sets it in the card slot class
        """
        nspanel_create_oh_connector(self.oh_host, self.oh_port, self.oh_timeout, self.oh_api_key)

    def resync_card_yaml_files(self):
        """
        Resync all card data with yaml files
        """
        #first create a new openhab connector to delete old connections and stop listener thread
        self.new_oh_connector()

        #store the old card names for each panel
        old_card_names = {}
        for panel_name, panel in self.panels.items():
            if panel.current_card is not None:
                old_card_names[panel_name] = panel.current_card.name

        #now load the yaml files again to update the card data
        NSPanel.load_cards( self.card_files )
        for panel_name, panel in self.panels.items():
            #first check the active status card. Does it still exist?
            if self.get_status_card(panel_name) not in NSPanelCard.cards_by_group[NSPanelCard.STATUS_CARD_GROUP]:
                self.log.debug("Status card for panel '%s'. Card is no longer valid.", panel_name)
                self.set_status_card(panel_name, NSPanelCard.CARD_DEFAULT_STATUS)
            #first check the active group and card. Do they still exist?
            if panel.current_group in NSPanelCard.cards_by_group and panel_name in old_card_names:
                card = NSPanelCard.get_card(panel.current_group, old_card_names[panel_name])
                if card is not None:
                    self.log.debug("Resyncing card for panel '%s'. Card is still valid.", panel_name)
                    panel.navigate(card)
                    continue
            panel.current_group = NSPanelCard.CARDS_HOME
            self.log.debug("Resyncing card for panel '%s'. Card is no longer valid.", panel_name)
            panel.navigate(panel.get_screensaver_card())


    def read_client_config(self, config):
        """
        Reads the configured ini file and sets attributes based on the config
        """
        # read ini file values
        #try:
        # read brigtness config
        self.brighness_screensaver = int(config["global"]["screensaver"])
        self.brighness_standard = int(config["global"]["standard"])
        self.brighness_timeout = int(config["global"]["saverTimeout"])
        self.saver_update = (int(config["global"]["saverUpdate"])*60)/self.publish_delay
        # read command config
        self.cmd_timeout_value = int(config["global"]["cmdTimeout"])

        # read openhab config
        self.oh_host = config["oh"]["host"]
        if "port" in config["oh"]:
            self.oh_port = config["oh"]["port"]
        if "apiKey" in config["oh"]:
            self.oh_api_key = config["oh"]["apiKey"]
        if "timeout" in config["oh"]:
            self.oh_timeout= int(config["oh"]["timeout"])

        #create the global openhab connector object
        self.new_oh_connector()

        #read localization
        self.lang = config["localize"]["lang"]
        nspanel_set_language( self.lang )

        #panel skin
        self.skin_file = config["skin"]["skinFile"]
        nspanel_set_skin( self.skin_file )

        #define topic configuration for all panels
        self.topic_config["status_left"] = {
            "topic": self.topic_root + "/status_left",
            "publish": None,
            "set":  self.set_status_left_mqtt,
            "value":"OFF"
            }
        self.topic_config["status_right"] = {
            "topic": self.topic_root + "/status_right",
            "publish": None,
            "set":  self.set_status_right_mqtt,
            "value": "OFF"
            }
        self.topic_config["status_card"] = {
            "topic": self.topic_root + "/status_card",
            "publish": None,
            "set":  self.set_status_card_mqtt,
            "value": NSPanelCard.CARD_DEFAULT_STATUS
            }
        self.topic_config["notification"] = {
            "topic": self.topic_root + "/notification",
            "publish": None,
            "set":  self.set_notification_mqtt,
            "value": "|"
            }
        self.topic_config["brightness"] = {
            "topic": self.topic_root + "/brightness",
            "publish": None,
            "set":  self.set_brightness_mqtt,
            "value": self.brighness_standard
            }
        self.topic_config["brightness_saver"] = {
            "topic": self.topic_root + "/brightness_saver",
            "publish": None,
            "set":  self.set_brightness_saver_mqtt,
            "value": self.brighness_screensaver
            }
        self.topic_config["timeout"] = {
            "topic": self.topic_root + "/timeout",
            "publish": None,
            "set":  self.set_timeout_mqtt,
            "value": self.brighness_timeout
            }
        self.topic_config["card"] = {
            "topic": self.topic_root + "/card",
            "publish": None,
            "set":  self.set_card_mqtt,
            "value": '{ "class": "home", "name": "'+ NSPanelCard.CARD_SCREENSAVER +'"}'
            }


        #define specific topic configuration for each panel
        #read list of panels

        for name, topic in config.items("panels"):
            #check for additional parameters in the topic definition
            params = topic.split(",")
            compatibility_mode = NSPanelCard.COMPATIBILITY_MODE_DEFAULT
            if len(params) >= 1:
                topic = params[0]
                if len(params) >= 2 and params[1].lower() in NSPanelCard.COMPATIBILITY_MODES:
                    compatibility_mode = params[1].lower()
            panel = NSPanel(self, name, topic, compatibility_mode=compatibility_mode)
            self.panels[name] = panel
            # topic configuration
            #configure tasmota result
            self.topic_config[topic] = {
                "topic": topic+"/RESULT",
                "set":  panel.panel_callback
                }
            #configure additional topics for commands and pulbishing for each panel
            self.topic_config[name+"_"+"brightness"] = {
                "topic": self.topic_root + '/'+name + "/brightness",
                "publish": panel.publish_mqtt,
                "set":  panel.set_brightness_mqtt,
                "value": self.brighness_standard
                }
            self.topic_config[name+"_"+"brightness_saver"] = {
                "topic": self.topic_root + '/'+ name + "/brightness_saver",
                "publish": panel.publish_mqtt,
                "set":  panel.set_brightness_saver_mqtt,
                "value": self.brighness_screensaver
                }
            self.topic_config[name+"_"+"timeout"] = {
                "topic": self.topic_root + '/'+ name + "/timeout",
                "publish": panel.publish_mqtt,
                "set":  panel.set_timeout_mqtt,
                "value": self.brighness_timeout
                }
            self.topic_config[name+"_"+"card"] = {
                "topic": self.topic_root + '/'+ name + "/card",
                "publish": panel.publish_mqtt,
                "set":  panel.set_card_mqtt,
                "value": '{ "class": "home", "name": "'+ NSPanelCard.CARD_SCREENSAVER +'"}'
                }
            self.topic_config[name+"_"+"version"] = {
                "topic": self.topic_root + '/'+ name + "/version",
                "publish": panel.publish_mqtt,
                "value": None
                }
            self.topic_config[name+"_"+"status_left"] = {
                "topic": self.topic_root + '/'+ name + "/status_left",
                "publish": panel.publish_mqtt,
                "set":  panel.set_status_left_mqtt,
                "value":"OFF"
                }
            self.topic_config[name+"_"+"status_right"] = {
                "topic": self.topic_root + '/'+ name + "/status_right",
                "publish": panel.publish_mqtt,
                "set":  panel.set_status_right_mqtt,
                "value": "OFF"
                }
            self.topic_config[name+"_"+"status_card"] = {
                "topic": self.topic_root + '/'+ name + "/status_card",
                "publish": panel.publish_mqtt,
                "set":  panel.set_status_card_mqtt,
                "value": NSPanelCard.CARD_DEFAULT_STATUS
                }
            self.topic_config[name+"_"+"notification"] = {
                "topic": self.topic_root + '/'+ name + "/notification",
                "publish": panel.publish_mqtt,
                "set":  panel.set_notification_mqtt,
                "value": "|"
                }


            #pages definition file location
            if "configPath" in config:
                if "cards" in config["configPath"]:
                    self.card_files = config["configPath"]["cards"]
                    self.check_card_filepath()

                if "observer" in config["configPath"]:
                    self.observe_yaml_files = config["configPath"]["observer"]

        #except (KeyError, RuntimeError) as error:
        #    self.log.error("Error while reading ini file: %s", error)
        #    sys.exit()

        self.log.debug("Constructed!")

    def check_card_filepath(self):
        """
        checks if the card filepath exists and is a directory. If not, it creates the directory.
        """
        if os.path.exists(self.card_files) is False:
            self.log.warning("Card file path '%s' does not exist. Creating directory.", self.card_files)
            try:
                os.makedirs(self.card_files)
                self.log.info("Directory '%s' created successfully.", self.card_files)
                with open(self.card_files+ "/readme.txt", "w", encoding="utf-8") as file:
                    file.write("""Place your nspanel bridge card definition yaml files in this folder.
Each .yaml file will be loaded in the overall card data base.
You can find example yaml files in the ./config directory of the github repository of the bridge.
https://github.com/olialb/nspanelMqttBridge/tree/main/config
The how to create your own yaml files is described in the documentation:
https://github.com/olialb/nspanelMqttBridge/wiki/YamlOverview""")
            except OSError as error:
                self.log.error("Error creating directory '%s': %s", self.card_files, error)
                sys.exit()
        elif not os.path.isdir(self.card_files):
            self.log.error("Card file path '%s' is not a directory.", self.card_files)
            sys.exit()

    def publish_loop_callback(self):
        """
        Publish call back called from root class
        """
        #panel time ticks
        for panel in self.panels.values():
            panel.time_tick()
        #observer time tick
        if self.file_observer is not None:
            self.file_observer.time_tick()
        #card time ticks:
        NSPanelCard.time_tick()


    def publish_mqtt(self, topic, my_config):
        """
        generic publish method for all topics.
        """
        msg = my_config["value"]
        # send message to broker
        if self.unpublished is True and msg is not None:
            #publish the value
            result = self.client.publish(topic, msg)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                self.log.debug("Bridge send '%s' to topic %s", msg, topic )
                return True
            self.log.error("Bridge failed to send message to topic %s", topic)
            return False
        return False

    def set_brightness_mqtt(self, my_config, msg):
        """
        mqtt command to set the brightness in all panels
        """
        for panel_name, panel in self.panels.items():
            my_config = self.topic_config[panel_name+"_"+"brightness"]
            panel.set_brightness_mqtt(my_config, msg)


    def set_brightness_saver_mqtt(self, my_config, msg):
        """
        mqtt command to set the brightness saver in all panels
        """
        for panel_name, panel in self.panels.items():
            my_config = self.topic_config[panel_name+"_"+"brightness_saver"]
            panel.set_brightness_saver_mqtt(my_config, msg)

    def set_timeout_mqtt(self, my_config, msg):
        """
        mqtt command to set the timeout in all panels
        """
        for panel_name, panel in self.panels.items():
            my_config = self.topic_config[panel_name+"_"+"timeout"]
            panel.set_timeout_mqtt(my_config, msg)

    def set_card_mqtt(self, my_config, msg):
        """
        mqtt command to set a card in all panels
        """
        for panel_name, panel in self.panels.items():
            my_config = self.topic_config[panel_name+"_"+"card"]
            panel.set_card_mqtt(my_config, msg)

    def set_notification_mqtt(self, my_config, msg):
        """
        mqtt command to set a notification in all panels
        """
        for panel_name, panel in self.panels.items():
            my_config = self.topic_config[panel_name+"_"+"notification"]
            panel.set_notification_mqtt(my_config, msg)

    def set_status_left_mqtt(self, my_config, msg):
        """
        mqtt command to set the left alarm in all panels
        """
        for panel_name, panel in self.panels.items():
            my_config = self.topic_config[panel_name+"_"+"status_left"]
            panel.set_status_left_mqtt(my_config, msg)

    def set_status_right_mqtt(self, my_config, msg):
        """
        mqtt command to set the right alarm in all panels
        """
        for panel_name, panel in self.panels.items():
            my_config = self.topic_config[panel_name+"_"+"status_right"]
            panel.set_status_right_mqtt(my_config, msg)

    def set_status_card_mqtt(self, my_config, msg):
        """
        mqtt command to set the right alarm in all panels
        """
        for panel_name, panel in self.panels.items():
            my_config = self.topic_config[panel_name+"_"+"status_card"]
            panel.set_status_card_mqtt(my_config, msg)

    #
    # set/get methods for the topics in this bridge
    #
    def get_brightness( self, panel_name ):
        """
        returns the current brigtness value
        """
        return str(self.topic_config[panel_name+"_"+"brightness"]["value"])

    def get_brightness_saver( self, panel_name ):
        """
        returns the current brigtness saver value
        """
        return str(self.topic_config[panel_name+"_"+"brightness_saver"]["value"])

    def get_timeout( self, panel_name ):
        """
        returns the current timeout value
        """
        return str(self.topic_config[panel_name+"_"+"timeout"]["value"])

    def get_card( self, panel_name ):
        """
        returns the current card value
        """
        return self.topic_config[panel_name+"_"+"card"]["value"]

    def get_status_card( self, panel_name ):
        """
        returns the current status card value
        """
        return self.topic_config[panel_name+"_"+"status_card"]["value"]

    def get_status_left( self, panel_name ):
        """
        returns the current status left value
        """
        return self.topic_config[panel_name+"_"+"status_left"]["value"] == 'ON'

    def get_status_right( self, panel_name ):
        """
        returns the current status right value
        """
        return self.topic_config[panel_name+"_"+"status_right"]["value"] == 'ON'

    def set_brightness( self, panel_name, value ):
        """
        set the current brightness value
        """
        topic_config = self.topic_config[panel_name+"_"+"brightness"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def set_brightness_saver( self, panel_name, value ):
        """
        set the current brightness_saver value
        """
        topic_config = self.topic_config[panel_name+"_"+"brightness_saver"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def set_timeout( self, panel_name, value ):
        """
        set the current timeout value
        """
        topic_config = self.topic_config[panel_name+"_"+"timeout"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def set_card( self, panel_name, value ):
        """
        set the current card value
        """
        topic_config = self.topic_config[panel_name+"_"+"card"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def set_status_card( self, panel_name, value ):
        """
        set the current card value
        """
        topic_config = self.topic_config[panel_name+"_"+"status_card"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def set_status_left( self, panel_name, value ):
        """
        set the current status_left value
        """
        topic_config = self.topic_config[panel_name+"_"+"status_left"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def set_status_right( self, panel_name, value ):
        """
        set the current status_right value
        """
        topic_config = self.topic_config[panel_name+"_"+"status_right"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def set_version( self, panel_name, value ):
        """
        set the current version value
        """
        topic_config = self.topic_config[panel_name+"_"+"version"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def set_notification( self, panel_name, value ):
        """
        set the current notification value
        """
        topic_config = self.topic_config[panel_name+"_"+"notification"]
        topic_config["value"] = value
        self.client.publish( topic_config["topic"], value )

    def signal_term_handler( self, sig, frame ): # pylint: disable=unused-argument
        """
        Call back to handle OS SIGTERM signal to terminate client.
        """
        self.log.warning( "Received SIGTERM. Stop client...")
        self.stop()
        sys.exit(0)

if __name__ == "__main__":
    CLIENT = NspanelMqttBridge(CONFIG_FILE)
    signal.signal(signal.SIGTERM, CLIENT.signal_term_handler)
    print("Signals initialized.")
    try:
        CLIENT.run()
        print("CLIENT finished properly")
    except Exception as e:  # pylint: disable=broad-except
        print("CLIENT run crashed!", traceback.format_exc())
    CLIENT.stop()  # either case, we make sure to stop all potentially started threads
