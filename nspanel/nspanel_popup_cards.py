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

# project specific imports:
from nspanel.nspanel_globals import name_to_16bit_color, map_state_pannel2oh, pos_to_hs_color
from nspanel.nspanel_base_cards import NSPanelCardSlot, NSPanelCard
from skin import skin

class NSPanelCardPopup(NSPanelCard):
    """
    class for popup cards
    """
    MY_TYPE = "NSPanelCardPopup"

    def __init__(self, name, slot_obj=None ):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name )
        #set corresponding slot object
        self.slot_obj = slot_obj

    def create_update_payload(self):
        """
        Create nav card payload
        """
        return "entityUpdateDetail" + self.slot_obj.create_popup_payload()

    def disconnect(self, nspanel):
        """
        disconnect from openhab (nothing to do for popup card)
        """
        self.log.debug("Disconnect nspanel '%s' to card '%s'", nspanel.name, self.name )

    def connect(self, nspanel):
        """
        connect to openhab (nothing to do for popup card)
        """
        self.log.debug("Connect nspanel '%s' to card '%s'", nspanel.name, self.name )

class NSPanelCardPopupLight(NSPanelCardPopup):
    """
    class for popup light cards
    """
    MY_TYPE = "popupLight"

    def event_button_press( self, slot_name, params ): #pylint: disable=too-many-branches
        """
        process a button press event for this card
        """
        #"brightnessSlider,34'
        #colorTempSlider,89
        #colorWheel,59|48|160

        self.log.debug("Process for item '%s' the button press event: %s", slot_name, str(params))
        if slot_name != self.slot_obj.name:
            self.log.debug("Slot name '%s' not matching to popup.", slot_name )
            return None
        if params[0] == 'brightnessSlider' and len(params) >= 2:
            if self.slot_obj.dimmer_item is not None:
                self.slot_obj.dimmer_item.set_item_state(params[1])
                self.log.info("Brigtness event '%s' for slot '%s'", params[0], self.slot_obj.dimmer_item.name)
            else:
                self.log.error("event_button_press: DimmerItem does not exist")
        if params[0] == 'colorTempSlider' and len(params) >= 2:
            if self.slot_obj.col_temp_item is not None:
                self.slot_obj.col_temp_item.set_item_state(params[1])
                self.log.info("Color Temperatur event '%s' for slot '%s'", params[0], self.slot_obj.col_temp_item.name)
            else:
                self.log.error("event_button_press: colTempItem does not exist")
        if params[0] == 'OnOff' and len(params) >= 2:
            if self.slot_obj.item is not None:
                self.slot_obj.item.set_item_state(map_state_pannel2oh(params[0], params[1]))
                self.log.info("Switch event '%s' for slot '%s'", params[0], self.slot_obj.item.name)
            else:
                self.log.error("event_button_press: SwitchItem does not exist")
        if params[0] == 'colorWheel' and len(params) >= 2:
            if self.slot_obj.color_item is not None:
                coordinates = params[1].split('|')
                if len(coordinates) >= 2:
                    try:
                        x = int(coordinates[0])
                        y = int(coordinates[1])
                    except ValueError:
                        self.log.error("event_button_press: Invalid color wheel values '%s'", params[1])
                        return None
                    if self.slot_obj.color_item is not None:
                        try:
                            brightness = self.slot_obj.color_item.state.split(',')[2]
                        except IndexError:
                            self.log.error("event_button_press: Can not get brightness from item state '%s'", self.slot_obj.color_item.state)
                            return None
                    else:
                        self.log.error("event_button_press: itemColor not defined in this slot '%s'", self.slot_obj.name )
                        return None
                    self.log.debug("Color wheel event with x: %d and y: %d, old brightness: %s", x, y, brightness)
                    #convert x and y to hue and saturation values
                    hsb = pos_to_hs_color(x, y) + ',' + brightness
                    self.slot_obj.color_item.set_item_state(hsb)
                    self.log.info("New color value '%s' for item '%s'", hsb, self.slot_obj.color_item.name)
            else:
                self.log.error("event_button_press: SwitchItem does not exist")
        return None

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardPopupLight.MY_TYPE] = NSPanelCardPopupLight

class NSPanelCardPopupInputSelect(NSPanelCardPopup):
    """
    class for popup input_sel cards
    """
    MY_TYPE = "popupInSel"

    def event_button_press( self, slot_name, params ):
        """
        process a button press event for this card
        """
        #params:
        #mode-option,2

        self.log.debug("Process for item '%s' the button press event: %s", slot_name, str(params))
        if slot_name != self.slot_obj.name:
            self.log.warning("Slot name '%s' not matching to popup.", slot_name )
            return None
        if len(params) >= 2 and params[0].lower() == "mode-option":
            new_state = self.slot_obj.item.state_formated
            try:
                #try to find new value in options
                new_state = list(self.slot_obj.item.options.keys())[int(params[1])]
            except ValueError:
                self.log.warning("Selected value can not be found in options!")
            if new_state != self.slot_obj.item.state_formated:
                self.slot_obj.item.set_item_state(new_state)
            self.log.info("Input select event '%s' for item '%s'", new_state, self.slot_obj.item.name)
            return None
        return None

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardPopupInputSelect.MY_TYPE] = NSPanelCardPopupInputSelect

class NSPanelCardPopupShutter(NSPanelCardPopup):
    """
    class for popup input_sel cards
    """
    MY_TYPE = "popupShutter"
    TILT_BUTTONS = {'tiltopen': 'UP', 'tiltclose': 'DOWN', 'tiltstop': 'STOP'}

    def event_button_press( self, slot_name, params ):
        """
        process a button press event for this card
        """
        #params:
        #mode-option,2

        self.log.debug("Process for item '%s' the button press event: %s", slot_name, str(params))
        if slot_name != self.slot_obj.name:
            self.log.warning("Slot name '%s' not matching to popup.", slot_name )
            return None
        if len(params) >= 1 and params[0].lower() in ['up', 'down', 'stop']:
            self.slot_obj.item.set_item_state(params[0].upper())
            self.log.info("Rollershutter event '%s' for item '%s'", params[0].upper(), self.slot_obj.item.name)
            return None
        if len(params) >= 2 and params[0].lower() in ['positionslider']:
            self.slot_obj.item.set_item_state(params[1])
            self.log.info("Rollershutter slider event '%s' for item '%s'", params[1].upper(), self.slot_obj.item.name)
            return None
        if len(params) >= 1 and params[0].lower() in ['tiltopen', 'tiltclose', 'tiltstop']:
            self.slot_obj.item.set_item_state(self.TILT_BUTTONS[params[0].lower()])
            self.log.info("Rollershutter event '%s' for item '%s'", params[0].upper(), self.slot_obj.item.name)
            return None
        if len(params) >= 2 and params[0].lower() in ['tiltslider']:
            self.slot_obj.tilt_item.set_item_state(params[1])
            self.log.info("Rollershutter tilt slider event '%s' for item '%s'", params[1].upper(), self.slot_obj.item.name)
            return None
        return None

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardPopupShutter.MY_TYPE] = NSPanelCardPopupShutter

class NSPanelCardPopupThermo(NSPanelCardPopup):
    """
    class for popup thermo card
    """
    MY_TYPE = "popupThermo"

    def create_update_payload(self):
        """
        Create nav card payload
        """
        #Fromat:
        #entityUpdateDetail~{entity_id}~{icon_id}~{icon_color}~{heading}~{slotID}~{mode}~mode1~mode1?mode2?mode3~{heading}~{slotID}~{mode}~mode1~mode1?mode2?mode3~{heading}~{slotID}~{mode}~mode1~mode1?mode2?mode3~
        #Error in documentation of lovelace ui! There is one additonal parameter after each heading with the slot id!

        payload = "entityUpdateDetail~CardThermo~" + skin.key(self.MY_TYPE, "icon") + '~'+\
                                                     str(name_to_16bit_color(skin.key(self.MY_TYPE, "iconColor")))

        #there are 3 entries for input_sel items in the popup card
        for i in range(4):
            #state slots:
            count = 0
            slot_name = "slot_"+str(i+2)
            if slot_name in self.slot_obj.slots and self.slot_obj.slots[slot_name] is not None and self.slot_obj.slots[slot_name].slot_class == "ohItem":
                #slot 3,4,5,6 must contain an input_sel items
                slot = self.slot_obj.slots[slot_name]
                if slot.type == NSPanelCardSlot.SLOT_INPUT_SEL:
                    count = count + 1
                    if count == 3:
                        #popup card is full
                        break
                    slot.item.update_item()
                    if slot.text is not None:
                        heading = slot.text
                    else:
                        heading = str(slot.item.label)
                    options=""
                    for label in slot.item.options.values():
                        options = options + label + '?'

                    if len(slot.item.options.values()):
                        #remove last "?"
                        options = options[:-1]

                    payload = payload + "~" + heading + "~"+slot_name+"~" + str(slot.item.state_formated) + "~" + options
        payload = payload + (3-count) * "~~~~"
        return payload

#add this card class type to the factory
NSPanelCard.card_types[NSPanelCardPopupThermo.MY_TYPE] = NSPanelCardPopupThermo

