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
This file contain the differnt card slots shown in the panel.
"""

#general imports
from datetime import datetime

# project specific imports:
from nspanel.nspanel_globals import interpret_options, name_to_16bit_color, map_state_oh2panel
from oh.oh_connector import OHItemDB
from file_logger import file_logger as FLOGGER
from lang import translate
from skin import skin
#
# global constants
#

#
# Class definitions
#
class NSPanelCardSlot(): #pylint: disable=too-many-instance-attributes
    """
    base class for an nspanel card slots
    """
    MY_TYPE = "NSPanelCardSlot"

    #Slot types constants in lovelace
    SLOT_NUMBER = "number"
    SLOT_LIGHT = "light"
    SLOT_SHUTTER = "shutter"
    SLOT_TEXT = "text"
    SLOT_BUTTON = "button"
    SLOT_SWITCH = "switch"
    SLOT_INPUT_SEL = "input_sel"
    SLOT_OPENWEATHERMAP = "openweathermap"

    #translator
    translator = None
    #all classes which ar instantiable:
    all_slot_classes = {}
    #global slot logger
    log = FLOGGER.create_log_handler("NSPanelcardSlot")

    @classmethod
    def set_translator_db( cls, db):
        """
        set translator db
        """
        translate.set_transloator_db( db )

    @classmethod
    def set_skin_db( cls, db):
        """
        set skin db
        """
        skin.set_skin_db( db )

    def __init__(self, json_data, slot_index, card):
        """
        Constructor of a Slot in a NSPanelCard
        """
        #nspanel slot name is "slot_" + slot index in card
        self.name = "slot_"+ str(slot_index)
        #reference to card:
        self.index = slot_index
        self.card = card
        #addtional attributes
        self.slot_class = None
        self.text = None
        self.icon = skin.key(self.MY_TYPE, "icon")
        self.icon_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, "iconColor")))
        self.type = self.MY_TYPE
        self.json_data = json_data

        """
        Set attributes from json data
        """
        self.slot_class = json_data["class"]
        if "text" in json_data:
            self.text = str(json_data["text"])

        if "icon" in json_data and json_data["icon"] is not None:
            self.icon = skin.icon( json_data["icon"] )
        if "iconColor" in json_data and json_data["iconColor"] is not None:
            self.icon_color = str(name_to_16bit_color(json_data["iconColor"]))

    def create_payload(self):
        """
        create upstate payload for this slot
        """
        if self.text is None:
            self.text = "-text undefined-"
        payload = '~' + self.type + "~" + self.name + "~"
        payload = payload + self.icon+self.card.icon_size_payload() + "~" + self.icon_color + "~"
        payload = payload + self.text + "~"
        return payload

    @classmethod
    def factory( cls, json_data, slot_index, card ): #pylint: disable=too-many-return-statements
        """
        creates a slot object from json data
        """
        if "class" in json_data and isinstance(json_data, dict): #pylint: disable=too-many-nested-blocks
            if str(json_data["class"]) in cls.all_slot_classes:
                if json_data["class"] == "ohItem":
                    #check also for type
                    classes = cls.all_slot_classes[json_data["class"]]
                    if "type" in json_data:
                        if json_data["type"] in classes:
                            #class exist intantiate it check it item defined
                            oh_class = classes[json_data["type"]]
                            if "item" in json_data:
                                return oh_class(json_data, slot_index, card)
                            cls.log.error("No item defined in '%s' of slot %d in card '%s'.",json_data["class"], slot_index, card.name )
                            return None
                        cls.log.error("No slot class with type '%s' defined in '%s' of slot %d in card '%s'.",json_data["type"],json_data["class"], slot_index, card.name )
                        return None
                    cls.log.error("No slot type defined in '%s' of slot %d in card '%s'.",json_data["class"], slot_index, card.name )
                    return None

                if json_data["class"] == "navigate":
                    #check for "navTo" attribute
                    if "navTo" in json_data:
                        #instanciate navigation slot
                        return cls.all_slot_classes["navigate"](json_data, slot_index, card)
                    cls.log.error("No navTo defined in '%s' of slot %d in card '%s'.",json_data["class"], slot_index, card.name )
                #cls.LOG.error("Unknown slot class '%s' defined in slot %d in card '%s'.",json_data["class"], slot_index, card.name )

                #Other class without additinal attributes (for example class: None)
                return cls.all_slot_classes[str(json_data["class"])](json_data, slot_index, card)
        cls.log.error("No class defined in slot %d in card '%s'.", slot_index, card.name )
        return None

class NsPanelCardSlotNavigation( NSPanelCardSlot ):
    """
    base class for slots with navigation
    """
    MY_TYPE ="navigate"

    def __init__(self, json_data, slot_index, card):
        """
        Constructor of a Slot of type navigation in a NSPanelCard
        """
        #nspanel root topic
        super().__init__( json_data, slot_index, card )
        self.nav_to = str(json_data["navTo"])
        self.log.debug("Constructed!" )

    def create_payload(self):
        """
        create upstate payload for navigate slot
        """
        #take navTo attribute as text if no text available
        if self.text is None:
            self.text = self.nav_to
        payload = '~button~' + self.name + "~"
        payload = payload + self.icon+self.card.icon_size_payload() + "~" + self.icon_color + "~"
        payload = payload + self.text + "~" + skin.key("default", "linkIcon")
        self.log.debug("Navigate payload created: %s", payload)
        return payload

#add to factory dictionary
NSPanelCardSlot.all_slot_classes["navigate"] = NsPanelCardSlotNavigation

class NsPanelCardSlotDelete( NSPanelCardSlot ):
    """
    base class for empty slots
    """
    MY_TYPE = "None"

    def create_payload(self):
        """
        create upstate payload for "delete" slot
        """
        payload = "~delete~~~~~"
        self.log.debug("'delete' payload created: %s", payload)
        return payload

#add to factory dictionary
NSPanelCardSlot.all_slot_classes[NsPanelCardSlotDelete.MY_TYPE] = NsPanelCardSlotDelete

class NsPanelCardSlotOhItem( NSPanelCardSlot ):
    """
    base class for slots with openhab items
    """
    MY_TYPE="NsPanelCardSlotOhItem"

    #openhab connector
    OH = None

    @classmethod
    def create_openhab_connector(cls, host, port, timeout, api_key):
        """
        creates an openhab connector object globally used in all slots
        """
        if cls.OH is not None:
            cls.log.debug("Openhab connector already exists. New connector will be created.")
            #disconnect existing connection before creating a new one. That listener tHReads are stopped and will be restarted with new connection.
            cls.OH.disconnect()

        cls.OH = OHItemDB( host, port, timeout, api_key )
        if cls.OH is None:
            cls.log.error("Openhab connection could not be established.")

    def __init__(self, json_data, slot_index, card):
        """
        Constructor of a Slot in a NSPanelCard
        """
        super().__init__(json_data, slot_index, card)
        self.item = self.OH.item_factory(json_data["item"], card.item_update_callback )
        if "options" in json_data and json_data["options"] is not None:
            self.options = interpret_options(str(json_data["options"]))
        else:
            self.options = None
        self.icon_state_color = None

        self.log.debug("NsPanelCardSlotOhItem '%s' constructed!", self.name )

    def create_payload(self, stateText="empty"):
        """
        create upstate payload for ohitem slot
        """
        #take label from openhab item as text if no text available
        text = self.text
        if text is None:
            text = self.item.label
        else:
            if text == "=itemState":
                text = stateText

        payload = '~' + self.type + "~" + self.name + "~"
        payload = payload + self.icon+self.card.icon_size_payload() + "~" + self.icon_color + "~"
        payload = payload + text + "~"
        return payload

    def get_icon_color(self):
        """
        returns the best matching icon color
        """
        return self.icon_color

    def create_status_payload(self, icon, color):
        """
        send status update command to panel
        """
        #Format: "statusUpdate~iconLeft~iconCOlorLeft~iconRight~iconColorRight")

        slot_text=icon
        slot_color=color
        self.item.update_item(self.options)
        #take label from openhab item as text if no text available
        text = self.text
        if text is None:
            text = self.item.label
        else:
            if text == "=itemState":
                text = translate.key( "openhabStates", self.item.state_formated )
        slot_text = self.icon+text
        slot_color = self.get_icon_color()

        return "~" + slot_text + '~' + slot_color


#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"] = {}

class NsPanelCardSlotOhItemText( NsPanelCardSlotOhItem ):
    """
    base class for slots with openhab items of type text
    """
    MY_TYPE=NSPanelCardSlot.SLOT_TEXT

    def create_payload(self, stateText="empty"):
        """
        create upstate payload for text slot
        """
        #overwrite options in openhab item with locally defined options, if availbale:
        self.item.update_item(self.options)
        payload = super().create_payload(self.item.state_formated)
        payload = payload + self.item.state_formated
        self.log.debug("Text payload created: %s", payload)
        return payload

#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"][NsPanelCardSlotOhItemText.MY_TYPE] = NsPanelCardSlotOhItemText

class NsPanelCardSlotOhItemWeather( NsPanelCardSlotOhItem ):
    """
    base class for slots with openwaethermap items info
    """
    MY_TYPE=NSPanelCardSlot.SLOT_OPENWEATHERMAP

    def __init__(self, json_data, slot_index, card):
        """
        Constructor of a Slot with openweathermap items
        """
        super().__init__(json_data, slot_index, card)
        self.item = self.OH.item_factory(json_data["item"], card.item_update_callback )
        if "textItem" in json_data and json_data["textItem"] is not None:
            self.text_item = self.OH.item_factory(str(json_data["textItem"]), card.item_update_callback )
        else:
            self.text_item = None
        if "timeItem" in json_data and json_data["timeItem"] is not None:
            self.time_item = self.OH.item_factory(str(json_data["timeItem"]), card.item_update_callback )
        else:
            self.time_item = None

        self.log.debug("NsPanelCardSlotOhItemWaether '%s' constructed!", self.name )

    def create_payload(self, stateText="empty"):
        """
        create upstate payload for text slot
        """
        #example :~"+main_icon+"~"+main_icon_color+"~~"+"9:00"
        self.item.update_item()
        self.time_item.update_item()

        weather_id = skin.key("openweathermap", self.item.state)
        if weather_id is None:
            weather_id = "error"

        icon = skin.key("openweathermap_icons", weather_id )
        icon_color = str(name_to_16bit_color(skin.key("openweathermap_icons_colors", weather_id )))

        if self.text_item is not None:
            self.text_item.update_item()
            text = self.text_item.state_formated #this can be the tempearture or other info
        else:
            text = "TxTx"

        time_str = "00:00"
        if self.time_item is not None:
            #bild time string for this
            try:
                dt = datetime.fromisoformat(self.time_item.state)
                time_str = dt.strftime(translate.weather_time_templ())
            except ValueError:
                self.log.error("Could not convert content '%s' in openhab item '%s' to datetime object.", self.time_item.state, self.time_item.name )

        payload = "~text~"+self.name+"~" + icon + '~' + icon_color + '~' + time_str + '~' + text
        self.log.debug("Weather slot payload created: %s", payload)
        return payload

#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"][NsPanelCardSlotOhItemWeather.MY_TYPE] = NsPanelCardSlotOhItemWeather


class NsPanelCardSlotOhItemSwitch( NsPanelCardSlotOhItem ):
    """
    base class for slots with openhab items of type switch
    """
    MY_TYPE=NSPanelCardSlot.SLOT_SWITCH

    def __init__(self, json_data, slot_index, card):
        """
        Constructor of a Slot in a NSPanelCard
        """
        super().__init__(json_data, slot_index, card)

        self.icon_state_color = [self.icon_color, self.icon_color]
        if "iconStateColor" not in json_data or json_data["iconStateColor"] is None or json_data["iconStateColor"] is True:
            self.icon_state_color[0] = str(name_to_16bit_color(skin.key(self.MY_TYPE, 'color_on')))
            self.icon_state_color[1] = str(name_to_16bit_color(skin.key(self.MY_TYPE, 'color_off')))
        else:
            if json_data["iconStateColor"] is not False:
                color_names = json_data["iconStateColor"].split('|')
                self.icon_state_color[0] = str(name_to_16bit_color(color_names[0].strip()))
                if len(color_names) >= 2:
                    self.icon_state_color[1] = str(name_to_16bit_color(color_names[1].strip()))
                else:
                    self.icon_state_color[1] = str(name_to_16bit_color(skin.key(self.MY_TYPE, 'color_off')))

            self.icon_color = str(name_to_16bit_color(skin.key(self.MY_TYPE, 'default_icon_color')))
        self.log.debug("Constructed!")

    def get_icon_color(self):
        """
        returns the best matching icon color
        """
        self.item.update_item()
        state = map_state_oh2panel("switch", self.item.state)
        if state == "1":
            self.icon_color = self.icon_state_color[0]
        else:
            self.icon_color = self.icon_state_color[1]
        return self.icon_color

    def create_payload(self, stateText="empty"):
        """
        create update payload for switch slot
        """
        #overwrite options in openhab item with locally defined options, if availbale:
        self.get_icon_color()
        state = map_state_oh2panel("switch", self.item.state)
        payload = super().create_payload(translate.key( "openhabStates", self.item.state_formated ))

        #create payload with new state now
        payload = payload + state
        self.log.debug("Switch payload created. State=%s: %s", state, payload)
        return payload


#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"][NsPanelCardSlotOhItemSwitch.MY_TYPE] = NsPanelCardSlotOhItemSwitch

class NsPanelCardSlotOhItemButton( NsPanelCardSlotOhItem ):
    """
    base class for slots with openhab items of type button
    """
    MY_TYPE=NSPanelCardSlot.SLOT_BUTTON

    def create_payload(self, stateText="empty"):
        """
        create updtate payload for button slot
        """
        #example: button~button.entityName~3~17299~bt-name~bt-text
        #overwrite options in openhab item with locally defined options, if availbale:
        self.item.update_item(self.options)
        #take the plain state data from openhab as button state text but check if it acn be translated in other language!
        state = translate.key( "openhabStates", self.item.state_formated )
        payload = super().create_payload(state)
        payload = payload + state
        self.log.debug("Number payload created: %s", payload)
        return payload


#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"][NsPanelCardSlotOhItemButton.MY_TYPE] = NsPanelCardSlotOhItemButton

class NsPanelCardSlotOhItemNumber( NsPanelCardSlotOhItem ):
    """
    base class for slots with openhab items of type number
    """
    MY_TYPE=NSPanelCardSlot.SLOT_NUMBER
    DEFAULT_MIN = "0"
    DEFAULT_MAX = "100"

    def __init__(self, json_data, slot_index, card):
        """
        Constructor of a Slot of type ohItem in a NSPanelCard
        """
        #nspanel root topic
        super().__init__( json_data, slot_index, card )

        #Set attributes from json data:
        if "min" in json_data and json_data["min"] is None:
            self.min = str(json_data["min"])
        else:
            self.min = self.DEFAULT_MIN
            self.log.debug("Attribute min not defined in slot %d of ohItem '%s'. Value '%s' will be used.", self.index, self.card.name, self.DEFAULT_MIN)
        if "max" in json_data and json_data["max"] is None:
            self.max = str(json_data["max"])
        else:
            self.max = self.DEFAULT_MAX
            self.log.debug("Attribute max not defined in slot %d of ohItem '%s'. Value '%s' will be used.", self.index, self.card.name, self.DEFAULT_MAX)
        self.log.debug("Constructed!" )

    def create_payload(self, stateText="empty"):
        """
        create upstate payload for number slot
        """
        #overwrite options in openhab item with locally defined options, if availbale:
        self.item.update_item(self.options)
        payload = super().create_payload(self.item.state_formated)
        payload = payload + str(self.item.state)+"|" + self.min + "|" + self.max
        self.log.debug("Number payload created: %s", payload)
        return payload

#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"][NsPanelCardSlotOhItemNumber.MY_TYPE] = NsPanelCardSlotOhItemNumber


class NsPanelCardSlotOhItemLight( NsPanelCardSlotOhItemSwitch ):
    """
    base class for slots with openhab items of type light
    """
    MY_TYPE=NSPanelCardSlot.SLOT_LIGHT

    def __init__(self, json_data, slot_index, card):
        """
        Constructor of a Slot of type ohItem in a NSPanelCard
        """
        #nspanel root topic
        #list with all items in this slot oblect (needed for pupup)
        super().__init__( json_data, slot_index, card )

        self.log.debug("Constructed!" )
        #Set attributes from json data
        self.dimmer_item = None
        self.col_temp_item = None
        self.color_item = None

        if "dimmerItem" in json_data and json_data["dimmerItem"] is not None:
            self.dimmer_item = self.OH.item_factory(str(json_data["dimmerItem"]), card.item_update_callback)
        else:
            self.log.info("Attribute 'dimmerItem' not defined in slot %d of ohItem '%s'. Better use switch instead of light?", self.index, self.card.name)
        if "colorItem" in json_data and json_data["colorItem"] is not None:
            self.color_item = self.OH.item_factory(str(json_data["colorItem"]), card.item_update_callback)
        if "colTempItem" in json_data and json_data["colTempItem"] is not None:
            self.col_temp_item = self.OH.item_factory(str(json_data["colTempItem"]), card.item_update_callback)

    def create_popup_payload(self):
        """
        create the payload for the poplight card
        """

        self.item.update_item()
        state = map_state_oh2panel("switch", self.item.state )
        dimmer_state = 'disable'
        if self.dimmer_item is not None:
            self.dimmer_item.update_item()
            dimmer_state = self.dimmer_item.state_int
        color_state = 'disable'
        if self.color_item is not None:
            self.color_item.update_item()
            color_state = "enable" #colorwheel can be just enabled and disabled. It dies not show the current value
        col_temp_state = 'disable'
        if self.col_temp_item is not None:
            self.col_temp_item.update_item()
            col_temp_state = self.col_temp_item.state_int

        #Format
        #entityUpdateDetail~entityName~*icon*~*iconColor*~*switchState*~*sliderBrightnessPos*~
        #*sliderColorTempPos*~*colorMode*~*Text1*~*Text2*~*Text3*
        #entityName:          reference to the entity in the slot which created the popup
        #icon:                which is shown in upper left corner
        #iconColor:           color of this item
        #switchState:         state of the switch 1/0
        #sliderBrightnessPos: brighness value 0-100
        #sliderColorTempPos:  color temperature 0-100
        #colorMode:           disable/enable the color weel
        #Text1:               Text on the color wheel icon
        #Text2:               Text on the color temperature slider
        #Text2:               Text on the brighness slider

        text1 = translate.key( self.MY_TYPE, "color")
        text2 = translate.key( self.MY_TYPE, "colTemp")
        text3 = translate.key( self.MY_TYPE, "brightness")

        return "~" + self.name + '~' + self.icon + '~' + self.icon_color + '~'\
                    + state + '~' + dimmer_state + '~' + col_temp_state + '~' + color_state + '~'\
                    + text1 + '~' + text2 + '~' + text3

#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"][NsPanelCardSlotOhItemLight.MY_TYPE] = NsPanelCardSlotOhItemLight

class NsPanelCardSlotOhItemShutter( NsPanelCardSlotOhItem ):
    """
    base class for slots with openhab items of type shutter
    """
    MY_TYPE=NSPanelCardSlot.SLOT_SHUTTER

    def __init__(self, json_data, slot_index, card):
        """
        Constructor of a Slot in a NSPanelCard
        """
        self.tilt_item = None
        super().__init__(json_data, slot_index, card)
        if "shutterControls" in json_data and json_data["shutterControls"] is not None and len(str(json_data["shutterControls"]).split('|')) == 3:
            self.shutter_controls = str(json_data["shutterControls"])
        else:
            self.shutter_controls = "enable|enable|enable"
        if "tiltItem" in json_data and json_data["tiltItem"] is not None:
            self.tilt_item = self.OH.item_factory(str(json_data["tiltItem"]), card.item_update_callback)
        if "tiltControls" in json_data and json_data["tiltControls"] is not None and len(str(json_data["tiltControls"]).split('|')) == 3:
            self.tilt_controls = str(json_data["tiltControls"])
        else:
            self.tilt_controls = "enable|enable|enable"
        self.log.debug("Constructed!")

    def create_payload(self, stateText="empty"):
        """
        create update payload for slot with an ohItem
        """
        self.item.update_item()
        #create payload for rollershutter slot
        icon_up = skin.key( self.MY_TYPE, "shutter_up" )
        icon_down = skin.key( self.MY_TYPE, "shutter_down" )
        icon_stop = skin.key( self.MY_TYPE, "shutter_stop" )
        #example shutter state: "A|B|C|enable|enable|enable"
        payload = super().create_payload(self.item.state_formated)+icon_up+"|"+icon_stop+"|"+icon_down+"|"+self.shutter_controls
        self.log.debug("Shutter payload created: %s", payload)
        return payload

    def create_popup_payload(self): #pylint: disable=too-many-locals
        """
        create the payload for a rollershutter popup
        """
        #entityUpdateDetail
        #~entityName
        # ~*sliderPos*          :0-100
        # ~2ndrow               :2nd row text
        # ~textPosition         :text shutter slider
        # ~icon1
        # ~iconUp
        # ~iconStop
        # ~iconDown
        # ~iconUpStatus         :enable/disable
        # ~iconStopStatus       :enable/disable
        # ~iconDownStatus       :enable/disable
        # ~textTilt             :text tilt slider
        # ~iconTiltLeft
        # ~iconTiltStop
        # ~iconTiltRight
        # ~iconTiltLeftStatus   :enable/disable
        # ~iconTiltStopStatus   :enable/disable
        # ~iconTiltLeftStatus   :enable/disable
        # ~tiltPos              :0-100
        self.item.update_item()
        text_position = translate.key( self.MY_TYPE, "position")
        icon1 = skin.key( self.MY_TYPE, "icon" )
        icon_up = skin.key( self.MY_TYPE, "shutter_up" )
        icon_down = skin.key( self.MY_TYPE, "shutter_down" )
        icon_stop = skin.key( self.MY_TYPE, "shutter_stop" )
        status = self.shutter_controls.split('|')
        icon_up_status = status[0].strip()
        icon_down_status = status[1].strip()
        icon_stop_status = status[2].strip()
        if self.tilt_item is not None:
            text_tilt = translate.key( self.MY_TYPE, "tilt")
            self.tilt_item.update_item()
            tilt_status = self.tilt_item.state_int
            status = self.tilt_controls.split('|')
            icon_t_up_status = status[0].strip()
            icon_t_down_status = status[1].strip()
            icon_t_stop_status = status[2].strip()
            icon_t_up = skin.key( self.MY_TYPE, "tilt_up" )
            icon_t_down = skin.key( self.MY_TYPE, "tilt_down" )
            icon_t_stop = skin.key( self.MY_TYPE, "tilt_stop" )
        else:
            text_tilt = ""
            tilt_status = "disable"
            icon_t_up_status = "disable"
            icon_t_down_status = "disable"
            icon_t_stop_status = "disable"
            icon_t_up = ""
            icon_t_down = ""
            icon_t_stop = ""
        return '~' + self.name + '~' + self.item.state_int + '~' + self.card.title + "~" + text_position +\
               '~' + icon1 + '~' + icon_up + '~' + icon_stop + '~' + icon_down +\
               '~' + icon_up_status + '~' + icon_stop_status + '~' + icon_down_status +\
               '~' + text_tilt + '~' + icon_t_up + '~' + icon_t_stop + '~' + icon_t_down +\
               '~' + icon_t_up_status + '~' + icon_t_stop_status + '~' + icon_t_down_status + '~' + tilt_status

#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"][NsPanelCardSlotOhItemShutter.MY_TYPE] = NsPanelCardSlotOhItemShutter

class NsPanelCardSlotOhItemInputSel( NsPanelCardSlotOhItem ):
    """
    base class for slots with openhab items of type input select
    """
    MY_TYPE=NSPanelCardSlot.SLOT_INPUT_SEL

    def create_payload(self, stateText="empty"):
        """
        create update payload for slot with an ohItem
        """
        #overwrite options in openhab item with locally defined options, if availbale:
        self.item.update_item(self.options)
        #create payload with new state now
        payload = super().create_payload(self.item.state_formated)+self.item.state_formated
        self.log.debug("InpuSel payload created: %s", payload)
        return payload

    def create_popup_payload(self):
        """
        create the payload for the popup Input select card
        """
        self.item.update_item(self.options)
        state = self.item.state_formated

        #Format
        #Example: entityUpdateDetail2~*entity_id*~~*icon_color*~*input_sel*~*state*~*options*
        #entityUpdateDetail2  Command key
        #entityName:          reference to the entity in the slot which created the popup
        #icon:                which is shown in upper left corner
        #iconColor:           color of this item
        #input_sel            just a text which is added to the event
        #state                current state. Will be highlited in the list
        #options              ? separated list

        options = ""
        for label in self.item.options.values():
            options = options + label + '?'

        if len(self.item.options) > 0:
            #remove last "?"
            options = options[:-1]

        return "2~" + self.name + '~' + self.icon + '~' + self.icon_color + '~'\
                    + "option" + '~' + state + '~' + options

#add ohItem class to factory dictionary
NSPanelCardSlot.all_slot_classes["ohItem"][NsPanelCardSlotOhItemInputSel.MY_TYPE] = NsPanelCardSlotOhItemInputSel
