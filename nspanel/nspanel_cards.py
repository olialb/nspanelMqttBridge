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

# project specific imports:
from nspanel.nspanel_globals import name_to_16bit_color, map_state_oh2panel
from nspanel.nspanel_base_cards import NSPanelCard, NSPanelCardWithSlots
from lang import translate
from skin import skin

#
# global constants
#

#
# Class definitions
#
class NSPanelCardScreenSaver(NSPanelCardWithSlots):
    """
    Class for screen saver
    """
    MY_TYPE = "screensaver"
    COLORS = ["backgroundColor", "tTimeColor", "timeAMPMColor",
              "tDateColor", "tMainTextColor", "tForecast1Color",
              "tForecast2Color", "tForecast3Color", "tForecast4Color",
              "tForecast1ValColor", "tForecast2ValColor", "tForecast3ValColor",
              "tForecast4ValColor", "barColor", "tMainTextAlt2Color",
              "tTimeAddColor" ]

    def __init__(self, name, group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, group )
        #build color dict with colors from skin file
        self.colors = {}
        for color_name in self.COLORS:
            self.colors[color_name] = str(name_to_16bit_color(skin.key("default", color_name)))

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        ret = super().load_card_yaml( card_yaml )
        #check if any specific color attribute is defined in card_yaml
        for color_name in self.COLORS:
            if color_name in card_yaml and card_yaml[color_name] is not None:
                self.colors[color_name] = str(name_to_16bit_color(card_yaml[color_name]))
        return ret

    def create_color_payload(self):
        """
        create color command for coloring the screensaver
        """
        payload = "color"
        for color_name in self.COLORS:
            payload = payload + "~" + self.colors[color_name]
        return payload

    def create_cmd_payload(self):
        """
        create command payload to switch to this card type
        """
        return "pageType~"+self.MY_TYPE

    def create_update_payload(self):
        """
        Create screensaver payload
        """
        return "weatherUpdate" + self.create_slots_payload()

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardScreenSaver.MY_TYPE] = NSPanelCardScreenSaver

class NSPanelCardEntities(NSPanelCardWithSlots):
    """
    Represent an card of type CardEntities in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_ENTITIES

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardEntities.MY_TYPE] = NSPanelCardEntities

class NSPanelCardGrid(NSPanelCardWithSlots):
    """
    Represent an card of type CardEntities in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_GRID

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardGrid.MY_TYPE] = NSPanelCardGrid

class NSPanelStatusCard(NSPanelCardWithSlots):
    """
    Represent an card of type "statusCard"
    """
    MY_TYPE = NSPanelCard.CARD_STATUS

    def create_status_payload(self, status_left, status_right):
        """
        send status update command to panel
        """
        #Format: "statusUpdate~iconLeft~iconCOlorLeft~iconRight~iconColorRight")

        payload = "statusUpdate"
        if status_left is True:
            icon=skin.key("default", "stateIconLeft")
            color=str(name_to_16bit_color(skin.key("default", "stateIconLeftColor")))
            if "slot_0" in self.slots and self.slots["slot_0"] is not None:
                payload = payload + self.slots["slot_0"].create_status_payload(icon,color)
            else:
                payload = payload + "~" + icon + '~' + color
        else:
            payload = payload + "~~"

        if status_right is True:
            icon=skin.key("default", "stateIconRight")
            color=str(name_to_16bit_color(skin.key("default", "stateIconRightColor")))
            if "slot_1" in self.slots and self.slots["slot_1"] is not None:
                payload = payload + self.slots["slot_1"].create_status_payload(icon,color)
            else:
                payload = payload + "~" + icon + '~' + color
        else:
            payload = payload + "~~"
        return payload

    def item_update_callback(self):
        """
        this callback is called from OHItensDB if the state of an item in this card is updated
        """
        self.log.debug("Call from item listner of state card '%s'. Item state in card has changed", self.name)
        for panel in self.connected_panels.values():
            panel.update_status()



#add this card class type to the factory
NSPanelCard.card_types[NSPanelStatusCard.MY_TYPE] = NSPanelStatusCard

class NSPanelCardQR(NSPanelCardWithSlots):
    """
    Base class for cards with QR codes
    """
    MY_TYPE = NSPanelCard.CARD_QR

    def create_qr_payload(self):
        """
        Create the QR part of the payload
        """
        if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
            #slot 0 must contain a string item with ssid
            slot = self.slots["slot_0"]
            slot.item.update_item()
            return slot.item.state
        return "https://albold-home.de"


    def create_slots_payload(self):
        """
        Create card QR wifi payload
        """
        #Format: example entityUpd~Guest Wifi~button~navigate.prev~<~65535~~~button~navigate.next~>~65535~~
        #        ~WIFI:S:test_ssid;T:WPA;P:test_pw;;
        #        ~text~iText.test_ssid~���~17299~Name~test_ssid
        #        ~text~iText.test_pw~���~17299~Password~test_pw

        #QR code generation payload
        payload = "~" + self.create_qr_payload()
        #slot 0
        icon = skin.key(self.MY_TYPE, "icon1")
        icon_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "icon_color_1")))
        text = "?slot0?"
        state = ""
        if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
            #slot 0 should contain a string item
            slot = self.slots["slot_0"]
            if slot.text is not None:
                text = slot.text
            else:
                text = str(slot.item.label)
            if "icon" in slot.json_data:
                icon = slot.item.icon
            if "iconColor" in slot.json_data:
                icon_color = slot.item.icon_color
            state = str(slot.item.state)
        payload = payload + "~text~slot0~"+icon+'~'+icon_color+'~'+text+'~'+ state

        #slot 1:
        #check if slot is active fro this card:
        if skin.key(self.MY_TYPE, "icon2") is None:
            #slot not used for this card
            payload = payload + "~text~slot1~~~~"
        else:
            icon = skin.key(self.MY_TYPE, "icon2")
            icon_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "icon_color_2")))
            text = "?slot1?"

            if "slot_1" in self.slots and self.slots["slot_1"] is not None and self.slots["slot_1"].slot_class == "ohItem":
                #slot 0 sould contain a string item
                slot = self.slots["slot_1"]
                slot.item.update_item()
                if slot.text is not None:
                    text = slot.text
                else:
                    text = str(slot.item.label)
                if "icon" in slot.json_data:
                    icon = slot.item.icon
                if "iconColor" in slot.json_data:
                    icon_color = slot.item.icon_color
                state = str(slot.item.state)
        payload = payload + "~text~slot1~"+icon+'~'+icon_color+'~'+text+'~'+state
        return payload

    def create_cmd_payload(self):
        """
        create command payload to switch to this card type
        """
        return "pageType~"+NSPanelCardQR.MY_TYPE



#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardQR.MY_TYPE] = NSPanelCardQR

class NSPanelCardQRWifi(NSPanelCardQR):
    """
    Card to show the wifi QR code
    """
    MY_TYPE = "cardQRWifi"

    def __init__(self, name,  group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel card QR codes
        """
        super().__init__( name, group )
        self.security = "WPA2"
        self.hidden = "false"

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        ret = super().load_card_yaml( card_yaml )

        if "security" in card_yaml and card_yaml["security"] is not None:
            self.security = str(card_yaml["security"])
        else:
            self.log.debug("Attribute security not defined in cardQRWifi with name '%s'. Use 'WPA2", self.name)
        if "hidden" in card_yaml and card_yaml["hidden"] is not None:
            self.hidden = str(card_yaml["hidden"])
        else:
            self.log.debug("Attribute hidden not defined in cardQRWifi with name '%s'. Use 'H:false'", self.name)
        return ret

    def create_qr_payload(self):
        """
        Create the QR part of the payload
        """
        #Wifi QR code: WIFI:S:<SSID>;T:<WPA|WEP|>;P:<PASSWORD>;; https://wiqrcode.com/blog/complete-guide-to-wifi-qr-codes
        #QR code generation payload
        ssid = "?slot ssid?"
        password = "?slot password?"

        if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
            #slot 0 must contain a string item with ssid
            slot = self.slots["slot_0"]
            slot.item.update_item()
            ssid = str(slot.item.state)
        if "slot_1" in self.slots and self.slots["slot_1"] is not None and self.slots["slot_1"].slot_class == "ohItem":
            #slot 0 must contain a string item with password
            slot = self.slots["slot_1"]
            slot.item.update_item()
            password = str(slot.item.state)

        return "WIFI:S:" + ssid +";T:"+ self.security +";P:" + password +";H:" + self.hidden + ";"


#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardQRWifi.MY_TYPE] = NSPanelCardQRWifi

class NSPanelCardAlarm(NSPanelCardWithSlots):
    """
    Represent an card of type cardAlarm in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_ALARM

    def create_slots_payload(self): #pylint: disable=too-many-statements, too-many-branches
        """
        evaluate the alarm slots and create the payload:
        Examples:~ButtonRowID~Text1~ID1~Text2~ID2~Text3~ID3~Text4~ID4~~65504~enable~enable~~1024~ID5
                ~CardAlarm~Vollschutz~mode1~Zuhause~mode2~Nacht~mode3~Besuch~mode4~~63488~disable~disable~~AB1
        """
        #Build the key pad on right side first:
        idb = []
        idb.append("")
        idb.append("")
        idb.append("")
        idb.append("")
        textb = []
        textb.append("")
        textb.append("")
        textb.append("")
        textb.append("")

        if "slot_1" in self.slots and self.slots["slot_1"] is not None and self.slots["slot_1"].slot_class == "ohItem":
            #slot 1 must contain the option list for the switches
            slot = self.slots["slot_1"]
            slot.item.update_item()
            if slot.item.options is not None:
                i=0
                for key in slot.item.options:
                    idb[i] = key
                    textb[i] = slot.item.options[key]
                    i = i + 1
                    if i >= 4:
                        break

        #Build the top icon:
        icon = skin.key(self.MY_TYPE, "icon")
        icon_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "icon_color")))
        flash = skin.key(self.MY_TYPE, "flashing")

        if "slot_2" in self.slots and self.slots["slot_2"] is not None and self.slots["slot_2"].slot_class == "ohItem":
            #optional slot 2 controlls the icon on top
            slot = self.slots["slot_2"]
            slot.item.update_item()
            state_values = str(slot.item.state).split('|')
            if state_values[0].upper() == 'ON':
                flash = "enable"
            if len(state_values) > 1:
                icon = skin.icon(state_values[1])
            else:
                if "icon" in slot.json_data:
                    icon = slot.icon
            if len(state_values) > 2:
                icon_color = str(name_to_16bit_color(state_values[2]))
            else:
                if "iconColor" in slot.json_data:
                    icon_color = slot.icon_color

        #check for keypad disabled
        keypad = "enable"
        if "slot_3" in self.slots and self.slots["slot_3"] is not None and self.slots["slot_3"].slot_class == "ohItem":
            #optional slot 3 controlls the keypad visibility
            slot = self.slots["slot_3"]
            slot.item.update_item()
            if slot.item.state != 'ON':
                keypad = "disable"

        #check for optional button in lower lef corner under keypad
        opt_icon = ""
        opt_icon_color = ""
        if "slot_4" in self.slots and self.slots["slot_4"] is not None and self.slots["slot_4"].slot_class == "ohItem":
            #optional slot 4 defines the additionl button
            slot = self.slots["slot_4"]
            slot.item.update_item()
            opt_icon = slot.icon
            opt_icon_color = slot.icon_color
            if slot.icon_state_color is not None:
                if slot.item.state == "ON":
                    opt_icon_color = slot.icon_state_color[0]
                else:
                    opt_icon_color = slot.icon_state_color[1]

        #finally make slot payload ot of it
        payload = "~CardAlarm"
        for i in range(4):
            payload = payload + '~' + textb[i] + '~' + idb[i]
        return payload + "~" + icon + "~" + icon_color + "~" + keypad + "~" + flash +\
                       "~" + opt_icon + "~" + opt_icon_color + "~" + "CardAlarm2"

    def event_card_alarm( self, slot_name, params):
        """
        Event handling for this card
        """
        if slot_name == "CardAlarm":
            if len(params) > 0 and params[0] in self.slots["slot_1"].item.options:
                item = self.slots["slot_1"].item
                item.set_item_state( params[0] )
                self.log.debug("Button '%s' pressed with value '%s'.",params[0], item.options[params[0]] )
                if len(params) > 1 and "slot_0" in self.slots and self.slots["slot_0"].slot_class == "ohItem":
                    item = self.slots["slot_0"].item
                    item.set_item_state( params[1] )
                return
            self.log.warning("Can not process event 'CardAlarm'.")
            return
        if slot_name == "CardAlarm2":
            if "slot_4" in self.slots and self.slots["slot_4"].slot_class == "ohItem":
                item = self.slots["slot_4"].item
                item.toggle_item_state()
                self.log.debug("Toggle item '%s'.",item.name )
                return
            self.log.warning("Can not process event 'CardAlarm2'.")
            return
        self.log.warning("Unknown event '%s' for cardAlarm.", params[0])

    def event_button_press( self, slot_name, params, panel=None ):
        """
        process a button press event for this card
        """
        #example event params:
        #"OnOff,1"
        #"button"
        #"brightnessSlider,34'
        #colorTempSlider,89
        #navigate.prev,button"
        #down
        #tiltOpen
        #event,buttonPress2,CardAlarm,AB0|mode2,6655

        #check for cardAlarm Events.
        if slot_name in ["CardAlarm","CardAlarm2"] and self.MY_TYPE == self.CARD_ALARM:
            return self.event_card_alarm( slot_name, params)

        return super().event_button_press( slot_name, params, panel )

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardAlarm.MY_TYPE] = NSPanelCardAlarm

class NSPanelCardThermo(NSPanelCardWithSlots):
    """
    Represent an card of type cardThermo in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_THERMO

    def __init__(self, name, group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, group )
        self.min = "50"
        self.max = "300"
        self.step = "5"
        self.details = "1"

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        ret = super().load_card_yaml( card_yaml )

        if "min" in card_yaml and card_yaml["min"] is not None:
            try:
                self.min = str(card_yaml["min"]*10)
            except ValueError:
                self.log.error("No valid defined attribute min '%s'", card_yaml["min"])

        if "max" in card_yaml and card_yaml["max"] is not None:
            try:
                self.max = str(card_yaml["max"]*10)
            except ValueError:
                self.log.error("No valid defined attribute max '%s'", card_yaml["max"])

        if "step" in card_yaml and card_yaml["step"] is not None:
            try:
                self.step = str(card_yaml["step"]*10)
            except ValueError:
                self.log.error("No valid defined attribute step '%s'", card_yaml["step"])

        if "details" in card_yaml and card_yaml["details"] is True:
            self.details = "0"
        return ret

    def create_slots_payload(self):
        """
        evaluate the thermo slots and create the payload:
        Examples:~CardThermo~24.5~260~status~100~300~5
                 ~~65504~1~button1~~65504~1~button2~~65504~1~button3~~65504~1~button4~~65504~1~button5~~65504~1~button6~~65504~1~button7~~65504~1~button8
                 ~cl1stTb~state2~~°C~200~1
        """
        payload = "~CardThermo" #Button ID

        #Unit
        unit = translate.temperture_unit()

        #Target temperature 1
        target1 = "10.0"+unit
        if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
            #slot 1 must contain an themperature set item
            slot = self.slots["slot_0"]
            slot.item.update_item()
            try:
                target1 = str(slot.item.state*10)
            except ValueError:
                self.log.error("No valid defined attribute for temperature 1 '%s'", slot.item.state)

        #Target temperature 2
        target2 = ""
        if "slot_1" in self.slots and self.slots["slot_1"] is not None and self.slots["slot_1"].slot_class == "ohItem":
            #slot 2 must contain a temperature set item
            slot = self.slots["slot_1"]
            slot.item.update_item()
            try:
                target2 = str(slot.item.state*10)
            except ValueError:
                self.log.error("No valid defined attribute for temperature 2 '%s'", slot.item.state)

        #state slots
        states = ["","","",""]
        for i in range(4):
            slot_name = "slot_"+str(i+2)
            if slot_name in self.slots and self.slots[slot_name] is not None and self.slots[slot_name].slot_class == "ohItem":
                #slot 3,4,5,6 must contain a state item
                slot = self.slots[slot_name]
                slot.item.update_item()
                states[i] = slot.item.state_formated

        payload = payload + "~" + states[1] + "~" + target1 + "~" + states[3] + "~" + self.min + "~" + self.max + "~" + self.step

        #button slots
        for i in range(8):
            slot_name = "slot_"+str(i+6)
            if slot_name in self.slots and self.slots[slot_name] is not None and self.slots[slot_name].slot_class == "ohItem":
                #slot 7-15 can contain a switch item
                slot = self.slots[slot_name]
                slot.item.update_item()
                payload = payload + "~" + slot.icon + "~" + slot.icon_color + "~"+ map_state_oh2panel('switch', slot.item.state)  + "~" + slot_name
            else:
                payload = payload + "~~~~"

        return payload + "~" + states[0] + "~" + states[2] + "~~" + unit + "~" + target2 + "~" + self.details

    def event_card_thermo( self, slot_name, params ):
        """
        Event handling for this card
        """
        #CardThermo,hvac_action,slot_7

        if params[0] == "hvac_action" and len(params) > 1 and params[1] in self.slots:
            slot = self.slots[params[1]]
            slot.item.toggle_item_state()
            self.log.debug("HVAC button '%s' toggled", slot.item.name)
            return
        if params[0] == "tempUpdHighLow" and len(params) > 1:
            temperatures = params[1].split("|")
            #set temperature 1
            if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
                #slot 1 must contain an themperature set item
                slot = self.slots["slot_0"]
                try:
                    slot.item.set_item_state( str(float(temperatures[0])/10) )
                except ValueError:
                    self.log.error("No valid temperature 1 in event '%s'", params[1])
            #set temperature 2
            if "slot_1" in self.slots and self.slots["slot_1"] is not None and self.slots["slot_1"].slot_class == "ohItem":
                #slot 1 must contain an themperature set item
                slot = self.slots["slot_1"]
                try:
                    slot.item.set_item_state( str(float(temperatures[1])/10) )
                except ValueError:
                    self.log.error("No valid temperature 2 in event '%s'", params[1])
            return
        if params[0][0:len("mode-")] == "mode-" and len(params) > 1:
            slot_name = params[0][len("mode-"):]
            if slot_name in self.slots and self.slots[slot_name] is not None and self.slots[slot_name].slot_class == "ohItem":
                slot = self.slots[slot_name]
                new_state = slot.item.state_formated
                try:
                    #try to find new value in options
                    new_state = list(slot.item.options.keys())[int(params[1])]
                except ValueError:
                    self.log.warning("Selected value '%s' can not be found in options!", params[1])
                if new_state != slot.item.state_formated:
                    slot.item.set_item_state(new_state)
                    self.log.info("Input select event '%s' for slot '%s'", new_state, slot.item.name)
            return
        self.log.warning("Unknown event '%s' for cardThermo.", params[0])

    def event_button_press( self, slot_name, params, panel=None ):
        """
        process a button press event for this card
        """
        #example event params:
        #"OnOff,1"
        #"button"
        #"brightnessSlider,34'
        #colorTempSlider,89
        #navigate.prev,button"
        #down
        #tiltOpen
        #event,buttonPress2,CardAlarm,AB0|mode2,6655

        #check for cardThermo Events.
        if slot_name in ["CardThermo"] and self.MY_TYPE == self.CARD_THERMO:
            return self.event_card_thermo( slot_name, params )

        return super().event_button_press( slot_name, params, panel )

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardThermo.MY_TYPE] = NSPanelCardThermo

class NSPanelCardChart(NSPanelCardWithSlots):
    """
    Represent an card of type cardChart in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_CHARD
    MAX_Y = 196   #Maximal y value allowed in chart
    MAX_BAR = 50  #maximal number of bars
    SUPPORTED_NUMBER_TYPES = ["Number", "Dimmer", "Rollershutter"]
    SUPPORTED_STRING_TYPES = ["String","Switch","Contact"]
    MAX_STATES = 10 #maximal number of different states shown in chart (for string items)

    def __init__(self, name, group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, group )
        self.bar_max = self.MAX_BAR  #maximal number of bars shown in the chart
        self.period = 60 #one hour
        self.past = 0 #from now back
        self.color = str(name_to_16bit_color(skin.key( self.MY_TYPE, "color")))
        self.life = False

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        ret = super().load_card_yaml( card_yaml )

        if "barMax" in card_yaml and card_yaml["barMax"] is not None:
            try:
                self.bar_max = min(int(card_yaml["barMax"]), self.MAX_BAR)
            except ValueError:
                self.log.error("No valid defined attribute barMax '%s'", card_yaml["barMax"])
        if self.bar_max > self.MAX_BAR:
            self.log.error("No valid value for attribute barMax '%s'. Should be max %d", card_yaml["barMax"],self.MAX_BAR)
            self.bar_max = self.MAX_BAR

        if "period" in card_yaml and card_yaml["period"] is not None:
            if skin.key("periods", str(card_yaml["period"]).lower()) is not None:
                self.period = skin.key("periods", str(card_yaml["period"]).lower())
            else:
                try:
                    self.period = int(card_yaml["period"])
                except ValueError:
                    self.log.error("No valid defined attribute period '%s'", card_yaml["period"])

        if "past" in card_yaml and card_yaml["past"] is not None:
            if skin.key("periods", card_yaml["past"]) is not None:
                self.past = skin.key("periods", card_yaml["past"])
            else:
                try:
                    self.past = int(card_yaml["past"])
                except ValueError:
                    self.log.error("No valid defined attribute past '%s'", card_yaml["past"])

        if "color" in card_yaml and card_yaml["color"] is not None:
            self.color =  str(name_to_16bit_color(card_yaml["color"]))

        if "life" in card_yaml and card_yaml["life"] is not None:
            if card_yaml["life"] is True:
                self.life =  True

        return ret

    def name_from_dt(self, time):
        """
        create a string from a date time object
        """
        now = datetime.datetime.now()
        if (now-time).days < 1:
            text = time.strftime(translate.key(self.MY_TYPE, "time_templ"))
        else:
            if (now-time).days <= 7:
                text = translate.weekdays_short(time.weekday())+','+time.strftime(translate.key(self.MY_TYPE, "time_templ"))
            else:
                text = time.strftime(translate.key(self.MY_TYPE, "date_templ"))
        return text

    def create_number_chart_payload(self, y_axis_label,slot, start_time, end_time): #pylint: disable=too-many-locals
        """
        create a payload for a number chart with the given values
        """
        values = slot.item.persistance_data_float(start_time, end_time)
        if values is None or len(values) == 0:
            self.log.error("No persistance or no float data for cardChart '%s' and item '%s'", self.name, slot.item.name)
            return "~65535~No data/float!~~~"

        #go over all values:
        entry_count = len(values)
        if entry_count > self.bar_max:
            bar_period = (self.period*60) / self.bar_max
        else:
            bar_period = (self.period*60) / entry_count
        #find max_value for scaling
        max_val = 0
        min_val = values[0]["state"]
        for val in values:
            max_val = max(val["state"], max_val)
            min_val = min(val["state"], min_val)
        if y_axis_label is None:
            if max_val > 1000:
                y_axis_label = f"{min_val/1000:.3f}-{max_val/1000:.3f}k"+ slot.item.unit
            else:
                y_axis_label = f"{min_val:.1f}-{max_val:.1f}"+ slot.item.unit
            #start chart from 0
            max_val -= min_val
        scale = max_val / self.MAX_Y

        #loop to create the bar values
        bar_index=0
        i=0
        bar_average=0
        chart_bars = []
        bar_start_time=start_time
        for val in values:
            #calculate delta time in this bar
            bar_average+=val["state"]
            i+=1
            delta = (val["time"] - bar_start_time).seconds
            if val["time"] > bar_start_time and delta > bar_period:
                while delta > bar_period:
                    chart_bars.append(str(int(((bar_average/i)-min_val)/scale)))
                    bar_index+=1
                    delta -= bar_period
                bar_average=0
                i=0
                bar_start_time = val["time"]
        if i > 0:
            #add last entry
            chart_bars.append(str(int(((bar_average/i)-min_val)/scale)))
            bar_index+=1

        self.log.debug("Chart '%s' has %d bars. Max value is %f. Scale is %f. Bar period is %f seconds.", self.name, bar_index, max_val, scale, bar_period)

        chart_bars[-1] += "^"+self.name_from_dt(end_time)
        chart_bars[int(len(chart_bars)/2)] += "^"+translate.key(self.MY_TYPE, "until")
        chart_bars[0] += "^"+self.name_from_dt(start_time)

        val_payload = ""
        for chart_bar in chart_bars:
            val_payload += '~' + chart_bar

        payload =  "~"+self.color+"~"+y_axis_label+"~"+val_payload
        return payload

    def create_string_chart_payload(self, y_axis_label,slot, start_time, end_time ):
        """
        create a payload for a string type chart with the given values
        """
        #if slot.item.label is not None:
        #    y_axis_label = slot.item.label

        values = slot.item.persistance_data_string(start_time, end_time)
        if values is None or len(values) == 0:
            self.log.error("No persistance data for cardChart '%s' and item '%s'", self.name, slot.item.name)
            return "~65535~No data!~~~"

        #go over all values:
        state_dict = {}
        num_states = 0
        state = None
        time = None
        total_time = 0
        for val in values:
            if time is not None:
                delta = (val["time"] - time).seconds
                if state in state_dict:
                    state_dict[state] += delta
                else:
                    state_dict[state] = delta
                    num_states += 1
                    if num_states > self.MAX_STATES:
                        self.log.error("Too many different states '%d' for string chart '%s'. Max is %d", num_states, self.name, self.MAX_STATES)
                        return "~65535~Too many states!~~~"
            else:
                delta = 0
            total_time += delta
            time=val["time"]
            state=val["state"]

        y_axis_label = self.name_from_dt(start_time)+"-"+self.name_from_dt(end_time)
        val_payload = ""
        for state, time in state_dict.items():
            val_payload += '~' + str(round(time/total_time*self.MAX_Y)) + '^' + state+':'+str(round(time/total_time*100)) + '%'

        payload =  "~"+self.color+"~"+y_axis_label+"~"+val_payload
        return payload

    def create_slots_payload(self):
        """
        evaluate the chart card data and create the payload:

        Examples:
        65535~         color of the chart bars
        Gas [kWh]~     Label on y axis
        2:4:6:8:10~    Tick labels on y axis multiplied by 10
        10~            1. bar value
        1^X1           2. bar value with label "X1"
        ~10            3. bar value
        ~1^X2          4. bar value with label "X2"
        ~10            5. bar value
        ~1^X3          6. bar value with label "X3" and so on
        ....~10~1^X4~10~1^X5~10~1^X6~10~1^X7~10")
        """

        payload = "~65535~Slot error~~~"

        #Check for valis slot 0
        if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
            #slot 1 must contain an item with numbers

            #create y axis label
            y_axis_label = "no label"
            slot = self.slots["slot_0"]
            slot.item.update_item()
            y_axis_label = None
            if slot.text is not None:
                y_axis_label = slot.text

            #get persiatance values
            end_time =  datetime.datetime.now()-datetime.timedelta(minutes=self.past)
            start_time = end_time - datetime.timedelta(minutes=self.period)
            self.log.debug("Get persistence data for chart '%s' and item '%s' from %s to %s", self.name, slot.item.name, start_time, end_time)

            if slot.item.type in self.SUPPORTED_NUMBER_TYPES or slot.item.group_type in self.SUPPORTED_NUMBER_TYPES:
                 return self.create_number_chart_payload(y_axis_label, slot, start_time, end_time)
            if slot.item.type in self.SUPPORTED_STRING_TYPES or slot.item.group_type in self.SUPPORTED_STRING_TYPES:
                 return self.create_string_chart_payload(y_axis_label, slot, start_time, end_time)
            self.log.error("Unsupported item type '%s', group type '%s' for cardChart '%s'", slot.item.type, slot.item.group_type, self.name)
            payload = "~65535~OH item type error!~~~"
        else:
            self.log.error("No valid slot 1 defined in cardChart '%s'", self.name)

        return payload

    def disconnect(self, nspanel):
        """
        disconnect from openhab
        """
        if self.life:
            super().disconnect(nspanel)

    def connect(self, nspanel):
        """
        connect to openhab
        """
        if self.life:
            super().connect(nspanel)


#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardChart.MY_TYPE] = NSPanelCardChart
