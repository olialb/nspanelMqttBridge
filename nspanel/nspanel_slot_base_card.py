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
This file contain the differnt base classe for cards shown in the panel.
"""

#general imports

# project specific imports:
from nspanel.nspanel_globals import map_state_pannel2oh
from nspanel.nspanel_base_cards import NSPanelCardWithNav, NSPanelCard
from nspanel.nspanel_card_slots import NSPanelCardSlot
from oh.oh_connector import oh

#
# global constants
#

#
# Class definitions
#
class NSPanelCardWithSlots(NSPanelCardWithNav):
    """
    Base class for cards list of items
    """
    MY_TYPE = "NSPanelCardWithSlots"

    def __init__(self, name, group=NSPanelCard.CARDS_HOME ):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, group )

        #slot dictionary
        self.slots = {}

    def load_slots_yaml( self, slots_yaml ):
        """
        Load slots for a card
        """
        self.log.debug("Load slots yaml: %s", str(slots_yaml))

        #test if slots are iterable
        try:
            _ = (e for e in slots_yaml)
        except TypeError:
            self.log.error("Slots in card '%s' are not a valid list.", self.name )
            return False

        for slot_yaml in slots_yaml:
            slot = NSPanelCardSlot.factory( slot_yaml, len(self.slots.keys()), self)
            if slot is not None:
                self.slots[slot.name] = slot

        if len(self.slots.keys()) <= 0:
            self.log.error("No valid slots defined for card %s", self.name )
            return False
        return True

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        super().load_card_yaml(card_yaml)

        if "slots" in card_yaml and card_yaml["slots"] is not None:
            return self.load_slots_yaml(card_yaml["slots"])

        self.log.error("No 'slots' attribute defined in card %s", self.name )
        return False

    def disconnect(self, nspanel):
        """
        disconnect from openhab
        """
        self.log.debug("Disconnect nspanel '%s' to card '%s'", nspanel.name, self.name )
        if nspanel.name in self.connected_panels:
            del self.connected_panels[nspanel.name]
        if nspanel.name in NSPanelCard.all_connected_panels:
            del NSPanelCard.all_connected_panels[nspanel.name]
        if len(NSPanelCard.all_connected_panels) == 0:
            #no panel connected anymore. Stop listner
            oh().disconnect()

    def connect(self, nspanel):
        """
        connect to openhab
        """
        self.log.debug("Connect nspanel '%s' to card '%s'", nspanel.name, self.name )
        if len(NSPanelCard.all_connected_panels) == 0:
            #start listening on openhab items
            oh().connect()
        self.connected_panels[nspanel.name] = nspanel
        NSPanelCard.all_connected_panels[nspanel.name] = nspanel

    def create_slots_payload(self):
        """
        create upstate payload for all slots
        """
        payload = ""
        for slot in self.slots.values():
            payload = payload + slot.create_payload()

        self.log.debug("Slot payload for all slots created: %s", payload)
        return payload

    def create_update_payload(self, compatibility=NSPanelCard.COMPATIBILITY_MODE_DEFAULT):
        """
        Create nav card payload
        """
        return super().create_update_payload(compatibility) + self.create_slots_payload()

    def popup_card(self, card_type, slot_name):
        """
        setup a popup card for this card type
        """
        self.log.debug("Create card '%s' for '%s'",card_type, slot_name)
        if slot_name in self.slots:
            self.popup = NSPanelCard.factory(card_type, self.slots[slot_name])
        else:
            if slot_name == 'CardThermo':
                #thermo popup
                self.popup = NSPanelCard.factory(card_type, self)
            else:
                self.log.warning("Popup for unknown slot '%s' received.", slot_name)
                return

        if self.popup is None:
            self.log.error("Popup card type could not be created '%s',", card_type)

    def item_update_callback(self, item):
        """
        this callback is called from OHItensDB if the state of an item in this card is updated
        """
        self.log.debug("Call from item listner of card '%s'. Item '%s' state in card has changed", self.name, item.name)
        for panel in self.connected_panels.values():
            panel.update()

    def event_button_press( self, params, panel=None ): #pylint: disable=too-many-return-statements, disable=too-many-branches
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
        slot_name = params[0]

        #check for item events
        if slot_name in self.slots:
            slot = self.slots[slot_name]
            if self.popup is not None:
                if self.popup.event_button_press( slot_name, params[1:] ):
                    return self
                return None
            self.log.debug("Process for item '%s' the button press event: %s", slot_name, str(params))

            if params[1] == "button":
                #button for this item was pressed => toggel the value
                if slot.slot_class == "ohItem":
                    if slot.popup_on_buttonpress is None:
                        if slot.type == NSPanelCardSlot.SLOT_BUTTON and slot.radio_button_state is not None:
                            #special handling for Radio Button function
                            slot.item.set_item_state(slot.radio_button_state)
                            return self
                        if slot.item.toggle_item_state(slot.options):
                            self.log.info("Toggle event '%s' for slot '%s'", params[1], slot.name)
                            return self
                    else:
                        #open a popup directly on button press
                        if slot.popup_on_buttonpress in NSPanelCard.compatible_cards[panel.compatibility_mode][NSPanelCard.POPUP_CARDS]:
                            self.popup = NSPanelCard.factory(slot.popup_on_buttonpress, slot)
                            panel.send_panel_cmd(self.popup.create_popup_cmd_payload(panel.compatibility_mode))
                            panel.send_panel_cmd(self.popup.create_update_payload(panel.compatibility_mode))
                        else:
                            self.log.warning("Popup not compatible or does not exist: '%s'", slot.popup_on_buttonpress)
                            self.popup = None
                        return None
                if slot.slot_class == "navigate":
                    self.log.debug("Navigate event '%s' for slot '%s'", params[1], slot.name)
                    card=NSPanelCard.card_by_path(slot.nav_to, panel)
                    if card is not None:
                        self.log.info("Navigate to '%s' over slot '%s'", slot.nav_to, slot.name)
                    else:
                        self.log.warning("Could not navigate to '%s' over slot '%s'", slot.nav_to, slot.name)
                    return card
            if params[1] == 'OnOff' and len(params) >= 3:
                if slot.item.set_item_state(map_state_pannel2oh(params[1], params[2])):
                    self.log.info("Switch event '%s' for slot '%s'", params[2], slot.name)
                    return self
            if params[1] == 'number-set' and len(params) >= 3:
                if slot.item.set_item_state( params[2]):
                    self.log.info("Number set event '%s' for slot '%s'", params[2], slot.name)
                    return self
            #check for cardPlayer events
            if params[1] in ['volumeSlider', 'media-shuffle', 'media-back', 'media-next', 'media-OnOff', 'media-pause']:
                if slot.slot_class == "ohItem" and slot.type == "player":
                    if slot.player_event(params[1:]):
                        self.log.debug("Player event '%s' for slot '%s processed'", params, slot.name)
                        return self

        self.log.warning("Event not processed for '%s' with params '%s'.", slot_name, params)
        return super().event_button_press( params, panel )

