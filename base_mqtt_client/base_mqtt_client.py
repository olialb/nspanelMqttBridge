# python
# because of smbus usage:
# pylint: disable=c-extension-no-member
#
# This file is part of the mqttDisplayClient distribution
# (https://github.com/olialb/mqttDisplayClient).
# Copyright (c) 2025 Oliver Albold.
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
Module implements a base class for MQTT clients based on paho.mqtt
"""

import configparser
import os
import sys
import time
from paho.mqtt import client as mqtt_client

#project specific configs
from file_logger import file_logger as FLOGGER

#
# class definitions
#
class BaseMqttClient: #pylint: ...disable=too-many-instance-attributes
    """
    Implements a base classe for an mqtt client based on paho-mqtt
    """
    def __init__(self, config_file):
        """
        Constructor takes config file as parameter (ini file) and defines global atrributes
        """
        # Global config:
        self.config_file = config_file

        # other global attributes
        self.reconnect_delay = 5  # retry in seconds to try to reconnect mgtt broker
        self.publish_delay = 3  # delay between two publish loops in seconds
        self.full_publish_cycle = 20  # Every publishcycle*fullPublishCycle
        self.topic_root = None  # Root path for all topics
        self.unpublished = True  # set to true if the topics are not published yet
        self.client = None  # mqtt client
        self.reconnect = True  # set to true if the client should reconnect after disconnect

        # broker config:
        self.broker = None
        self.port = 1883
        self.username = ""
        self.password = ""

        # initialize logger
        self.log = FLOGGER.create_log_handler("MQTTBridge")
        self.log_level = None
        self.log_file_handler = None

        # topic configuration
        self.topic_config = {}

        #read ini file
        self.read_config_file()

    def disconnect(self):
        """
        Method to disconnect from the mqtt broker
        """
        if self.client is not None:
            self.reconnect = False
            self.client.disconnect()

    def read_config_file(self):
        """
        Reads the configured ini file and sets attributes based on the config
        and set up the logger and broker data
        """
        # read ini file
        config = configparser.ConfigParser()

        # try to open ini file
        try:
            if os.path.exists(self.config_file) is False:
                self.log.critical("Config file not found '%s'!", self.config_file)
            else:
                config.read(self.config_file)
        except OSError:
            self.log.error("Error while reading ini file: %s", self.config_file)
            sys.exit()

        # read ini file values
        try:
            # read logging config

            # read broker config
            self.broker = config["global"]["broker"]
            self.port = int(config["global"]["port"])
            self.username = config["global"]["username"]
            self.password = config["global"]["password"]
            self.topic_root = (
                config["global"]["topicRoot"]
            )
            self.reconnect_delay = int(config["global"]["reconnectDelay"])
            self.publish_delay = int(config["global"]["publishDelay"])
            self.full_publish_cycle = int(config["global"]["fullPublishCycle"])


            #call call back for addition config data
            self.read_client_config( config )

        except KeyError as inst:
            self.log.error("Error while reading ini file: %s", inst)
            sys.exit()

    def read_client_config( self, config):
        """This method can be overwritten to read more config data from ini file"""

    @classmethod
    def on_connect(cls, client, inst, flags, rc, properties): #pylint: disable=too-many-arguments,too-many-positional-arguments,unused-argument
        """Method called on connect to broker"""
        if rc == 0:
            inst.log.info("Connected to MQTT Broker!")
            # make the subscritions at the broker
            inst.subscribe()
        else:
            inst.log.warning("Failed to connect, return code %s", rc)

    @classmethod
    def on_disconnect(cls, client, inst, flags, rc, properties): #pylint: disable=too-many-arguments,too-many-positional-arguments,unused-argument
        """Method called on disconnect from broker"""
        inst.log.info("Disconnected with result code: %s", rc)
        inst.unpublished = True
        inst.brightness = -1
        while inst.reconnect is True:
            inst.log.info("Reconnecting in %s seconds...", inst.reconnect_delay)
            time.sleep(inst.reconnect_delay)

            try:
                client.reconnect()
                inst.log.info("Reconnected successfully!")
                return
            except OSError as err:
                inst.log.warning("%s. Reconnect failed. Retrying...", err)
        if inst.reconnect is False:
            inst.log.info("Stopping client...")
            client.loop_stop()

    @classmethod
    def on_message(cls, client, inst, msg):  # pylint: disable=unused-argument
        """
        method is called when the cleint receives a message from the broker
        """
        try:
            debuginfo = f"Received `{msg.payload.decode().strip()}` from `{msg.topic}` topic"
        except UnicodeDecodeError:
            inst.log.error( "Mqtt payload from subscribed message can not be decoded!!")
            return

        inst.log.debug( debuginfo )

        # check received topic syntax
        topic = msg.topic
        if topic.split("/")[-1] == "set":
            #remove /set from the end
            topic = topic[0:-len("/set")]

        # search for topic:
        topic_key = None
        for key, t in inst.topic_config.items():
            if t["topic"] == topic:
                topic_key = key
                break

        if topic_key is not None:
            # call the configured command
            if "set" in inst.topic_config[topic_key]:
                try:
                    inst.topic_config[topic_key]["set"](
                        inst.topic_config[topic_key], msg.payload.decode()
                    )
                except Exception as e: #pylint: disable=broad-exception-caught
                    #fatal error during exection of the message
                    log = FLOGGER.create_log_handler("MQTTBridge message esception")
                    log.exception(e)
            else:
                inst.log.info(
                    "Command for topic without command received from broker %s",
                    msg.topic
                )
        else:
            inst.log.info("Command for unknown topic received from broker %s", msg.topic)

    def connect(self) -> mqtt_client:
        """
        Method to connect to the mqtt broker
        """
        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
        if self.username != "":
            self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = BaseMqttClient.on_connect
        self.client.on_disconnect = BaseMqttClient.on_disconnect
        while True:
            try:
                self.client.connect(self.broker, self.port)
            except OSError as error:
                self.log.warning(
                    "Error while connect to server %s:%s: %s",
                    self.broker,
                    self.port,
                    error,
                )
                time.sleep(self.reconnect_delay)
                continue
            break
        # set user data for call backs
        self.client.user_data_set(self)

        # start main loop of mqtt client
        self.client.loop_start()

    def subscribe(self):
        """
        method to subscribe to all the configured topics at the broker
        """
        # Subscribe to all configured topics
        for topic_config in self.topic_config.values():
            if "topic" in topic_config:
                if "publish" in topic_config:
                    topic = f"{topic_config['topic']}/set"
                else:
                    topic = topic_config['topic']
                self.client.subscribe(topic)
                self.log.debug("Subscribe to: %s", topic)
        self.client.on_message = BaseMqttClient.on_message

    def publish_loop_callback(self):
        """
        This call back is called by publish loop and can be overwritten by child class
        """

    def publish_loop(self):
        """
        endless main publish loop
        """
        # endless publish loop
        self.unpublished = True
        loop_counter = 0
        try:
            while True:
                for topic_config in self.topic_config.values():
                    if "publish" in topic_config and topic_config["publish"] is not None:
                        topic = topic_config['topic']
                        topic_config["publish"](topic, topic_config)
                # mark the topics as published
                self.unpublished = False
                # delay until next loo starts
                time.sleep(self.publish_delay)
                # call publish loop call back to allow child class to add additional cyclic stuff
                self.publish_loop_callback()
                # call time time tick of chrome pages
                loop_counter += 1
                if loop_counter > self.full_publish_cycle:
                    loop_counter = 0
                    self.unpublished = True
        except KeyboardInterrupt:
            self.log.warning("Keyboard interrupt receiced. Stop client...")
