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

# project specific imports:
from nspanel.nspanel_globals import name_to_16bit_color, map_state_oh2panel
from nspanel.nspanel_base_cards import NSPanelCard, NSPanelCardWithNav
from nspanel.nspanel_slot_base_card import NSPanelCardWithSlots
from oh.oh_connector import oh
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
    MY_TYPE = NSPanelCard.CARD_SCREENSAVER
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

    def create_update_payload(self, compatibility=NSPanelCard.COMPATIBILITY_MODE_DEFAULT):
        """
        Create screensaver payload
        """
        return "weatherUpdate" + self.create_slots_payload()

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardScreenSaver.MY_TYPE] = NSPanelCardScreenSaver

class NSPanelCardScreensaver2(NSPanelCardScreenSaver):
    """
    Class for screen saver 2 with different layout
    """
    MY_TYPE = NSPanelCard.CARD_SCREENSAVER2

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardScreensaver2.MY_TYPE] = NSPanelCardScreensaver2

class NSPanelCardScreensaver3(NSPanelCardScreenSaver):
    """
    Class for screen saver 3 with different layout
    """
    MY_TYPE = NSPanelCard.CARD_SCREENSAVER3

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardScreensaver3.MY_TYPE] = NSPanelCardScreensaver3


class NSPanelCardEntities(NSPanelCardWithSlots):
    """
    Represent an card of type CardEntities in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_ENTITIES

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardEntities.MY_TYPE] = NSPanelCardEntities

class NSPanelCardGrid(NSPanelCardWithSlots):
    """
    Represent an card of type CardGrid in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_GRID

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardGrid.MY_TYPE] = NSPanelCardGrid

class NSPanelCardGrid2(NSPanelCardWithSlots):
    """
    Represent an card of type CardGrid2 in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_GRID2

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardGrid2.MY_TYPE] = NSPanelCardGrid2

class NSPanelCardGrid3(NSPanelCardWithSlots):
    """
    Represent an card of type CardGrid3 in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_GRID3

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardGrid3.MY_TYPE] = NSPanelCardGrid3

class NSPanelCardPower(NSPanelCardWithSlots):
    """
    Represent an card of type CardPower in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_POWER

    def create_slots_payload(self):
        """
        create upstate payload for all slots
        """
        payload = ""
        for slot in self.slots.values():
            payload = payload + slot.create_payload() + "~" + str(slot.speed)

        self.log.debug("Slot payload for all slots created: %s", payload)
        return payload

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardPower.MY_TYPE] = NSPanelCardPower

class NSPanelCardMedia(NSPanelCardWithSlots):
    """
    Represent an card of type CardMedia in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_MEDIA

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardMedia.MY_TYPE] = NSPanelCardMedia

class NSPanelStatusCard(NSPanelCardWithSlots):
    """
    Represent an card of type "statusCard"
    """
    MY_TYPE = NSPanelCard.CARD_STATUS

    def __init__(self, name, group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel status card with slots
        """
        super().__init__( name, NSPanelCard.STATUS_CARD_GROUP )

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

        #The behavior of icon size in status update is strange. The size is only smaller when the size payload is not send
        if self.icon_size == 1:
            return payload
        return payload + "~" + str(self.icon_size) + "~" + str(self.icon_size)

    def item_update_callback(self, item):
        """
        this callback is called from OHItensDB if the state of an item in this card is updated
        """
        self.log.debug("Call from item listner of state card '%s'. Item '%s' state in card has changed", self.name, item.name)
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
                icon = slot.item.get_icon()
            if "iconColor" in slot.json_data:
                icon_color = slot.item.get_icon_color()
            state = str(slot.item.state)
        payload = payload + "~text~slot0~"+icon+'~'+icon_color+'~'+text+'~'+ state

        #slot 1:
        #check if slot is active fro this card:
        if skin.key(self.MY_TYPE, "icon2") is False:
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
                    icon = slot.item.get_icon()
                if "iconColor" in slot.json_data:
                    icon_color = slot.item.get_icon_color()
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
    MY_TYPE = NSPanelCard.CARD_QR_WIFI

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
        icon_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "iconColor")))
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
                    icon = slot.get_icon()
            if len(state_values) > 2:
                icon_color = str(name_to_16bit_color(state_values[2]))
            else:
                if "iconColor" in slot.json_data:
                    icon_color = slot.get_icon_color()

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
            opt_icon = slot.get_icon()
            opt_icon_color = slot.get_icon_color()
#            if slot.icon_state_color is not None:
#                if slot.item.state == "ON":
#                    opt_icon_color = slot.icon_state_color[0]
#                else:
#                    opt_icon_color = slot.icon_state_color[1]

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

    def event_button_press( self, params, panel=None ):
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
        if params[0] in ["CardAlarm","CardAlarm2"] and self.MY_TYPE == self.CARD_ALARM:
            return self.event_card_alarm( params[0], params[1:])

        return super().event_button_press( params, panel )

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
                payload = payload + "~" + slot.get_icon() + "~" + slot.get_icon_color() + "~"+ map_state_oh2panel('switch', slot.item.state)  + "~" + slot_name
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

    def event_button_press( self, params, panel=None ):
        """
        process a button press event for this card
        """

        #check for cardThermo Events.
        if params[0] in ["CardThermo"] and self.MY_TYPE == self.CARD_THERMO:
            return self.event_card_thermo( params[0], params[1:] )

        return super().event_button_press( params, panel )

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardThermo.MY_TYPE] = NSPanelCardThermo

class NSPanelCardThermo2(NSPanelCardThermo):
    """
    Represent an card of type cardThermo in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_THERMO2

    def create_slots_payload(self):
        """
        evaluate the thermo slots and create the payload:
        """
        payload = "~CardThermo" #Button ID

        #Unit
        unit = translate.temperture_unit()
        unit_humidity = translate.key(self.MY_TYPE, "humidity_unit")

        #Target temperature slot:
        target1 = "?.?"
        if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
            #slot 1 must contain an themperature set item
            slot = self.slots["slot_0"]
            slot.item.update_item()
            try:
                target1 = str(slot.item.state*10)
            except ValueError:
                self.log.error("No valid defined attribute for target temperature '%s'", slot.item.state)

        payload += '~'+target1+'~'+self.min+'~'+self.max+'~'+self.step+'~'+unit+"~{active}"

        #Current Temp slot:
        temp = "?.?"
        if "slot_1" in self.slots and self.slots["slot_1"] is not None and self.slots["slot_1"].slot_class == "ohItem":
            #slot 2 must contain an themperature item
            slot = self.slots["slot_1"]
            slot.item.update_item()
            try:
                temp = str(slot.item.state*10)
            except ValueError:
                self.log.error("No valid defined attribute for current temperature '%s'", slot.item.state)

            if "icon" in slot.json_data:
                icon = slot.get_icon()
            else:
                icon = skin.key( self.MY_TYPE, "icon_temperature")
            if "iconColor" in slot.json_data:
                color = slot.get_icon_color()
            else:
                color = str(name_to_16bit_color(skin.key( self.MY_TYPE, "icon_temperature_color")))
            payload += '~~~'+icon+'~'+color+'~~~~~'+temp+'~'+color+'~~~~~'+unit+'~'+color+'~~~~'
        else:
            payload += '~~~~~~~~~~~~~~~~~~~~'

        #Humidity slot:
        humid = "??"
        if "slot_2" in self.slots and self.slots["slot_2"] is not None and self.slots["slot_2"].slot_class == "ohItem":
            #slot 2 must contain an themperature item
            slot = self.slots["slot_2"]
            slot.item.update_item()
            try:
                humid = str(slot.item.state*10)
            except ValueError:
                self.log.error("No valid defined attribute for current humidity '%s'", slot.item.state)

            color = slot.get_icon_color()
            if "icon" in slot.json_data:
                icon = slot.get_icon()
            else:
                icon = skin.key( self.MY_TYPE, "icon_humidity")
            if "iconColor" in slot.json_data:
                color = slot.get_icon_color()
            else:
                color = str(name_to_16bit_color(skin.key( self.MY_TYPE, "icon_humidity_color")))
            payload += '~'+icon+'~'+color+'~~~~~'+humid+'~'+color+'~~~~~'+unit_humidity+'~'+color+'~~~~'
        else:
            payload += '~~~~~~~~~~~~~~~~~~'

        #Status slot
        status = "??"
        if "slot_3" in self.slots and self.slots["slot_3"] is not None and self.slots["slot_3"].slot_class == "ohItem":
            #slot 3 must contain the current status of the thermostat
            slot = self.slots["slot_3"]
            slot.item.update_item()
            try:
                status = str(slot.item.state)
            except ValueError:
                self.log.error("No valid defined attribute for current status '%s'", slot.item.state)

            color = slot.get_icon_color()
            payload += '~'+status+'~'+color+'~~{active}'
        else:
            payload += '~~~~{active}'

        #slot on/off
        status = "??"
        active = '0'
        if "slot_4" in self.slots and self.slots["slot_4"] is not None and self.slots["slot_4"].slot_class == "ohItem":
            #slot 3 must contain the current status of the thermostat
            slot = self.slots["slot_4"]
            payload += slot.create_payload()
            if slot.item.state_formated.upper() != "OFF":
                active = '1'
        else:
            payload = payload + "~~~~~~"

       #button slots
        for i in range(8):
            slot_name = "slot_"+str(i+5)
            if slot_name in self.slots and self.slots[slot_name] is not None and self.slots[slot_name].slot_class == "ohItem":
                #slot 7-15 can contain a switch item
                slot = self.slots[slot_name]
                slot.item.update_item()
                payload += slot.create_payload()
            else:
                payload = payload + "~~~~~~"

        return payload.format(active=active)

    def event_button_press( self, params, panel=None ):
        """
        process a button press event for this card
        """
        #check for cardThermo Events.
        if params[0] in ["CardThermo"] and self.MY_TYPE == self.CARD_THERMO2:
            if params[1] == "tempUpd" and len(params) > 2:
                try:
                    temp = float(params[2])/10
                except ValueError:
                    self.log.error("Can not convert '%s' to temperature", params[2])
                    return None
                if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
                    #slot 0 must contain an temperature set item
                    slot = self.slots["slot_0"]
                    slot.item.set_item_state(str(temp))
                    self.log.debug("Temperature changed  to '%.2f' °C", temp)
                else:
                    self.log.warning("No Target temperature item defined in slot 1 to set '%.2f' °C", temp)
                return None

        self.log.warning("Unknown event '%s' for cardThermo2.", params[0])

        return super().event_button_press( params, panel )

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardThermo2.MY_TYPE] = NSPanelCardThermo2

class NSPanelCardChart(NSPanelCardWithSlots):
    """
    Represent an card of type cardChart in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_CHARD
    MAX_Y = 196   #Maximal y value allowed in chart
    MAX_BAR = 50  #maximal number of bars
    SUPPORTED_NUMBER_TYPES = ["Number", "Dimmer", "Rollershutter"]
    SUPPORTED_STRING_TYPES = ["String","Switch","Contact"]
    MAX_STATES = 5 #maximal number of different states shown in chart (for string items)

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
            delta = (val["time"] - bar_start_time).total_seconds()
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

        payload =  "~"+self.color+"~"+y_axis_label+"~:"+val_payload
        return payload

    def create_string_chart_payload(self, y_axis_label,slot, start_time, end_time ):
        """
        create a payload for a string type chart with the given values
        """
        #if slot.item.label is not None:
        #    y_axis_label = slot.item.label

        if slot.item.last_state_change < start_time and slot.item.last_state_change < end_time:
            #no state change in this period. Add current state as value for whole period
            values = [{"state": slot.item.state_formated, "time": start_time}, {"state": slot.item.state_formated, "time": end_time}]
        else:
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
                delta = (val["time"] - time).total_seconds()
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
        if total_time == 0:
            self.log.error("Total time is 0 for string chart '%s'.", self.name)
            return "~65535~No data!~~~"
        val_payload = ""
        for state, time in state_dict.items():
            val_payload += '~' + str(round(time/total_time*self.MAX_Y)) + '^' + translate.key( "openhabStates", state ) + ':' + str(round(time/total_time*100)) + '%'

        payload =  "~"+self.color+"~"+y_axis_label+"~:"+val_payload
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
            slot.item.update_item(slot.options)
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

class NSPanelpopupNotify(NSPanelCardWithSlots):
    """
    Represent an card of type popupNotify in lovelace ui for NSPanels
    """
    MY_TYPE = NSPanelCard.CARD_POPUP_NOTIFY

    def __init__(self, name, group=NSPanelCard.NOTIFY_CARD_GROUP):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, NSPanelCard.NOTIFY_CARD_GROUP )
        self.font_size = skin.key(self.MY_TYPE, "fontSize")
        self.heading_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "headingColor")))
        self.text_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "textColor")))
        self.b1_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "b1Color")))
        self.b2_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "b2Color")))
        self.b3_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "b3Color")))
        self.b1_text = translate.key(self.MY_TYPE, "b1Text")
        self.b2_text = translate.key(self.MY_TYPE, "b2Text")
        self.b3_text = translate.key(self.MY_TYPE, "b3Text")
        self.timeout = skin.key(self.MY_TYPE, "timeout")

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        ret = super().load_card_yaml( card_yaml )

        if "fontSize" in card_yaml and card_yaml["fontSize"] is not None:
            if isinstance(card_yaml["fontSize"],int) is False and card_yaml["fontSize"] in NSPanelCard.FONT_SIZES:
                self.font_size = skin.key("fontSize", str(card_yaml["fontSize"]).lower())
            else:
                if card_yaml["fontSize"] in skin.key("fontSizeRange"):
                    self.font_size = card_yaml["fontSize"]
                else:
                    self.log.error("No valid value for attribute fontSize '%s'. Use default instead '%d'.", card_yaml["fontSize"],self.font_size)

        if "titleColor" in card_yaml and card_yaml["titleColor"] is not None:
            self.heading_color =  str(name_to_16bit_color(card_yaml["titleColor"]))
        if "textColor" in card_yaml and card_yaml["textColor"] is not None:
            self.text_color =  str(name_to_16bit_color(card_yaml[" textColor"]))
        if "b1Color" in card_yaml and card_yaml["b1Color"] is not None:
            self.b1_color =  str(name_to_16bit_color(card_yaml["b1Color"]))
        if "b2Color" in card_yaml and card_yaml["b2Color"] is not None:
            self.b2_color =  str(name_to_16bit_color(card_yaml["b2Color"]))
        if "b1Text" in card_yaml and card_yaml["b1Text"] is not None:
            self.b1_text =  card_yaml["b1Text"]
        if "b2Text" in card_yaml and card_yaml["b2Text"] is not None:
            self.b2_text =  card_yaml["b2Text"]

        #connect all existing panels to the card to receive events if this card is active
        for panel in NSPanelCard.all_panels.values():
            self.connect(panel)
        return ret

    def is_active(self):
        """
        check if this card is active. A popupNotify card is active if the switch in slot 0 is on
        """
        if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
            #slot 0 must contain a switch item
            slot = self.slots["slot_0"]
            slot.item.update_item()
            if slot.item.state == "ON":
                return True
        return False


    def get_notification_text(self):
        """
        get the notification text for this card. The text is taken from the state of the item in slot 1 if it exists. Otherwise a default text is returned.
        """
        text = "Notification text slot missing."
        if "slot_1" in self.slots and self.slots["slot_1"] is not None and self.slots["slot_1"].slot_class == "ohItem":
            #slot 1 exist take the current state as warning text
            slot = self.slots["slot_1"]
            slot.item.update_item()
            text = slot.item.state_formated
        return text

    def create_update_payload(self, compatibility=NSPanelCard.COMPATIBILITY_MODE_DEFAULT):
        """
        Create popup Notify card payload
        """
        #Format:
        #entityUpdateDetail~*internalName*~*tHeading*~65535~*b1*~65535~*b2*~65535~Dies ist\r\nein sehr\r\nlanger text~65535~10~4~A~65535"

        payload = f"entityUpdateDetail~{self.MY_TYPE}~{self.title}~{self.heading_color}"
        payload += f"~{self.b1_text}~{self.b1_color}~{self.b2_text}~{self.b2_color}"
        if compatibility == NSPanelCard.COMPATIBILITY_MODE_FORK1:
            # Handle fork1 specific logic here. It has an additonal button.
            payload += f"~{self.b3_text}~{self.b3_color}"

        icon_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "iconColor")))
        icon= skin.key(self.MY_TYPE, "icon")
        if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem":
            #slot 0 must contain a switch item
            slot = self.slots["slot_0"]
            if "icon" in slot.json_data:
                icon = slot.get_icon()
            if "iconColor" in slot.json_data:
                icon_color = slot.get_icon_color()
        text = self.get_notification_text()

        payload += f"~{text}~{self.text_color}~{self.timeout}~{self.font_size}~{icon}~{icon_color}"

        return payload

    def item_update_callback(self, item):
        """
        this callback is called from OHItensDB if the state of an item in this card is updated
        """
        self.log.debug("Call from item listner of state card '%s'. Item '%s' state in card has changed", self.name, item.name)
        if self.is_active():
            self.log.debug("Popup notify card '%s' is active. Send notification to panels.", self.name)
            text = self.get_notification_text()
            for panel in NSPanelCard.all_panels.values():
                panel.send_notification(self.title, text)
        else:
            self.log.debug("Popup notify card '%s' is not active. No notification sent to panel.", self.name)

    def event_popup(self, params, active_notification):
        """
        this method is called when a panel with this card is leaving. We disconnect the item listener to avoid unnecessary calls if the card is not active
        """
        self.log.debug("Leave popup notify card '%s'.", self.name)
        #check if any notification card is active.
        if params[0] not in ["notifyAction", "bExit"]:
            self.log.warning("Unknown event '%s' for popup notify card.", params[0])
            return None
        if len(params) > 1 and params[1] in ["yes", "no", "button1", "button2", "button3"]:
            if "slot_2" in self.slots and self.slots["slot_2"] is not None and self.slots["slot_2"].slot_class == "ohItem":
                #slot 2 must contain a string item
                slot = self.slots["slot_2"]
                if params[1] == "button3":
                    slot.item.set_item_state(self.b3_text)
                    self.log.debug("Set item '%s' to '%s' from popup notify card '%s'.", slot.item.name, self.b3_text, self.name)
                if params[1] == "yes" or params[1] == "button2":
                    slot.item.set_item_state(self.b2_text)
                    self.log.debug("Set item '%s' to '%s' from popup notify card '%s'.", slot.item.name, self.b2_text, self.name)
                if params[1] == "no" or params[1] == "button1":
                    slot.item.set_item_state(self.b1_text)
                    self.log.debug("Set item '%s' to '%s' from popup notify card '%s'.", slot.item.name, self.b1_text, self.name)
            else:
                if "slot_0" in self.slots and self.slots["slot_0"] is not None and self.slots["slot_0"].slot_class == "ohItem" and params[1] in ["yes", "button2"]:
                    #slot 0 must contain a string item
                    self.slots["slot_0"].item.set_item_state("OFF")
        else:
            self.log.error("No action taken for popup notify card '%s'. Params: '%s'", self.name, str(params))

        notify_count = 0
        if NSPanelCard.NOTIFY_CARD_GROUP in NSPanelCard.cards_by_group:
            for card in NSPanelCard.cards_by_group[NSPanelCard.NOTIFY_CARD_GROUP].values():
                if card.is_active():
                    notify_count += 1
                    if notify_count > active_notification:
                        #navigate to the notification card
                        return card
        return None

#add this card class type to the factory
NSPanelCard.card_types[NSPanelpopupNotify.MY_TYPE] = NSPanelpopupNotify

class NSPanelCardSupervision(NSPanelCardWithNav): #pylint: disable=too-many-instance-attributes
    """
    Card to supervise the items in an openHAB group
    """
    MY_TYPE = NSPanelCard.CARD_ENTITIES
    MAX_SLOTS = 6

    TIMEOUT = "timeout"
    EQUAL = "=="
    NOT_EQUAL = "!="
    BIGGER = ">"
    SMALLER = "<"
    BIGGER_OR_EQUAL = ">="
    SMALLER_OR_EQUAL = "<="

    CYCLIC_REFRESCH = 30

    MODES = [ TIMEOUT,EQUAL,NOT_EQUAL,BIGGER,BIGGER_OR_EQUAL,SMALLER,SMALLER_OR_EQUAL ]

    def __init__(self, name, group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel card supervision
        """
        super().__init__( name, group )
        self.oh_group = None
        self.mode = "timeout"
        self.oh_value_item = None
        self.result_item = None
        self.icon = skin.icon(skin.key( NSPanelCard.CARD_SUPERVISION, "icon" ))
        self.icon_color = str(name_to_16bit_color(skin.key( NSPanelCard.CARD_SUPERVISION, "iconColor")))
        #item dictionaries
        self.members_by_name = {}
        self.values_by_label = {}
        self.dict_semaphore = threading.Semaphore()
        self.cyclic_refresh = 0
        self.payload = None
        self.compatibility = NSPanelCard.COMPATIBILITY_MODE_DEFAULT

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        ret = super().load_card_yaml( card_yaml )

        if "ohGroup" in card_yaml and card_yaml["ohGroup"] is not None:
            self.oh_group = oh().item_factory(card_yaml["ohGroup"], self.group_item_update)
            self.group_item_update(self.oh_group)
        if "mode" in card_yaml:
            if card_yaml["mode"] is not None and card_yaml["mode"] in self.MODES:
                self.mode = card_yaml["mode"]
            else:
                self.log.error( "CardSupervision '%s' mode not suppoted: '%s'", self.name, str(card_yaml["mode"]) )
                return False
        if "value" in card_yaml and card_yaml["value"] is not None:
            self.oh_value_item = oh().item_factory(card_yaml["value"], self.value_item_update)
            self.value_item_update(self.oh_value_item)
        if "result" in card_yaml and card_yaml["result"] is not None:
            self.result_item = oh().item_factory(card_yaml["result"] )
        if "icon" in card_yaml and card_yaml["icon"] is not None:
            self.icon = skin.icon(card_yaml["icon"])
        if "iconColor" in card_yaml and card_yaml["iconColor"] is not None:
            self.icon_color = str(name_to_16bit_color(card_yaml["iconColor"]))

        if self.mode == self.TIMEOUT:
            #register time tick call back
            NSPanelCard.add_time_tick_callback( self.tick )
        return ret

    def tick(self):
        """
        Timeout supervision. method must be called every second
        """
        with self.dict_semaphore:
            for member in self.members_by_name.values():
                member["timeout"] += 1
        self.cyclic_refresh += 1
        if self.cyclic_refresh >= self.CYCLIC_REFRESCH:
            self.cyclic_refresh = 0
            #create new payload
            self.payload = self.prepare_update_payload(self.compatibility)
            #inform all panels that the content has been updated
            for panel in self.all_panels.values():
                panel.content_update_info(self.name)


    def group_item_update(self, gitem):
        """
        Called when oh group is updated
        """
        self.log.debug("Group item updated: '%s'",gitem.name)
        gitem.update_item()
        members = gitem.create_group_member_items(self.member_update)
        members_by_name = {}
        for member in members:
            members_by_name[member.name] = {}
            members_by_name[member.name]["item"] = member
            if member.name in self.members_by_name:
                members_by_name[member.name]["timeout"] = self.members_by_name[member.name]["timeout"]
            else:
                members_by_name[member.name]["timeout"] = 0
            if member.last_state_update is not None:
                now = datetime.datetime.now()
                total_seconds = int((now-member.last_state_update).total_seconds())
                members_by_name[member.name]["timeout"] = total_seconds
        with self.dict_semaphore:
            self.members_by_name = members_by_name
        #create new payload
        self.payload = self.prepare_update_payload(self.compatibility)
        #inform all panels that the content has been updated
        for panel in self.all_panels.values():
            panel.content_update_info(self.name)

    def value_item_update(self, item):
        """
        Called when value item is updated
        """
        self.log.debug("Value item updated: '%s'",item.name)
        item.update_item()
        if item.type == "Group":
            members = item.create_group_member_items(self.value_update)
            values_by_label = {}
            for member in members:
                values_by_label[member.label.strip()] = member
            with self.dict_semaphore:
                self.values_by_label = values_by_label
        else:
            self.oh_value_item.update_item()
        #create new payload
        self.payload = self.prepare_update_payload(self.compatibility)
        #inform all panels that the content has been updated
        for panel in self.all_panels.values():
            panel.content_update_info(self.name)

    def member_update(self, item):
        """
        called when one of the items in the group is updated
        """
        self.log.debug("Group '%s 'member updated: '%s'",self.oh_group, item.name)
        with self.dict_semaphore:
            if item.name in self.members_by_name:
                self.members_by_name[item.name]["item"].update_item()
                self.members_by_name[item.name]["timeout"] = 0
        #create new payload
        self.payload = self.prepare_update_payload(self.compatibility)
        #inform all panels that the content has been updated
        for panel in self.all_panels.values():
            panel.content_update_info(self.name)

    def value_update(self, item):
        """
        called when value item is updated
        """
        self.log.debug("Value '%s 'member updated: '%s'",self.oh_value_item, item.name)
        with self.dict_semaphore:
            if self.oh_value_item.type == "Group":
                if item.label.strip() in self.values_by_label:
                    self.values_by_label[item.label.strip()].update_item()
            else:
                self.oh_value_item.update_item()
        #create new payload
        self.payload = self.prepare_update_payload(self.compatibility)
        #inform all panels that the content has been updated
        for panel in self.all_panels.values():
            panel.content_update_info(self.name)

    def create_slot_payload(self, icon, icon_color, value, label ):
        """
        create a payload for a single slot
        """
        return f"~text~slotName~{icon}~{icon_color}~{value}~{label}"

    def supervise(self, member, value):
        """
        supervision check
        """
        test = False
        if self.mode == self.TIMEOUT:
            if member["timeout"] > value*60:
                #check again for the latest update
                member["item"].update_item()
                if member["item"].last_state_update is not None:
                    now = datetime.datetime.now()
                    total_seconds = int((now-member["item"].last_state_update).total_seconds())
                    self.members_by_name[member["item"].name]["timeout"] = total_seconds
                if member["timeout"] > value*60:
                    test = True
        elif self.mode == self.EQUAL:
            if member["item"].state == value:
                test = True
        elif self.mode == self.BIGGER:
            if member["item"].state > value:
                test = True
        elif self.mode == self.SMALLER:
            if member["item"].state < value:
                test = True
        elif self.mode == self.BIGGER_OR_EQUAL:
            if member["item"].state >= value:
                test = True
        elif self.mode == self.SMALLER_OR_EQUAL:
            if member["item"].state <= value:
                test = True
        return test

    def get_value(self, item):
        """
        return compare value for an item
        """
        value = None
        if self.oh_value_item is not None:
            if self.oh_value_item.type == "Group":
                if item.label.strip() in self.values_by_label:
                    value = self.values_by_label[item.label.strip()].state
                else:
                    self.log.warning("Can not get value with label '%s' for item '%s'", item.label, item.name)
                    return None
            else:
                value = self.oh_value_item.state
        #try to male a float value ot of the state for better compare
        try:
            value = float(value)
        except (ValueError, TypeError):
            self.log.debug("Value is not a float value: '%s'", str(value) )
        return value

    def set_result(self, result_count):
        """
        sets the result item if defined
        """
        if self.result_item is not None:
            self.result_item.update_item()
            if self.result_item.type == "Switch":
                if result_count > 0:
                    self.result_item.set_item_state( "ON" )
                else:
                    self.result_item.set_item_state( "OFF" )
            elif self.result_item.type == "Contact":
                if result_count > 0:
                    self.result_item.set_item_state( "CLOSED" )
                else:
                    self.result_item.set_item_state( "OPEN" )
            elif self.result_item.type in ["Number", "String"]:
                self.result_item.set_item_state( str(result_count) )
            else:
                self.log.error("Unsupported result item type '%s' of item '%s'",self.result_item.type,self.result_item.name )

    def prepare_update_payload(self, compatibility=NSPanelCard.COMPATIBILITY_MODE_DEFAULT):
        """
        Create nav card payload
        """
        payload = super().create_update_payload(compatibility)
        slot_count = self.MAX_SLOTS
        result_count = 0

        for member in self.members_by_name.values():
            value = self.get_value(member["item"])
            if value is None:
                payload += self.create_slot_payload( self.icon, self.icon_color, member["item"].label, "XXX")
                slot_count -= 1
                if slot_count <= 0:
                    break
                continue

            if self.supervise(member, value):
                result_count += 1
                if slot_count > 0:
                    payload += self.create_slot_payload( self.icon, self.icon_color, member["item"].label, member["item"].state_formated)
                    slot_count -= 1

        if slot_count >= self.MAX_SLOTS:
            #create OK entry because all items are OK
            payload += self.create_slot_payload(
                            skin.icon(skin.key( NSPanelCard.CARD_SUPERVISION, "iconOK" )),
                            str(name_to_16bit_color(skin.key( NSPanelCard.CARD_SUPERVISION, "iconColorOK"))),
                            "Status", "OK")
        #set the result item, if defined
        self.set_result(result_count)
        return payload

    def create_update_payload(self, compatibility=NSPanelCard.COMPATIBILITY_MODE_DEFAULT):
        """
        Create nav card payload
        """
        if self.payload is None or self.compatibility != compatibility:
            self.compatibility = compatibility
            self.payload = self.prepare_update_payload(compatibility)
        return self.payload

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCard.CARD_SUPERVISION] = NSPanelCardSupervision

class NSPanelCardSupervision2(NSPanelCardSupervision):
    """
    Card to supervise the items in an openHAB group
    """
    MY_TYPE = NSPanelCard.CARD_SCHEDULE

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCard.CARD_SUPERVISION2] = NSPanelCardSupervision2
